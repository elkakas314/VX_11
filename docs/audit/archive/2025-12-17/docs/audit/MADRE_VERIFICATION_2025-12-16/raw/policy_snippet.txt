"""Policy Engine: risk classification + confirmation."""

import secrets
import logging
from typing import Optional, Dict, Any
from .models import RiskLevel

log = logging.getLogger("madre.policy")


class PolicyEngine:
    """Risk classification and confirmation token management."""

    # Allowlist: safe targets/actions (no confirmation needed)
    ALLOWLIST = {
        ("switch", "status"),
        ("hormiguero", "status"),
        ("manifestator", "status"),
        ("shub", "status"),
        ("tentaculo_link", "status"),
        ("hermes", "status"),
        ("health", "*"),
        ("read", "*"),
        ("list", "*"),
        ("analyze", "*"),
    }

    # High-risk actions (ALWAYS require confirmation)
    HIGH_RISK_ACTIONS = {
        "delete",
        "drop",
        "destroy",
        "reset",
        "migrate",
        "restore",
        "stop",
        "kill",
        "terminate",
    }

    # Med-risk actions (conditional confirmation)
    MED_RISK_ACTIONS = {
        "restart",
        "reboot",
        "suspend",
        "cleanup",
        "patch",
        "update",
    }

    @staticmethod
    def classify_risk(target: str, action: str) -> RiskLevel:
        """Classify action risk level."""
        action_lower = action.lower()
        target_lower = target.lower()

        # Deny suicidal actions: madre, tentaculo_link
        if target_lower in ["madre", "tentaculo_link"]:
            if action_lower in ["delete", "stop", "kill", "destroy"]:
                log.warning(f"Deny suicidal action: {action} on {target}")
                return RiskLevel.HIGH

        # Check allowlist
        if (target_lower, action_lower) in PolicyEngine.ALLOWLIST:
            return RiskLevel.LOW
        if (target_lower, "*") in PolicyEngine.ALLOWLIST:
            return RiskLevel.LOW

        # Destructive verbs are always HIGH
        if action_lower == "delete":
            return RiskLevel.HIGH

        # Check high-risk
        for hr in PolicyEngine.HIGH_RISK_ACTIONS:
            if hr in action_lower:
                return RiskLevel.HIGH

        # Check med-risk
        for mr in PolicyEngine.MED_RISK_ACTIONS:
            if mr in action_lower:
                return RiskLevel.MED

        # Default: LOW for unknown
        return RiskLevel.LOW

    @staticmethod
    def requires_confirmation(risk: RiskLevel, policy_override: bool = False) -> bool:
        """Check if confirmation is required."""
        if policy_override:
            return False
        return risk in [RiskLevel.MED, RiskLevel.HIGH]

    @staticmethod
    def generate_confirm_token() -> str:
        """Generate secure confirmation token."""
        return secrets.token_urlsafe(16)

    @staticmethod
    def validate_confirm_token(provided: str, stored: str) -> bool:
        """Validate confirmation token (timing-safe)."""
        return secrets.compare_digest(provided, stored)
