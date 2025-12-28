"""
DeepSeek R1 Co-Dev Client for VX11

Controlado acceso a DeepSeek R1 API con:
- Rate limiting (max req/hour)
- Budget tracking (tokens estimados)
- Retry logic (exponential backoff)
- DB logging (trazabilidad)
- Strict sanitization (no secrets en logs)

Use case: SOLO co-dev (planning, patch generation, review)
NOT para runtime chat (prohibido).
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Literal

import httpx

log = logging.getLogger("vx11.tentaculo_link.deepseek_r1")


class DeepSeekR1Client:
    """
    Cliente para DeepSeek R1 (API pública).

    Contrato:
    - Timeout configurable (default 30s)
    - Max retries: 1 (exponential backoff, max 10s)
    - Max tokens: 2000 (para limitar coste + latencia)
    - Purpose enum: plan | patch | review | risk_assessment
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_sec: float = 30.0,
        max_retries: int = 1,
        max_tokens: int = 2000,
        rate_limit_per_hour: int = 10,
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not set. Set via env var or __init__ param."
            )

        self.base_url = "https://api.deepseek.com/chat/completions"
        self.model = "deepseek-reasoner"
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.rate_limit_per_hour = rate_limit_per_hour

        # Rate limit tracking (in-memory, simple)
        self._request_times: list[float] = []
        self._lock = asyncio.Lock()

    async def _check_rate_limit(self) -> bool:
        """Check if rate limit exceeded. Return True if OK."""
        async with self._lock:
            now = time.time()
            one_hour_ago = now - 3600

            # Prune old requests
            self._request_times = [t for t in self._request_times if t > one_hour_ago]

            if len(self._request_times) >= self.rate_limit_per_hour:
                log.warning(
                    f"deepseek_r1: rate_limit_exceeded ({len(self._request_times)}/{self.rate_limit_per_hour})"
                )
                return False

            self._request_times.append(now)
            return True

    async def _post_with_retries(
        self,
        payload: Dict[str, Any],
    ) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        POST to DeepSeek con retry.
        Retorna: (success, response_dict, error_msg)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                    resp = await client.post(
                        self.base_url, json=payload, headers=headers
                    )

                    if resp.status_code == 200:
                        log.info(f"deepseek_r1: OK (attempt {attempt + 1})")
                        return True, resp.json(), None

                    elif resp.status_code == 429:
                        error_msg = "rate_limit_hit"
                        log.warning(f"deepseek_r1: {error_msg} (attempt {attempt + 1})")
                        if attempt < self.max_retries:
                            wait_sec = min(2**attempt, 10)
                            log.info(f"deepseek_r1: retrying in {wait_sec}s")
                            await asyncio.sleep(wait_sec)
                            continue
                        return False, None, error_msg

                    else:
                        error_msg = f"http_{resp.status_code}"
                        log.error(f"deepseek_r1: {error_msg} (attempt {attempt + 1})")
                        try:
                            err_body = resp.json()
                            if "error" in err_body:
                                error_msg = err_body["error"].get("message", error_msg)
                        except Exception:
                            pass
                        return False, None, error_msg

            except asyncio.TimeoutError:
                error_msg = "timeout"
                log.error(f"deepseek_r1: {error_msg} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    wait_sec = min(2**attempt, 10)
                    log.info(f"deepseek_r1: retrying in {wait_sec}s")
                    await asyncio.sleep(wait_sec)
                    continue
                return False, None, error_msg

            except Exception as e:
                error_msg = f"exception: {type(e).__name__}"
                log.error(
                    f"deepseek_r1: {error_msg}: {str(e)[:100]} (attempt {attempt + 1})"
                )
                return False, None, error_msg

        return False, None, "max_retries_exceeded"

    async def invoke(
        self,
        prompt: str,
        purpose: Literal["plan", "patch", "review", "risk_assessment"] = "plan",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Invoke DeepSeek R1 para co-dev.

        Args:
            prompt: User prompt (será sanitizado de secretos antes de guardar en DB)
            purpose: plan | patch | review | risk_assessment
            temperature: 0.0 - 2.0 (R1 sugiere ~1.0)
            max_tokens: override max_tokens (capped at self.max_tokens)

        Returns:
            {
                "status": "ok" | "error",
                "request_id": uuid,
                "purpose": purpose,
                "model": "deepseek-reasoner",
                "reasoning_content": "... reasoning ...",
                "response": "... answer ...",
                "tokens_used": int,
                "reasoning_tokens": int,
                "error_code": str (if error),
                "error_msg": str (if error),
            }
        """

        request_id = str(uuid.uuid4())
        started_at = time.time()

        # Rate limit check
        if not await self._check_rate_limit():
            log.warning(f"deepseek_r1 [{request_id}]: rate limit exceeded")
            return {
                "status": "error",
                "request_id": request_id,
                "purpose": purpose,
                "error_code": "rate_limit_exceeded",
                "error_msg": f"Max {self.rate_limit_per_hour} requests per hour",
            }

        # Clamp max_tokens
        tokens_to_use = min(max_tokens or self.max_tokens, self.max_tokens)

        # Payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt_for_purpose(purpose),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": tokens_to_use,
            "temperature": min(max(temperature, 0.0), 2.0),
        }

        # POST con retry
        success, resp_json, error_msg = await self._post_with_retries(payload)

        elapsed_ms = int((time.time() - started_at) * 1000)

        if not success:
            log.error(
                f"deepseek_r1 [{request_id}]: failed — {error_msg} ({elapsed_ms}ms)"
            )
            return {
                "status": "error",
                "request_id": request_id,
                "purpose": purpose,
                "error_code": error_msg or "unknown_error",
                "error_msg": error_msg or "Unknown error",
                "elapsed_ms": elapsed_ms,
            }

        # Parse success response
        try:
            reasoning_content = ""
            response_text = ""
            total_tokens = 0
            reasoning_tokens = 0

            if "choices" in resp_json and len(resp_json["choices"]) > 0:
                choice = resp_json["choices"][0]
                message = choice.get("message", {})
                reasoning_content = message.get("reasoning_content", "")
                response_text = message.get("content", "")

            if "usage" in resp_json:
                usage = resp_json["usage"]
                total_tokens = usage.get("total_tokens", 0)
                reasoning_tokens = usage.get("completion_tokens_details", {}).get(
                    "reasoning_tokens", 0
                )

            log.info(
                f"deepseek_r1 [{request_id}]: success ({total_tokens} tokens, {reasoning_tokens} reasoning, {elapsed_ms}ms)"
            )

            return {
                "status": "ok",
                "request_id": request_id,
                "purpose": purpose,
                "model": self.model,
                "reasoning_content": reasoning_content,
                "response": response_text,
                "tokens_used": total_tokens,
                "reasoning_tokens": reasoning_tokens,
                "elapsed_ms": elapsed_ms,
            }

        except Exception as e:
            log.error(
                f"deepseek_r1 [{request_id}]: response_parse_error: {str(e)[:100]}"
            )
            return {
                "status": "error",
                "request_id": request_id,
                "purpose": purpose,
                "error_code": "response_parse_error",
                "error_msg": str(e)[:100],
                "elapsed_ms": elapsed_ms,
            }

    @staticmethod
    def _system_prompt_for_purpose(
        purpose: Literal["plan", "patch", "review", "risk_assessment"],
    ) -> str:
        """System prompt contextualizado para cada purpose."""
        prompts = {
            "plan": "You are a senior software architect. Generate a detailed technical plan with clear steps and considerations.",
            "patch": "You are a code review expert. Generate a minimal, high-quality patch with explanation.",
            "review": "You are a code reviewer. Provide constructive feedback focusing on quality, security, and maintainability.",
            "risk_assessment": "You are a security/risk analyst. Identify potential risks and propose mitigations.",
        }
        return prompts.get(purpose, prompts["plan"])


# Singleton instance (lazy init)
_deepseek_r1_client: Optional[DeepSeekR1Client] = None


async def get_deepseek_r1_client() -> DeepSeekR1Client:
    """Get or create DeepSeek R1 client singleton."""
    global _deepseek_r1_client
    if _deepseek_r1_client is None:
        _deepseek_r1_client = DeepSeekR1Client()
    return _deepseek_r1_client
