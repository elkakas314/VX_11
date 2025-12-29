"""
Tests for DeepSeek R1 provider implementation.
"""

import pytest
import asyncio
from switch.providers import (
    DeepSeekR1Provider,
    MockProvider,
    LocalFallbackProvider,
    ProviderRegistry,
    get_provider,
    ProviderResponse,
)


class TestMockProvider:
    """Test mock provider (deterministic, no network)."""

    @pytest.mark.asyncio
    async def test_mock_provider_deterministic(self):
        """Mock provider returns deterministic response."""
        provider = MockProvider()
        correlation_id = "test-123"

        # Same prompt → same hash → same response
        response1 = await provider("test prompt", correlation_id)
        response2 = await provider("test prompt", correlation_id)

        assert response1["status"] == "success"
        assert response1["provider"] == "mock"
        assert response1["content"] == response2["content"]
        assert response1["reasoning"] == response2["reasoning"]
        assert response1["correlation_id"] == correlation_id

    @pytest.mark.asyncio
    async def test_mock_provider_fast(self):
        """Mock provider responds quickly (<10ms)."""
        provider = MockProvider()

        response = await provider("test", "test-id")
        assert response["latency_ms"] < 10


class TestLocalFallbackProvider:
    """Test local fallback provider."""

    @pytest.mark.asyncio
    async def test_local_fallback_always_responds(self):
        """Local fallback always responds."""
        provider = LocalFallbackProvider()

        response = await provider("any prompt", "fallback-id")
        assert response["status"] == "degraded"
        assert response["provider"] == "local"
        assert response["content"] != ""
        assert response["correlation_id"] == "fallback-id"

    @pytest.mark.asyncio
    async def test_local_fallback_fast(self):
        """Local fallback is fast."""
        provider = LocalFallbackProvider()

        response = await provider("test", "test-id")
        assert response["latency_ms"] < 10


class TestDeepSeekR1Provider:
    """Test DeepSeek R1 provider (with mock API)."""

    @pytest.mark.asyncio
    async def test_deepseek_missing_api_key(self):
        """DeepSeek degrades gracefully without API key."""
        provider = DeepSeekR1Provider(api_key=None)

        response = await provider("test", "deepseek-no-key")
        assert response["status"] == "degraded"
        assert response["provider"] == "deepseek_r1"
        assert response["error"] == "missing_api_key"
        assert response["correlation_id"] == "deepseek-no-key"

    @pytest.mark.asyncio
    async def test_deepseek_timeout(self):
        """DeepSeek times out or fails gracefully."""
        # Using fake key + very short timeout to trigger timeout/connection error
        provider = DeepSeekR1Provider(api_key="fake-key")

        response = await provider("test", "deepseek-timeout", timeout_seconds=0.001)
        # Either timeout or connection error is acceptable
        assert response["status"] == "degraded"
        assert response["error"] in (
            "timeout",
            "http_ConnectTimeout",
            "http_ReadTimeout",
        )


class TestProviderRegistry:
    """Test provider registry and selection."""

    def test_registry_get_provider_default(self):
        """Registry returns local provider by default."""
        registry = ProviderRegistry()
        provider = registry.get_provider()

        assert isinstance(provider, LocalFallbackProvider)

    def test_registry_get_specific_provider(self):
        """Registry can retrieve specific provider."""
        registry = ProviderRegistry()

        mock_provider = registry.get_provider("mock")
        assert isinstance(mock_provider, MockProvider)

        local_provider = registry.get_provider("local")
        assert isinstance(local_provider, LocalFallbackProvider)

    def test_registry_select_provider(self):
        """Registry can change selected default."""
        registry = ProviderRegistry()
        registry.select_provider("mock")

        provider = registry.get_provider()
        assert isinstance(provider, MockProvider)

    def test_registry_unknown_provider_fallback(self):
        """Registry falls back to local for unknown provider."""
        registry = ProviderRegistry()
        provider = registry.get_provider("unknown")

        assert isinstance(provider, LocalFallbackProvider)


class TestProviderResponse:
    """Test ProviderResponse structure."""

    def test_provider_response_dict_compatibility(self):
        """ProviderResponse is dict-compatible."""
        response = ProviderResponse(
            status="success",
            provider="mock",
            model="mock-reasoner",
            content="test",
            correlation_id="test-123",
            latency_ms=5,
        )

        assert response["status"] == "success"
        assert response["provider"] == "mock"
        assert response["correlation_id"] == "test-123"

    def test_provider_response_with_reasoning(self):
        """ProviderResponse supports reasoning field."""
        response = ProviderResponse(
            status="success",
            provider="deepseek_r1",
            model="deepseek-reasoner",
            content="output",
            correlation_id="ds-123",
            latency_ms=100,
            reasoning="[R1 reasoning here]",
        )

        assert response["reasoning"] == "[R1 reasoning here]"


@pytest.mark.asyncio
async def test_get_provider_global():
    """Global get_provider function works."""
    provider = get_provider()
    assert isinstance(provider, LocalFallbackProvider)

    mock_provider = get_provider("mock")
    assert isinstance(mock_provider, MockProvider)


# Integration test: full call chain
@pytest.mark.asyncio
async def test_provider_call_chain():
    """Test full provider call chain with mock."""
    provider = MockProvider()
    correlation_id = "integration-test-123"

    response = await provider(
        prompt="Analyze this audio",
        correlation_id=correlation_id,
        timeout_seconds=5,
    )

    assert isinstance(response, ProviderResponse)
    assert response["status"] == "success"
    assert response["provider"] == "mock"
    assert response["correlation_id"] == correlation_id
    assert response["content"]  # Non-empty
    assert response["latency_ms"] > 0
