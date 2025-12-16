"""
Copilot CLI provider wrapper.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


# Local lightweight ProviderConfig to avoid an unresolved absolute import.
# Keep fields minimal and extensible to match callers expecting an auth_state attribute.
@dataclass
class ProviderConfig:
    auth_state: str = "unknown"
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


# Simple alias for CLI responses used by providers.
CLIResponse = Dict[str, Any]


class CopilotCLIProvider:
    """Wrapper for Copilot CLI provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize provider."""
        self.config = config

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.config.auth_state == "ok"

    def call(
        self, prompt: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Copilot CLI.

        Returns:
            {
                "success": bool,
                "reply": str,
                "latency_ms": int,
                "tokens_estimated": int,
                "cost_estimated": float,
                "error_class": Optional[str],
            }
        """
        # Placeholder: in production, would invoke actual copilot-cli
        # For now, return mock response
        return {
            "success": self.is_available(),
            "reply": (
                f"[Copilot CLI mock] Received: {prompt[:50]}..."
                if self.is_available()
                else ""
            ),
            "latency_ms": 100,
            "tokens_estimated": len(prompt.split()),
            "cost_estimated": 0.0,
            "error_class": None if self.is_available() else "not_available",
        }
