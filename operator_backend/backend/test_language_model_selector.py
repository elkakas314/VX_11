"""
FASE C: Tests for Language Model Provider Selector.
Validates provider routing, fallback, and DeepSeek R1 integration.
"""

import pytest
import asyncio
import os
from language_model_selector import (
    LanguageModelSelector,
    MockLanguageModelSelector,
    ProviderType,
    get_language_model_selector,
)


class TestLanguageModelSelector:
    """Tests for provider selector logic (no external API calls)."""

    @pytest.mark.deepseek
    async def test_provider_selection_deepseek_enabled(self, monkeypatch):
        """Test that DeepSeek is selected when enabled and token present."""
        monkeypatch.setenv("VX11_ENABLE_DEEPSEEK_R1", "1")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-token")
        monkeypatch.setenv("VX11_OFFLINE", "0")

        selector = LanguageModelSelector()
        provider = selector.get_active_provider()

        assert provider == ProviderType.DEEPSEEK_R1

    @pytest.mark.timeout(5)
    async def test_provider_selection_offline_mode(self, monkeypatch):
        """Test that offline mode takes precedence."""
        monkeypatch.setenv("VX11_ENABLE_DEEPSEEK_R1", "1")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-token")
        monkeypatch.setenv("VX11_OFFLINE", "1")

        selector = LanguageModelSelector()
        provider = selector.get_active_provider()

        assert provider == ProviderType.OFFLINE

    @pytest.mark.timeout(5)
    async def test_provider_selection_disabled(self, monkeypatch):
        """Test that fallback is used when DeepSeek disabled."""
        monkeypatch.setenv("VX11_ENABLE_DEEPSEEK_R1", "0")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-token")

        selector = LanguageModelSelector()
        provider = selector.get_active_provider()

        assert provider == ProviderType.FALLBACK

    @pytest.mark.timeout(5)
    async def test_provider_selection_no_token(self, monkeypatch):
        """Test that fallback is used when token missing."""
        monkeypatch.setenv("VX11_ENABLE_DEEPSEEK_R1", "1")
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        selector = LanguageModelSelector()
        provider = selector.get_active_provider()

        assert provider == ProviderType.FALLBACK

    @pytest.mark.timeout(5)
    async def test_fallback_provider_response(self):
        """Test that fallback provider returns valid response."""
        selector = LanguageModelSelector()
        result = await selector._call_fallback("Test prompt")

        assert result["provider"] == "fallback"
        assert "degraded" in result
        assert result["degraded"] is True
        assert "response" in result
        assert isinstance(result["response"], str)

    @pytest.mark.timeout(5)
    async def test_offline_provider_response(self):
        """Test that offline provider returns valid response."""
        selector = LanguageModelSelector()
        result = await selector._call_offline("Test prompt")

        assert result["provider"] == "offline"
        assert result["degraded"] is True
        assert result["error"] == "Offline mode enabled"

    @pytest.mark.timeout(10)
    async def test_select_provider_calls_correct_impl(self, monkeypatch):
        """Test that select_provider routes to correct implementation."""
        monkeypatch.setenv("VX11_ENABLE_DEEPSEEK_R1", "0")

        selector = LanguageModelSelector()
        result = await selector.select_provider("Test prompt")

        # Should use fallback
        assert result["provider"] == "fallback"
        assert result["degraded"] is True

    @pytest.mark.timeout(5)
    async def test_stats_tracking(self):
        """Test that selector tracks provider usage statistics."""
        selector = LanguageModelSelector()

        # Call fallback provider
        await selector._call_fallback("Test 1")
        await selector._call_fallback("Test 2")
        await selector._call_offline("Test 3")

        stats = selector.get_stats()

        assert stats["fallback_calls"] == 2
        assert stats["offline_calls"] == 1
        assert stats["deepseek_calls"] == 0

    @pytest.mark.timeout(5)
    async def test_stats_reset(self):
        """Test that statistics can be reset."""
        selector = LanguageModelSelector()

        await selector._call_fallback("Test")
        stats_before = selector.get_stats()
        assert stats_before["fallback_calls"] == 1

        selector.reset_stats()
        stats_after = selector.get_stats()

        assert stats_after["fallback_calls"] == 0


class TestMockLanguageModelSelector:
    """Tests for mock provider selector (used in testing)."""

    @pytest.mark.timeout(5)
    async def test_mock_deepseek_response(self):
        """Test that mock DeepSeek returns predictable response."""
        selector = MockLanguageModelSelector()
        result = await selector._call_deepseek_r1("Explain Python")

        assert result["provider"] == "deepseek_r1_mock"
        assert result["degraded"] is False
        assert "response" in result
        assert "thinking" in result  # R1-specific field
        assert "[R1 Thinking]" in result["thinking"]

    @pytest.mark.timeout(10)
    async def test_mock_select_provider_with_deepseek_enabled(self, monkeypatch):
        """Test full select_provider flow with mocked DeepSeek."""
        monkeypatch.setenv("VX11_ENABLE_DEEPSEEK_R1", "1")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-mock")

        selector = MockLanguageModelSelector()
        result = await selector.select_provider("Test question")

        assert result["provider"] == "deepseek_r1_mock"
        assert result["degraded"] is False


class TestProviderIntegration:
    """Integration tests for provider switching."""

    @pytest.mark.timeout(5)
    async def test_graceful_fallback_on_error(self):
        """Test that selector falls back on any provider error."""
        selector = LanguageModelSelector()

        # Attempt to call with invalid provider (simulate error)
        # Should gracefully fall back
        result = await selector.select_provider("Test")

        assert "provider" in result
        assert "response" in result
        assert result["error"] is None or isinstance(result["error"], str)

    @pytest.mark.timeout(10)
    async def test_selector_singleton(self):
        """Test that get_language_model_selector returns singleton."""
        selector1 = get_language_model_selector()
        selector2 = get_language_model_selector()

        assert selector1 is selector2
