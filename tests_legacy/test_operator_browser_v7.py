"""
Tests for Operator Browser v7 (Playwright)
Stub-based tests (no real browser execution during tests)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from operator_backend.backend.browser import BrowserClient, BrowserResult, SCREENSHOTS_DIR


class TestBrowserResult:
    """BrowserResult model tests."""
    
    def test_browser_result_init(self):
        """Test BrowserResult initialization."""
        result = BrowserResult()
        assert result.status == "pending"
        assert result.url == ""
        assert result.title == ""
        assert result.error is None
    
    def test_browser_result_to_dict(self):
        """Test to_dict() conversion."""
        result = BrowserResult()
        result.status = "ok"
        result.url = "https://example.com"
        result.title = "Example"
        result.text_snippet = "Sample text"
        
        d = result.to_dict()
        assert d["status"] == "ok"
        assert d["url"] == "https://example.com"
        assert d["title"] == "Example"
        assert "timestamp" in d


class TestBrowserClientInit:
    """Browser client initialization tests."""
    
    def test_client_stub_mode(self):
        """Test client in stub mode."""
        client = BrowserClient(impl="stub")
        assert client.impl == "stub"
        assert client.headless is True
    
    def test_client_playwright_mode(self):
        """Test client in playwright mode."""
        client = BrowserClient(impl="playwright")
        assert client.impl == "playwright"
    
    def test_client_custom_timeout(self):
        """Test client with custom timeout."""
        client = BrowserClient(timeout_ms=60000)
        assert client.timeout_ms == 60000


class TestBrowserClientStub:
    """Stub implementation tests (no real browser)."""
    
    @pytest.mark.asyncio
    async def test_stub_navigate(self):
        """Test stub navigate."""
        client = BrowserClient(impl="stub")
        result = await client.navigate("https://example.com")
        
        assert result["status"] == "ok"
        assert result["url"] == "https://example.com"
        assert result["title"] == "Page Title (stub)"
        assert result["screenshot_path"] is None
    
    @pytest.mark.asyncio
    async def test_stub_extract_text(self):
        """Test stub text extraction."""
        client = BrowserClient(impl="stub")
        text = await client.extract_text("https://example.com")
        assert text == "Stub page text"
    
    @pytest.mark.asyncio
    async def test_stub_execute_js(self):
        """Test stub JS execution."""
        client = BrowserClient(impl="stub")
        result = await client.execute_js("https://example.com", "return 42")
        
        assert result["status"] == "ok"
        assert result["result"] is None
    
    @pytest.mark.asyncio
    async def test_stub_close(self):
        """Test stub close."""
        client = BrowserClient(impl="stub")
        await client.close()  # Should not raise


class TestBrowserClientPlaywright:
    """Playwright implementation tests (mocked)."""
    
    @pytest.mark.asyncio
    async def test_playwright_navigate_success(self):
        """Test Playwright navigate with mock."""
        client = BrowserClient(impl="playwright")
        
        with patch("operator.backend.browser.async_playwright") as mock_pw:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            
            mock_page.title = AsyncMock(return_value="Example Title")
            mock_page.text_content = AsyncMock(return_value="Example content")
            mock_page.screenshot = AsyncMock()
            
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()
            
            mock_chromium = AsyncMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.__aenter__.return_value.chromium = mock_chromium
            mock_pw.return_value = mock_pw_instance
            
            result = await client.navigate("https://example.com")
            
            assert result["status"] == "ok"
            assert result["url"] == "https://example.com"
            assert result["title"] == "Example Title"
    
    @pytest.mark.asyncio
    async def test_playwright_navigate_timeout(self):
        """Test Playwright navigate with timeout."""
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        
        client = BrowserClient(impl="playwright")
        
        with patch("operator.backend.browser.async_playwright") as mock_pw:
            mock_page = AsyncMock()
            mock_page.goto = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))
            
            mock_browser = AsyncMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()
            
            mock_chromium = AsyncMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.__aenter__.return_value.chromium = mock_chromium
            mock_pw.return_value = mock_pw_instance
            
            result = await client.navigate("https://example.com")
            
            assert result["status"] == "timeout"
            assert result["error"] is not None
    
    @pytest.mark.asyncio
    async def test_playwright_execute_js(self):
        """Test Playwright JS execution."""
        client = BrowserClient(impl="playwright")
        
        with patch("operator.backend.browser.async_playwright") as mock_pw:
            mock_page = AsyncMock()
            mock_page.evaluate = AsyncMock(return_value=42)
            
            mock_browser = AsyncMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()
            
            mock_chromium = AsyncMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.__aenter__.return_value.chromium = mock_chromium
            mock_pw.return_value = mock_pw_instance
            
            result = await client.execute_js("https://example.com", "return 42")
            
            assert result["status"] == "ok"
            assert result["result"] == 42


class TestBrowserClientIntegration:
    """Integration flow tests."""
    
    @pytest.mark.asyncio
    async def test_full_navigate_flow_stub(self):
        """Test complete navigate flow with stub."""
        client = BrowserClient(impl="stub")
        
        # Navigate
        nav_result = await client.navigate("https://example.com")
        assert nav_result["status"] == "ok"
        
        # Extract text
        text = await client.extract_text("https://example.com")
        assert len(text) > 0
        
        # Execute JS
        js_result = await client.execute_js("https://example.com", "return true")
        assert js_result["status"] == "ok"
        
        # Close
        await client.close()


class TestBrowserClientError:
    """Error handling tests."""
    
    @pytest.mark.asyncio
    async def test_unknown_impl(self):
        """Test unknown implementation."""
        client = BrowserClient(impl="unknown")
        result = await client.navigate("https://example.com")
        
        assert result["status"] == "error"
        assert "unknown_impl" in result["error"]
    
    @pytest.mark.asyncio
    async def test_playwright_error_handling(self):
        """Test Playwright error handling."""
        client = BrowserClient(impl="playwright")
        
        with patch("operator.backend.browser.async_playwright") as mock_pw:
            mock_page = AsyncMock()
            mock_page.goto = AsyncMock(side_effect=Exception("Network error"))
            
            mock_browser = AsyncMock()
            mock_browser.new_page = AsyncMock(return_value=mock_page)
            mock_browser.close = AsyncMock()
            
            mock_chromium = AsyncMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)
            
            mock_pw_instance = AsyncMock()
            mock_pw_instance.__aenter__.return_value.chromium = mock_chromium
            mock_pw.return_value = mock_pw_instance
            
            result = await client.navigate("https://example.com")
            
            assert result["status"] == "error"
            assert result["error"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
