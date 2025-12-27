"""
DeepSeek R1 client for madre LLM integration.

Minimal feature-flag implementation:
- Reads API key from env (DEEPSEEK_API_KEY, DEEPSEEK_KEY, VX11_DEEPSEEK_API_KEY)
- Uses httpx async client for consistent pattern
- Fallback on error (no token / timeout / API error)
- Response schema matches madre ChatResponse
"""

import os
import logging
from typing import Optional
import httpx

log = logging.getLogger("vx11.madre.llm.deepseek")


def get_deepseek_api_key() -> Optional[str]:
    """Read DeepSeek API key from env (priority order)."""
    return (
        os.environ.get("DEEPSEEK_API_KEY")
        or os.environ.get("DEEPSEEK_KEY")
        or os.environ.get("VX11_DEEPSEEK_API_KEY")
    )


async def call_deepseek_r1(
    message: str,
    timeout_seconds: int = 15,
) -> dict:
    """
    Call DeepSeek R1 model.

    Args:
        message: User message
        timeout_seconds: Request timeout (default 15s, prod-friendly)

    Returns:
        dict with keys:
        - response: str (model output or error message)
        - provider: "deepseek" | "error"
        - model: "deepseek-reasoner"
        - status: "DONE" | "DEGRADED"
    """
    api_key = get_deepseek_api_key()

    if not api_key:
        log.debug("DeepSeek API key not found, will use fallback provider")
        return {
            "response": "",
            "provider": "no_token",
            "model": None,
            "status": "DEGRADED",
        }

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-reasoner",
                    "messages": [
                        {
                            "role": "user",
                            "content": message,
                        }
                    ],
                    "temperature": 0.7,
                },
            )

        if response.status_code != 200:
            log.warning(
                f"DeepSeek API returned {response.status_code}: {response.text[:200]}"
            )
            return {
                "response": f"DeepSeek API error: {response.status_code}",
                "provider": "deepseek_error",
                "model": "deepseek-reasoner",
                "status": "ERROR",
            }

        data = response.json()
        model_response = (
            data.get("choices", [{}])[0].get("message", {}).get("content", "")
        )

        if not model_response:
            log.warning("DeepSeek returned empty response")
            return {
                "response": "DeepSeek returned empty response",
                "provider": "deepseek_error",
                "model": "deepseek-reasoner",
                "status": "ERROR",
            }

        log.info("DeepSeek R1 call successful")
        return {
            "response": model_response,
            "provider": "deepseek",
            "model": "deepseek-reasoner",
            "status": "DONE",
        }

    except httpx.TimeoutException:
        log.warning(f"DeepSeek timeout after {timeout_seconds}s")
        return {
            "response": f"DeepSeek timeout after {timeout_seconds}s",
            "provider": "deepseek_timeout",
            "model": "deepseek-reasoner",
            "status": "DEGRADED",
        }

    except Exception as e:
        log.error(f"DeepSeek call failed: {e}", exc_info=True)
        return {
            "response": f"DeepSeek error: {str(e)[:100]}",
            "provider": "deepseek_exception",
            "model": "deepseek-reasoner",
            "status": "ERROR",
        }


def is_deepseek_available() -> bool:
    """Check if DeepSeek API key is configured."""
    return bool(get_deepseek_api_key())
