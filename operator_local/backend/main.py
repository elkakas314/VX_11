"""Minimal shim module `operator.backend.main` used by tests for monkeypatching.

Provides a `switch_client` object with an async `chat` method that tests can
monkeypatch. This avoids ImportError: No module named 'operator.backend'.
"""

import asyncio


class _SwitchClientShim:
    async def chat(self, message, metadata, source="operator"):
        # default shim behavior: echo minimal structure
        return {"status": "ok", "proxy": True, "message": message}


switch_client = _SwitchClientShim()
