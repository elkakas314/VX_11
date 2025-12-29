"""
Provider pattern for DeepSeek R1 and fallback implementations.

Unified interface for LLM providers with mock support for tests.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import uuid
import time

import httpx

logger = logging.getLogger("vx11.providers")


class ProviderResponse(dict):
    """Standardized provider response format."""

    def __init__(
        self,
        status: str,
        provider: str,
        model: Optional[str],
        content: str,
        correlation_id: str,
        latency_ms: int,
        reasoning: Optional[str] = None,
        error: Optional[str] = None,
    ):
        super().__init__(
            status=status,
            provider=provider,
            model=model,
            content=content,
            correlation_id=correlation_id,
            latency_ms=latency_ms,
            reasoning=reasoning,
            error=error,
        )


class BaseProvider(ABC):
    """Abstract base class for all providers."""

    @abstractmethod
    async def __call__(
        self,
        prompt: str,
        correlation_id: str,
        timeout_seconds: int = 15,
    ) -> ProviderResponse:
        """Execute provider call.

        Args:
            prompt: User prompt/message
            correlation_id: Request tracking ID (echoed in response)
            timeout_seconds: Request timeout

        Returns:
            ProviderResponse with standardized schema
        """
        pass


class DeepSeekR1Provider(BaseProvider):
    """DeepSeek R1 reasoning model provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: str = "https://api.deepseek.com/v1/chat/completions",
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.endpoint = endpoint
        self.model = "deepseek-reasoner"

    async def __call__(
        self,
        prompt: str,
        correlation_id: str,
        timeout_seconds: int = 15,
    ) -> ProviderResponse:
        """Call DeepSeek R1 API."""
        start_time = time.time()

        if not self.api_key:
            latency_ms = int((time.time() - start_time) * 1000)
            return ProviderResponse(
                status="degraded",
                provider="deepseek_r1",
                model=None,
                content="DeepSeek API key not configured",
                correlation_id=correlation_id,
                latency_ms=latency_ms,
                error="missing_api_key",
            )

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "thinking": {"type": "enabled", "budget_tokens": 5000},
                    },
                )
                response.raise_for_status()
                data = response.json()

                content = ""
                reasoning = ""
                if "choices" in data and len(data["choices"]) > 0:
                    message = data["choices"][0].get("message", {})
                    content = message.get("content", "")
                    reasoning = message.get("thinking", "")

                latency_ms = int((time.time() - start_time) * 1000)
                return ProviderResponse(
                    status="success",
                    provider="deepseek_r1",
                    model=self.model,
                    content=content,
                    correlation_id=correlation_id,
                    latency_ms=latency_ms,
                    reasoning=reasoning,
                )

        except asyncio.TimeoutError:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"DeepSeek timeout after {latency_ms}ms")
            return ProviderResponse(
                status="degraded",
                provider="deepseek_r1",
                model=self.model,
                content="Request timeout",
                correlation_id=correlation_id,
                latency_ms=latency_ms,
                error="timeout",
            )
        except httpx.HTTPError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"DeepSeek HTTP error: {e}")
            return ProviderResponse(
                status="degraded",
                provider="deepseek_r1",
                model=self.model,
                content="API error",
                correlation_id=correlation_id,
                latency_ms=latency_ms,
                error=f"http_{type(e).__name__}",
            )
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"DeepSeek provider error: {e}")
            return ProviderResponse(
                status="error",
                provider="deepseek_r1",
                model=self.model,
                content="Provider error",
                correlation_id=correlation_id,
                latency_ms=latency_ms,
                error=str(e),
            )


class MockProvider(BaseProvider):
    """Deterministic mock provider for tests (no network)."""

    async def __call__(
        self,
        prompt: str,
        correlation_id: str,
        timeout_seconds: int = 15,
    ) -> ProviderResponse:
        """Return mock response (deterministic, no network)."""
        start_time = time.time()
        await asyncio.sleep(0.001)  # Minimal latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Deterministic response based on prompt
        prompt_hash = hash(prompt) % 1000
        reasoning = f"[Mock reasoning for prompt hash {prompt_hash}]"
        content = f"[Mock response] Analyzed: {prompt[:60]}... (hash: {prompt_hash})"

        return ProviderResponse(
            status="success",
            provider="mock",
            model="mock-reasoner",
            content=content,
            correlation_id=correlation_id,
            latency_ms=latency_ms,
            reasoning=reasoning,
        )


class LocalFallbackProvider(BaseProvider):
    """Local fallback provider (always works, no network)."""

    async def __call__(
        self,
        prompt: str,
        correlation_id: str,
        timeout_seconds: int = 15,
    ) -> ProviderResponse:
        """Return local fallback response."""
        start_time = time.time()
        await asyncio.sleep(0.001)
        latency_ms = int((time.time() - start_time) * 1000)

        # Simple echo fallback
        content = f"[Local fallback] Prompt received ({len(prompt)} chars). Provider not available."

        return ProviderResponse(
            status="degraded",
            provider="local",
            model=None,
            content=content,
            correlation_id=correlation_id,
            latency_ms=latency_ms,
            reasoning=None,
        )


class ProviderRegistry:
    """Registry for provider lookup and selection."""

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {
            "deepseek_r1": DeepSeekR1Provider(),
            "mock": MockProvider(),
            "local": LocalFallbackProvider(),
        }
        self._selected_provider = self._get_default_provider()

    def _get_default_provider(self) -> str:
        """Get default provider from env or config."""
        # Priority: explicit flag > mock mode > deepseek > local
        if os.environ.get("VX11_MOCK_PROVIDERS") == "true":
            return "mock"
        return os.environ.get("VX11_DEEPSEEK_PROVIDER", "local")

    def get_provider(self, name: Optional[str] = None) -> BaseProvider:
        """Get provider by name or use selected default."""
        provider_name = name or self._selected_provider
        return self._providers.get(provider_name, self._providers["local"])

    def select_provider(self, name: str) -> None:
        """Change selected default provider."""
        if name in self._providers:
            self._selected_provider = name
            logger.info(f"Provider switched to: {name}")
        else:
            logger.warning(f"Unknown provider: {name}, keeping default")

    def register_provider(self, name: str, provider: BaseProvider) -> None:
        """Register custom provider."""
        self._providers[name] = provider
        logger.info(f"Provider registered: {name}")


# Global registry instance
_default_registry = ProviderRegistry()


def get_provider(name: Optional[str] = None) -> BaseProvider:
    """Get provider from global registry."""
    return _default_registry.get_provider(name)


def get_registry() -> ProviderRegistry:
    """Get global provider registry."""
    return _default_registry
