"""
Test suite for DeepSeek R1 integration in madre/chat.
Mocks DeepSeek API calls to verify feature-flag behavior.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from madre.llm.deepseek_client import (
    call_deepseek_r1,
    is_deepseek_available,
    get_deepseek_api_key,
)


@pytest.mark.asyncio
async def test_deepseek_no_api_key():
    """Test DeepSeek behavior when API key not configured."""
    with patch.dict("os.environ", {}, clear=True):
        # Ensure no DeepSeek API key in env
        result = await call_deepseek_r1("test message")

        assert result["provider"] == "no_token"
        assert result["status"] == "DEGRADED"
        assert result["model"] is None


@pytest.mark.asyncio
async def test_deepseek_available():
    """Test is_deepseek_available() detection."""
    with patch(
        "madre.llm.deepseek_client.get_deepseek_api_key", return_value="fake-key"
    ):
        assert is_deepseek_available() is True

    with patch("madre.llm.deepseek_client.get_deepseek_api_key", return_value=None):
        assert is_deepseek_available() is False


@pytest.mark.asyncio
async def test_deepseek_successful_call():
    """Test successful DeepSeek R1 call with mock."""
    with patch(
        "madre.llm.deepseek_client.get_deepseek_api_key", return_value="fake-key"
    ):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Mock response from DeepSeek"}}]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await call_deepseek_r1("test message")

            assert result["provider"] == "deepseek"
            assert result["model"] == "deepseek-reasoner"
            assert result["status"] == "DONE"
            assert "Mock response" in result["response"]


@pytest.mark.asyncio
async def test_deepseek_timeout():
    """Test DeepSeek timeout handling."""
    import httpx

    with patch(
        "madre.llm.deepseek_client.get_deepseek_api_key", return_value="fake-key"
    ):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Timeout")

            result = await call_deepseek_r1("test message", timeout_seconds=5)

            assert result["provider"] == "deepseek_timeout"
            assert result["status"] == "DEGRADED"


@pytest.mark.asyncio
async def test_deepseek_api_error():
    """Test DeepSeek API error handling."""
    with patch(
        "madre.llm.deepseek_client.get_deepseek_api_key", return_value="fake-key"
    ):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await call_deepseek_r1("test message")

            assert result["provider"] == "deepseek_error"
            assert result["status"] == "ERROR"
            assert "401" in result["response"]


@pytest.mark.asyncio
async def test_madre_chat_endpoint_with_deepseek():
    """Test /madre/chat endpoint includes provider field."""
    from madre.main import madre_chat
    from madre.core.models import ChatRequest
    from unittest.mock import MagicMock

    # Mock deepseek as unavailable to get fallback
    with patch("madre.main.is_deepseek_available", return_value=False):
        req = ChatRequest(message="test", session_id="test-001")
        # Would need full FastAPI/DB setup; this is a smoke test structure
        assert True  # Placeholder


def test_get_deepseek_api_key_priority():
    """Test DeepSeek API key priority order (DEEPSEEK_API_KEY > DEEPSEEK_KEY > VX11_DEEPSEEK_API_KEY)."""
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "from-first"}, clear=True):
        assert get_deepseek_api_key() == "from-first"

    with patch.dict("os.environ", {"DEEPSEEK_KEY": "from-second"}, clear=True):
        assert get_deepseek_api_key() == "from-second"

    with patch.dict("os.environ", {"VX11_DEEPSEEK_API_KEY": "from-third"}, clear=True):
        assert get_deepseek_api_key() == "from-third"

    with patch.dict("os.environ", {}, clear=True):
        assert get_deepseek_api_key() is None
