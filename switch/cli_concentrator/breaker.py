"""
Circuit breaker for CLI providers.
Prevents cascading failures.
"""

from typing import Dict
from datetime import datetime, timedelta
from enum import Enum


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing; reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Simple circuit breaker for CLI providers."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_s: int = 60):
        """Initialize breaker."""
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.states: Dict[str, Dict] = {}

    def _ensure_state(self, provider_id: str):
        """Ensure provider has a state entry."""
        if provider_id not in self.states:
            self.states[provider_id] = {
                "state": CircuitBreakerState.CLOSED,
                "failure_count": 0,
                "last_failure_at": None,
                "opened_at": None,
            }

    def record_success(self, provider_id: str):
        """Record successful call."""
        self._ensure_state(provider_id)
        self.states[provider_id]["failure_count"] = 0
        self.states[provider_id]["state"] = CircuitBreakerState.CLOSED

    def record_failure(self, provider_id: str):
        """Record failed call."""
        self._ensure_state(provider_id)
        self.states[provider_id]["failure_count"] += 1
        self.states[provider_id]["last_failure_at"] = datetime.utcnow()

        if self.states[provider_id]["failure_count"] >= self.failure_threshold:
            self.states[provider_id]["state"] = CircuitBreakerState.OPEN
            self.states[provider_id]["opened_at"] = datetime.utcnow()

    def is_available(self, provider_id: str) -> bool:
        """Check if provider is available."""
        self._ensure_state(provider_id)
        state_info = self.states[provider_id]
        state = state_info["state"]

        if state == CircuitBreakerState.CLOSED:
            return True

        if state == CircuitBreakerState.OPEN:
            # Check if we can transition to HALF_OPEN
            if state_info["opened_at"]:
                elapsed = (datetime.utcnow() - state_info["opened_at"]).total_seconds()
                if elapsed > self.recovery_timeout_s:
                    state_info["state"] = CircuitBreakerState.HALF_OPEN
                    state_info["failure_count"] = 0
                    return True
            return False

        if state == CircuitBreakerState.HALF_OPEN:
            return True

        return False

    def get_state(self, provider_id: str) -> str:
        """Get current state."""
        self._ensure_state(provider_id)
        return self.states[provider_id]["state"].value
