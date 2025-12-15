"""
Browser Module v7.0 – Playwright Integration
Supports both local (direct) and remote (sidecar WebSocket) implementations.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Conditional Playwright import (optional dependency)
try:
    from playwright.async_api import (
        async_playwright,
        TimeoutError as PlaywrightTimeoutError,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

    # Create dummy objects for testing
    class TimeoutError(Exception):
        pass

    PlaywrightTimeoutError = TimeoutError

from config.forensics import write_log
from config.settings import settings
from config.playwright_config import PlaywrightConfig, PlaywrightClientFactory


# Lazy initialization - don't create dir on import
SCREENSHOTS_DIR = Path("/app/data/screenshots")


def _ensure_screenshots_dir():
    """Ensure screenshots directory exists."""
    try:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError):
        # Fallback to local directory if /app not available
        local_dir = Path("./data/screenshots")
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir
    return SCREENSHOTS_DIR


class BrowserResult:
    """Result from browser operations."""

    def __init__(self):
        self.status: str = "pending"
        self.url: str = ""
        self.title: str = ""
        self.text_snippet: str = ""
        self.screenshot_path: Optional[str] = None
        self.error: Optional[str] = None
        self.timestamp: str = datetime.utcnow().isoformat()
        self.duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "status": self.status,
            "url": self.url,
            "title": self.title,
            "text_snippet": self.text_snippet,
            "screenshot_path": self.screenshot_path,
            "error": self.error,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
        }


class BrowserClient:
    """Browser automation with Playwright (local or remote sidecar)."""

    def __init__(
        self, impl: str = None, headless: bool = True, timeout_ms: int = 30000
    ):
        """Initialize browser client."""
        self.impl = impl or os.getenv("BROWSER_IMPL", PlaywrightConfig.IMPL)
        self.headless = headless
        self.timeout_ms = timeout_ms or PlaywrightConfig.NAVIGATE_TIMEOUT_MS
        self.browser = None

        # Initialize Playwright configuration
        PlaywrightConfig.validate()
        PlaywrightConfig.ensure_dirs()

        # Create appropriateclient (local or remote)
        self.client = PlaywrightClientFactory.create(impl=self.impl)

        write_log(
            "operator_backend",
            f"browser_client:init:{self.impl}:headless={self.headless}:timeout={self.timeout_ms}ms",
        )

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL and capture screenshot + text (delegation to client)."""
        result = await self.client.navigate(url)
        write_log("operator_backend", f"browser:navigate:{result.get('status')}:{url}")
        return result

    def _stub_navigate(self, url: str) -> Dict[str, Any]:
        """Stub implementation (for testing without real browser)."""
        write_log("operator_backend", f"browser:stub_navigate:{url}")
        return {
            "status": "ok",
            "url": url,
            "title": "Page Title (stub)",
            "text_snippet": "Stub page content",
            "screenshot_path": None,
            "error": None,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 100,
        }

    async def _playwright_navigate_local(self, url: str) -> Dict[str, Any]:
        """Navigate with Playwright LOCAL instance (direct browser)."""
        import time

        result = BrowserResult()
        result.url = url
        start = time.time()

        # Check if Playwright is available
        if not PLAYWRIGHT_AVAILABLE:
            result.status = "unavailable"
            result.error = "playwright_not_installed"
            write_log(
                "operator_backend", f"browser:playwright_unavailable", level="WARNING"
            )
            return result.to_dict()

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()

                # Navigate
                await page.goto(url, wait_until="networkidle", timeout=self.timeout_ms)

                # Get title
                result.title = await page.title()

                # Extract text (first 500 chars)
                text = await page.text_content("body")
                result.text_snippet = (text or "")[:500]

                # Screenshot
                screenshot_filename = f"screenshot_{uuid.uuid4()}.png"
                screenshots_dir = PlaywrightConfig.SCREENSHOTS_DIR
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = screenshots_dir / screenshot_filename
                await page.screenshot(path=str(screenshot_path), full_page=False)
                result.screenshot_path = str(screenshot_path)

                result.status = "ok"
                await browser.close()
                write_log("operator_backend", f"browser:navigate:ok:{url}")

        except PlaywrightTimeoutError as exc:
            result.status = "timeout"
            result.error = f"navigation_timeout:{str(exc)}"
            write_log("operator_backend", f"browser:timeout:{url}", level="WARNING")

        except Exception as exc:
            result.status = "error"
            result.error = str(exc)
            write_log("operator_backend", f"browser:error:{exc}", level="ERROR")

        result.duration_ms = int((time.time() - start) * 1000)
        return result.to_dict()

    async def execute_js(self, url: str, script: str) -> Dict[str, Any]:
        """Execute JavaScript on page (delegated to client or local Playwright)."""
        if self.impl == "stub":
            write_log("operator_backend", "browser:stub_execute_js")
            return {"status": "ok", "result": None}

        # For now, use local Playwright if available
        try:
            if not PLAYWRIGHT_AVAILABLE:
                write_log(
                    "operator_backend",
                    "browser:execute_js:playwright_not_available",
                    level="WARNING",
                )
                return {"status": "unavailable", "error": "playwright_not_installed"}

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=self.timeout_ms)

                result = await page.evaluate(script)

                await browser.close()
                write_log("operator_backend", f"browser:execute_js:ok:{url}")
                return {"status": "ok", "result": result}

        except Exception as exc:
            write_log(
                "operator_backend", f"browser:execute_js_error:{exc}", level="ERROR"
            )
            return {"status": "error", "error": str(exc)}

    async def extract_text(self, url: str) -> str:
        """Extract all text from page (delegated or local)."""
        if self.impl == "stub":
            return "Stub page text"

        # For now, use local Playwright if available
        try:
            if not PLAYWRIGHT_AVAILABLE:
                write_log(
                    "operator_backend",
                    "browser:extract_text:playwright_not_available",
                    level="WARNING",
                )
                return ""

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=self.timeout_ms)

                text = await page.text_content("body")
                await browser.close()

                write_log("operator_backend", f"browser:extract_text:ok:{url}")
                return text or ""

        except Exception as exc:
            write_log(
                "operator_backend", f"browser:extract_text_error:{exc}", level="ERROR"
            )
            return ""

    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        write_log("operator_backend", f"browser:closed:{self.impl}")


def get_browser_impl() -> str:
    """Get configured browser implementation."""
    return os.getenv("BROWSER_IMPL", "playwright")
