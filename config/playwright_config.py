"""
Playwright Configuration & Remote Client
Supports both local (direct) and remote (WebSocket sidecar) modes.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import uuid
import json

from config.settings import settings
from config.forensics import write_log


class PlaywrightConfig:
    """Centralized Playwright configuration."""
    
    # Enable/disable Playwright globally
    ENABLED = os.getenv("VX11_ENABLE_PLAYWRIGHT", "1").lower() in ("1", "true", "yes")
    
    # WebSocket URL for remote Playwright server (if using sidecar)
    WS_URL = os.getenv("PLAYWRIGHT_WS_URL", "ws://playwright:3000")
    
    # Implementation: "playwright" (direct or remote), "stub" (for testing)
    IMPL = os.getenv("BROWSER_IMPL", "playwright")
    
    # Timeouts
    NAVIGATE_TIMEOUT_MS = int(os.getenv("PLAYWRIGHT_NAVIGATE_TIMEOUT", "30000"))
    SCREENSHOT_TIMEOUT_MS = int(os.getenv("PLAYWRIGHT_SCREENSHOT_TIMEOUT", "10000"))
    
    # Headless mode
    HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() in ("1", "true", "yes")
    
    # Screenshots directory
    SCREENSHOTS_DIR = Path(os.getenv("PLAYWRIGHT_SCREENSHOTS_DIR", "/app/data/screenshots"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        if not cls.ENABLED:
            write_log("playwright_config", "playwright:disabled")
            return False
        
        if cls.IMPL == "stub":
            write_log("playwright_config", "playwright:stub_mode")
            return True
        
        if cls.IMPL == "playwright":
            # Check if WebSocket URL is reachable (for remote)
            write_log("playwright_config", f"playwright:configured:ws_url={cls.WS_URL}")
            return True
        
        write_log("playwright_config", f"playwright:unknown_impl:{cls.IMPL}", level="WARNING")
        return False
    
    @classmethod
    def ensure_dirs(cls):
        """Ensure required directories exist."""
        try:
            cls.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            write_log("playwright_config", f"playwright:screenshots_dir_ready:{cls.SCREENSHOTS_DIR}")
        except OSError as e:
            write_log("playwright_config", f"playwright:mkdir_error:{e}", level="ERROR")


class PlaywrightRemoteClient:
    """
    Remote Playwright client for WebSocket-based sidecar connection.
    
    Alternatives to full Playwright local install:
    1. Use pyppeteer (deprecated, chromium-only)
    2. Use playwright's remote browser server (preferred)
    3. Use CDPSession + WebSocket directly (low-level)
    
    This implementation uses CDP (Chrome DevTools Protocol) over WebSocket.
    """
    
    def __init__(self, ws_url: str = None, timeout_ms: int = 30000):
        """Initialize remote client."""
        self.ws_url = ws_url or PlaywrightConfig.WS_URL
        self.timeout_ms = timeout_ms
        self.session_id: Optional[str] = None
        self.page_id: Optional[str] = None
        write_log("playwright_config", f"playwright_remote_client:init:{self.ws_url}")
    
    async def connect(self) -> bool:
        """Connect to remote Playwright server."""
        try:
            # Import websockets only if needed (optional dependency)
            import websockets
            import json
            
            async with websockets.connect(self.ws_url) as ws:
                # Handshake: request browser connection
                msg = {
                    "type": "launch",
                    "params": {
                        "headless": True,
                        "browser": "chromium"
                    }
                }
                await ws.send(json.dumps(msg))
                
                # Wait for response
                resp_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                resp = json.loads(resp_raw)
                
                if resp.get("type") == "ready":
                    self.session_id = resp.get("session_id")
                    write_log("playwright_config", f"playwright_remote:connected:{self.session_id}")
                    return True
                else:
                    write_log("playwright_config", f"playwright_remote:handshake_failed:{resp}", level="ERROR")
                    return False
        
        except ImportError:
            write_log("playwright_config", "playwright_remote:websockets_not_installed", level="WARNING")
            return False
        except Exception as e:
            write_log("playwright_config", f"playwright_remote:connect_error:{e}", level="ERROR")
            return False
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL (remote implementation)."""
        result = {
            "status": "pending",
            "url": url,
            "title": "",
            "text_snippet": "",
            "screenshot_path": None,
            "error": None,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 0,
        }
        
        try:
            import websockets
            import json
            import time
            
            start = time.time()
            
            async with websockets.connect(self.ws_url) as ws:
                # Request navigation
                msg = {
                    "type": "goto",
                    "session_id": self.session_id,
                    "url": url,
                    "timeout_ms": self.timeout_ms
                }
                await ws.send(json.dumps(msg))
                
                # Wait for completion
                resp_raw = await asyncio.wait_for(ws.recv(), timeout=self.timeout_ms / 1000 + 5)
                resp = json.loads(resp_raw)
                
                if resp.get("type") == "goto_done":
                    result["status"] = "ok"
                    result["title"] = resp.get("title", "")
                    result["text_snippet"] = resp.get("text_snippet", "")[:500]
                    
                    # Request screenshot
                    ss_msg = {
                        "type": "screenshot",
                        "session_id": self.session_id,
                        "full_page": False
                    }
                    await ws.send(json.dumps(ss_msg))
                    
                    ss_resp_raw = await asyncio.wait_for(ws.recv(), timeout=10)
                    ss_resp = json.loads(ss_resp_raw)
                    
                    if ss_resp.get("type") == "screenshot_data":
                        # Save screenshot
                        import base64
                        screenshot_data = base64.b64decode(ss_resp.get("data", ""))
                        filename = f"screenshot_{uuid.uuid4()}.png"
                        screenshot_path = PlaywrightConfig.SCREENSHOTS_DIR / filename
                        screenshot_path.write_bytes(screenshot_data)
                        result["screenshot_path"] = str(screenshot_path)
                        write_log("playwright_config", f"playwright_remote:screenshot_ok:{url}")
                else:
                    result["status"] = "error"
                    result["error"] = resp.get("error", "unknown_error")
            
            result["duration_ms"] = int((time.time() - start) * 1000)
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            write_log("playwright_config", f"playwright_remote:navigate_error:{e}", level="ERROR")
        
        return result


class PlaywrightClientFactory:
    """Factory to create appropriate Playwright client."""
    
    @staticmethod
    def create(impl: str = None):
        """Create client based on configuration."""
        impl = impl or PlaywrightConfig.IMPL
        
        if impl == "stub":
            write_log("playwright_config", "playwright:using_stub_client")
            return PlaywrightStubClient()
        elif impl == "playwright":
            # Try remote first, fall back to local if not available
            write_log("playwright_config", "playwright:using_remote_client")
            return PlaywrightRemoteClient()
        else:
            write_log("playwright_config", f"playwright:unknown_impl:{impl}", level="ERROR")
            return PlaywrightStubClient()  # Fallback to stub


class PlaywrightStubClient:
    """Stub client for testing (no real browser)."""
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Stub navigate (returns mock data)."""
        write_log("playwright_config", f"playwright_stub:navigate:{url}")
        return {
            "status": "ok",
            "url": url,
            "title": f"Mock Page - {url}",
            "text_snippet": "This is stub page content. Real Playwright not available.",
            "screenshot_path": None,
            "error": None,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_ms": 100,
        }


# Module-level convenience function
def get_playwright_client():
    """Get configured Playwright client."""
    return PlaywrightClientFactory.create()

