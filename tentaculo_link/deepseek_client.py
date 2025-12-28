"""
DeepSeek API Client for Tentáculo Link fallback chat.

When switch is unavailable (solo_madre policy), this client provides
fallback LLM responses using DeepSeek API (external).

Version: 1.0 | Module: tentaculo_link | Port: (external)
"""

import asyncio
import json
import sqlite3
from typing import Any, Dict, Optional
from datetime import datetime

import httpx

from config.settings import settings
from config.forensics import write_log


class DeepSeekClient:
    """Async HTTP client for DeepSeek API (external fallback)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = base_url or settings.deepseek_base_url
        self.client: Optional[httpx.AsyncClient] = None
        self.model = "deepseek-chat"  # Default model
        self.timeout = 30.0

        if not self.api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not set. Cannot initialize DeepSeekClient."
            )

    async def startup(self):
        """Initialize HTTP client with auth headers."""
        if not self.client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self.client = httpx.AsyncClient(headers=headers, timeout=self.timeout)

    async def shutdown(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def chat(
        self, message: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call DeepSeek /chat/completions API.

        Args:
            message: User message
            system_prompt: Optional system prompt (default: assistant role)

        Returns:
            Dict with keys: 'text', 'model', 'status', 'error' (if any)
        """
        if not self.client:
            await self.startup()

        if system_prompt is None:
            system_prompt = (
                "Eres un asistente útil y amable. Responde de forma clara y concisa."
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        try:
            endpoint = f"{self.base_url}/chat/completions"
            resp = await self.client.post(endpoint, json=payload)

            if resp.status_code != 200:
                error_text = resp.text[:200]
                write_log(
                    "tentaculo_link",
                    f"deepseek_api_error:status={resp.status_code}:{error_text}",
                    level="WARNING",
                )
                return {
                    "text": None,
                    "model": self.model,
                    "status": "error",
                    "error": f"HTTP {resp.status_code}",
                }

            data = resp.json()
            # Extract message from DeepSeek response
            if "choices" in data and len(data["choices"]) > 0:
                text = data["choices"][0].get("message", {}).get("content", "")
                return {
                    "text": text,
                    "model": data.get("model", self.model),
                    "status": "ok",
                    "error": None,
                }
            else:
                write_log(
                    "tentaculo_link",
                    f"deepseek_api_malformed:no_choices_in:{data}",
                    level="WARNING",
                )
                return {
                    "text": None,
                    "model": self.model,
                    "status": "error",
                    "error": "Malformed response (no choices)",
                }

        except asyncio.TimeoutError:
            write_log(
                "tentaculo_link",
                f"deepseek_api_timeout:{self.timeout}s",
                level="WARNING",
            )
            return {
                "text": None,
                "model": self.model,
                "status": "error",
                "error": "Timeout",
            }
        except Exception as exc:
            write_log(
                "tentaculo_link",
                f"deepseek_api_exception:{type(exc).__name__}:{str(exc)[:100]}",
                level="WARNING",
            )
            return {
                "text": None,
                "model": self.model,
                "status": "error",
                "error": str(exc)[:100],
            }


async def save_chat_to_db(
    session_id: str, user_message: str, assistant_response: str
) -> bool:
    """
    Save chat message to operator_session + operator_message tables.

    Runs synchronously in thread pool to avoid blocking async code.

    Args:
        session_id: Session ID
        user_message: User's message text
        assistant_response: Assistant's response text

    Returns:
        True if saved; False if error
    """
    try:
        db_path = settings.database_path
        db_file = f"{db_path}/vx11.db"

        # Use sync sqlite3 in thread pool
        loop = asyncio.get_event_loop()

        def _save():
            conn = sqlite3.connect(db_file)
            try:
                c = conn.cursor()
                now = datetime.utcnow().isoformat()

                # Ensure session exists
                c.execute(
                    """
                    INSERT OR IGNORE INTO operator_session
                    (session_id, user_id, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, "deepseek-fallback", "tentaculo-deepseek", now, now),
                )

                # Insert user message
                c.execute(
                    """
                    INSERT INTO operator_message
                    (session_id, role, content, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, "user", user_message, now),
                )

                # Insert assistant response
                c.execute(
                    """
                    INSERT INTO operator_message
                    (session_id, role, content, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, "assistant", assistant_response, now),
                )

                conn.commit()
                return True
            except Exception as e:
                write_log(
                    "tentaculo_link",
                    f"save_chat_to_db_error:{str(e)[:100]}",
                    level="WARNING",
                )
                return False
            finally:
                conn.close()

        result = await loop.run_in_executor(None, _save)
        return result
    except Exception as e:
        write_log(
            "tentaculo_link",
            f"save_chat_to_db_exception:{type(e).__name__}:{str(e)[:100]}",
            level="WARNING",
        )
        return False
