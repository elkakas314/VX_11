"""
Tests for Switch Integration Module
Async client tests for Switch communication
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from operator_backend.backend.switch_integration import SwitchClient, get_switch_client


@pytest.fixture
async def switch_client():
    """Get Switch client."""
    return await get_switch_client("http://switch:8002")


class TestSwitchClient:
    """Switch client tests."""
    
    @pytest.mark.asyncio
    async def test_query_chat_success(self):
        """Test successful chat query."""
        client = SwitchClient("http://switch:8002")
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "response": "Hello from Switch",
                "engine": "deepseek_r1",
            }
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await client.query_chat(
                messages=[{"role": "user", "content": "Hello"}],
                task_type="chat",
            )
            
            assert result["response"] == "Hello from Switch"
            assert result["engine"] == "deepseek_r1"
    
    @pytest.mark.asyncio
    async def test_query_task_success(self):
        """Test successful task query."""
        client = SwitchClient("http://switch:8002")
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": "Task completed",
                "duration_ms": 250,
            }
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await client.query_task(
                task_type="summarization",
                payload={"text": "Lorem ipsum dolor sit amet..."},
            )
            
            assert result["result"] == "Task completed"
            assert result["duration_ms"] == 250
    
    @pytest.mark.asyncio
    async def test_query_chat_http_error(self):
        """Test chat query with HTTP error."""
        client = SwitchClient("http://switch:8002")
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
            mock_client_class.return_value = mock_client
            
            result = await client.query_chat(
                messages=[{"role": "user", "content": "Hello"}],
            )
            
            assert "error" in result
            assert result["response"] is None
    
    @pytest.mark.asyncio
    async def test_submit_feedback(self):
        """Test submitting feedback."""
        client = SwitchClient("http://switch:8002")
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "status": "ok",
                "feedback_recorded": True,
            }
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await client.submit_feedback(
                engine="deepseek_r1",
                success=True,
                latency_ms=150,
                tokens=500,
            )
            
            assert result["status"] == "ok"
            assert result["feedback_recorded"] is True
    
    @pytest.mark.asyncio
    async def test_get_queue_status(self):
        """Test getting queue status."""
        client = SwitchClient("http://switch:8002")
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "queue_size": 5,
                "processing": 1,
                "waiting": 4,
            }
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await client.get_queue_status()
            
            assert result["queue_size"] == 5
            assert result["processing"] == 1


class TestSwitchClientInit:
    """Switch client initialization tests."""
    
    def test_client_default_url(self):
        """Test client with default URL."""
        client = SwitchClient()
        assert "switch" in client.switch_url or "8002" in client.switch_url
    
    def test_client_custom_url(self):
        """Test client with custom URL."""
        client = SwitchClient("http://custom-switch:8002")
        assert client.switch_url == "http://custom-switch:8002"
    
    def test_client_custom_timeout(self):
        """Test client with custom timeout."""
        client = SwitchClient(timeout=60.0)
        assert client.timeout == 60.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
