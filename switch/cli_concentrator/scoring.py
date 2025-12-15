"""
Scoring engine for CLI providers.
Incorporates latency, cost, quotas, and FLUZO signals.
"""

import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .schemas import ProviderConfig, CLIRequest
from .registry import CLIRegistry
from .breaker import CircuitBreaker


class CLIScorer:
    """Scores CLI providers based on multiple factors."""

    def __init__(self, registry: CLIRegistry, breaker: CircuitBreaker):
        """Initialize scorer."""
        self.registry = registry
        self.breaker = breaker
        self.fluzo_mode = os.getenv("VX11_FLUZO_MODE", "balanced")

    def score_provider(
        self,
        provider: ProviderConfig,
        request: CLIRequest,
        fluzo_data: Optional[Dict] = None,
    ) -> Tuple[float, Dict]:
        """
        Score a provider (0-100, higher = better).

        Returns:
            (score, debug_info)
        """
        debug = {
            "provider_id": provider.provider_id,
            "factors": {},
        }

        # Factor 1: Priority (lower = higher score)
        priority_score = max(0, 100 - provider.priority)
        debug["factors"]["priority"] = priority_score

        # Factor 2: Availability (breaker state)
        if not self.breaker.is_available(provider.provider_id):
            debug["factors"]["breaker"] = 0.0
            return 0.0, debug
        debug["factors"]["breaker"] = 100.0

        # Factor 3: Auth state
        auth_score = 100.0 if provider.auth_state == "ok" else 0.0
        debug["factors"]["auth"] = auth_score
        if auth_score == 0.0:
            return 0.0, debug

        # Factor 4: Quota (if limited)
        quota_score = 100.0
        if provider.quota_daily > 0 and provider.quota_daily < 100:
            quota_score = (provider.quota_daily / 100.0) * 100
        debug["factors"]["quota"] = quota_score

        # Factor 5: FLUZO influence (if provided)
        fluzo_score = 100.0
        if fluzo_data:
            fluzo_score = self._apply_fluzo_multiplier(fluzo_data, provider, request)
        debug["factors"]["fluzo"] = fluzo_score

        # Combine scores (weighted average)
        weights = {
            "priority": 0.4,
            "breaker": 0.2,
            "auth": 0.1,
            "quota": 0.15,
            "fluzo": 0.15,
        }

        final_score = (
            priority_score * weights["priority"]
            + 100.0 * weights["breaker"]
            + auth_score * weights["auth"]
            + quota_score * weights["quota"]
            + fluzo_score * weights["fluzo"]
        )

        debug["final_score"] = final_score
        return final_score, debug

    def _apply_fluzo_multiplier(
        self, fluzo_data: Dict, provider: ProviderConfig, request: CLIRequest
    ) -> float:
        """Apply FLUZO signal to scoring."""
        mode = fluzo_data.get("profile", "balanced")

        if mode == "low_power":
            # Prefer cheaper, less latent CLIs
            cost_penalty = 0.7 if provider.kind != "copilot_cli" else 0.9
            return 85.0 * cost_penalty

        elif mode == "performance":
            # Allow heavier CLIs
            return 100.0

        else:  # balanced
            return 90.0

    def select_best_provider(
        self,
        request: CLIRequest,
        fluzo_data: Optional[Dict] = None,
    ) -> Tuple[Optional[ProviderConfig], Dict]:
        """
        Select best provider for request.

        Returns:
            (provider, scoring_debug)
        """
        debug = {
            "candidate_scores": [],
            "selected_provider": None,
        }

        # Get candidates by intent
        candidates = self.registry.list_providers()
        if not candidates:
            return None, debug

        # Score each candidate
        scores = []
        for provider in candidates:
            score, score_debug = self.score_provider(provider, request, fluzo_data)
            scores.append((provider, score, score_debug))
            debug["candidate_scores"].append(
                {
                    "provider_id": provider.provider_id,
                    "score": score,
                    "debug": score_debug,
                }
            )

        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)

        # If provider_preference specified, try that first
        if request.provider_preference:
            for provider, score, _ in scores:
                if provider.provider_id == request.provider_preference:
                    debug["selected_provider"] = provider.provider_id
                    debug["reason"] = "user_preference"
                    return provider, debug

        # Otherwise use highest score
        if scores and scores[0][1] > 0:
            best_provider = scores[0][0]
            debug["selected_provider"] = best_provider.provider_id
            debug["reason"] = "highest_score"
            return best_provider, debug

        return None, debug
