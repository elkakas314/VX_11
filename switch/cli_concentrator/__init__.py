"""
CLI Concentrator for Switch (Phase 3)
Manages CLI providers, prioritization, scoring, and execution.
"""

from .registry import CLIRegistry, get_cli_registry
from .scoring import CLIScorer
from .breaker import CircuitBreaker
from .executor import CLIExecutor
from .schemas import CLIRequest, CLIResponse, ProviderConfig

__all__ = [
    "CLIRegistry",
    "get_cli_registry",
    "CLIScorer",
    "CircuitBreaker",
    "CLIExecutor",
    "CLIRequest",
    "CLIResponse",
    "ProviderConfig",
]
