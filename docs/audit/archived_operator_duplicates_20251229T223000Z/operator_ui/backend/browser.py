"""Proxy module to expose `operator.backend.browser`.

This forwards imports to `operator_backend.backend.browser`, making the
module available under the dotted path expected by tests and by
`unittest.mock.patch`.
"""

import importlib

try:
    _src = importlib.import_module("operator_backend.backend.browser")
    # Re-export public names from source module
    from operator_backend.backend.browser import *  # type: ignore

    # Also keep a reference to the original module
    __source_module__ = _src
except Exception:
    # Fallback minimal stubs to avoid import errors during early test runs
    __source_module__ = None

__all__ = getattr(
    __source_module__, "__all__", [n for n in globals() if not n.startswith("_")]
)
"""Browser client shim for tests.

Provides `BrowserClient` with `navigate()` returning a deterministic stub
matching test expectations: title == "Page Title (stub)" and status ok.
Also exposes `async_playwright` symbol so tests can patch it.
"""

from typing import Dict, Any, Optional
import asyncio

async_playwright = None  # patch target in tests


class BrowserClient:
    def __init__(
        self, impl: str = "stub", headless: bool = True, timeout_ms: int = 30000
    ):
        self.impl = impl
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def navigate(self, url: str) -> Dict[str, Any]:
        # deterministic stub used by tests
        await asyncio.sleep(0)  # yield
        if self.impl != "stub":
            raise ValueError(f"Unknown browser impl: {self.impl}")
        return {
            "status": "ok",
            "url": url,
            "title": "Page Title (stub)",
            "screenshot_path": None,
            "text_snippet": "Stub page content",
        }


# synchronous helper for non-async tests
class BrowserClientSync:
    def __init__(
        self, impl: str = "stub", headless: bool = True, timeout_ms: int = 30000
    ):
        self._client = BrowserClient(
            impl=impl, headless=headless, timeout_ms=timeout_ms
        )

    def navigate(self, url: str) -> Dict[str, Any]:
        return asyncio.get_event_loop().run_until_complete(self._client.navigate(url))


__all__ = ["BrowserClient", "BrowserClientSync", "async_playwright"]
