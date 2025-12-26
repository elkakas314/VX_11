"""
FASE C: Language Model Provider Selector (DeepSeek R1 Integration).

Supports:
- DeepSeek R1 (primary, when enabled and token available)
- Fallback provider (when offline or disabled)
- Graceful degradation
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any
from enum import Enum


class ProviderType(str, Enum):
    """Supported language model providers."""

    DEEPSEEK_R1 = "deepseek_r1"
    FALLBACK = "fallback"
    OFFLINE = "offline"


class LanguageModelSelector:
    """
    Selector for language model providers.
    Routes requests to DeepSeek R1 or fallback based on config.
    """

    def __init__(self):
        """Initialize selector with environment config."""
        self.deepseek_enabled = os.getenv("VX11_ENABLE_DEEPSEEK_R1", "0") == "1"
        self.deepseek_token = os.getenv("DEEPSEEK_API_KEY")
        self.offline_mode = os.getenv("VX11_OFFLINE", "0") == "1"
        self.testing_mode = os.getenv("VX11_TESTING_MODE", "0") == "1"

        # Provider selection stats
        self.stats = {
            "deepseek_calls": 0,
            "fallback_calls": 0,
            "offline_calls": 0,
            "provider_errors": 0,
        }

    def get_active_provider(self) -> ProviderType:
        """Determine which provider to use."""
        if self.offline_mode:
            return ProviderType.OFFLINE

        if not self.deepseek_enabled:
            return ProviderType.FALLBACK

        if self.testing_mode:
            return ProviderType.FALLBACK  # Use mock in tests

        if self.deepseek_token:
            return ProviderType.DEEPSEEK_R1

        return ProviderType.FALLBACK

    async def select_provider(self, prompt: str) -> Dict[str, Any]:
        """
        Select and call appropriate provider for prompt.

        Returns:
            {
                "provider": str,
                "response": str,
                "degraded": bool,
                "error": Optional[str]
            }
        """
        provider_type = self.get_active_provider()

        try:
            if provider_type == ProviderType.DEEPSEEK_R1:
                return await self._call_deepseek_r1(prompt)
            elif provider_type == ProviderType.OFFLINE:
                return await self._call_offline(prompt)
            else:
                return await self._call_fallback(prompt)

        except Exception as e:
            self.stats["provider_errors"] += 1
            # Fallback on any error
            return await self._call_fallback(prompt)

    async def _call_deepseek_r1(self, prompt: str) -> Dict[str, Any]:
        """Call DeepSeek R1 API."""
        self.stats["deepseek_calls"] += 1

        # Import here to avoid hard dependency
        try:
            from config.deepseek import call_deepseek_reasoner

            response = await asyncio.to_thread(call_deepseek_reasoner, prompt)

            return {
                "provider": "deepseek_r1",
                "response": response,
                "degraded": False,
                "error": None,
            }
        except Exception as e:
            print(f"[WARN] DeepSeek R1 failed: {e}")
            self.stats["provider_errors"] += 1
            # Cascade to fallback
            return await self._call_fallback(prompt)

    async def _call_fallback(self, prompt: str) -> Dict[str, Any]:
        """Call fallback provider."""
        self.stats["fallback_calls"] += 1

        # Simple fallback: echo prompt or mock response
        fallback_response = f"[Fallback] Processed: {prompt[:100]}..."

        return {
            "provider": "fallback",
            "response": fallback_response,
            "degraded": True,  # Mark as degraded mode
            "error": None,
        }

    async def _call_offline(self, prompt: str) -> Dict[str, Any]:
        """Call offline-safe provider."""
        self.stats["offline_calls"] += 1

        # Offline response (no network)
        offline_response = f"[Offline Mode] Cannot process external requests. Input length: {len(prompt)}"

        return {
            "provider": "offline",
            "response": offline_response,
            "degraded": True,
            "error": "Offline mode enabled",
        }

    def get_stats(self) -> Dict[str, int]:
        """Get provider selection statistics."""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            "deepseek_calls": 0,
            "fallback_calls": 0,
            "offline_calls": 0,
            "provider_errors": 0,
        }


# Singleton instance
_selector_instance: Optional[LanguageModelSelector] = None


def get_language_model_selector() -> LanguageModelSelector:
    """Get or create singleton language model selector."""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = LanguageModelSelector()
    return _selector_instance


# For tests
class MockLanguageModelSelector(LanguageModelSelector):
    """Mock selector for testing without DeepSeek API calls."""

    async def _call_deepseek_r1(self, prompt: str) -> Dict[str, Any]:
        """Mock DeepSeek R1 response."""
        # Simulate R1 reasoning process
        mock_thinking = f"[R1 Thinking] Analyzing: {prompt[:50]}... [/R1 Thinking]"
        mock_response = f"Mock R1 response to: {prompt[:100]}"

        return {
            "provider": "deepseek_r1_mock",
            "response": mock_response,
            "degraded": False,
            "error": None,
            "thinking": mock_thinking,  # R1-specific field
        }
