"""Telegram adapter (OFF by default).

This is a safe stub. It does not import `python-telegram-bot` or any heavy
dependencies. Activation must be explicit via env `VX11_ENABLE_TELEGRAM_ADAPTER=1`.

If enabled in future, this adapter must NOT contain hardcoded tokens and
must only enqueue intents via the gateway endpoint `/v1/command`.
"""

import os
from typing import Dict, Any

ENABLED = os.getenv("VX11_ENABLE_TELEGRAM_ADAPTER", "0") == "1"


def handle_update(update: Dict[str, Any]) -> Dict[str, Any]:
    """Convert incoming telegram update into an intent payload.

    This stub returns a normalized object; it does not call Telegram API.
    """
    message = update.get("message", {}).get("text", "")
    intent = {
        "intent_type": "chat",
        "source": "telegram",
        "payload": {"message": message},
    }
    return intent
