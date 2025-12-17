"""Fallback DSL Parser: simple keyword-based intent extraction."""

import re
from .models import DSL, ModeEnum, RiskLevel
import logging

log = logging.getLogger("madre.parser")


class FallbackParser:
    """Keyword-based parser when Switch is unavailable."""

    # Destructive verbs (HIGH risk, require confirmation)
    DESTRUCTIVE_VERBS = {
        "delete",
        "remove",
        "drop",
        "destroy",
        "kill",
        "terminate",
        "reset",
        "wipe",
        "truncate",
        "erase",
    }

    # Audio/Shub keywords
    AUDIO_KEYWORDS = {
        "mix",
        "mezcla",
        "mixing",
        "blend",
        "master",
        "mastering",
        "audio",
        "reaper",
        "daw",
        "plugin",
        "stem",
        "render",
        "eq",
        "compress",
        "limiter",
        "shub",
        "engineer",
        "wave",
        "track",
        "normalize",
    }

    # Action patterns
    ACTION_PATTERNS = {
        "run": r"run|execute|perform|start",
        "stop": r"stop|pause|halt",
        "analyze": r"analyze|analyze|check|scan|audit",
        "list": r"list|show|get|what|tell",
        "help": r"help|what|how",
    }

    @staticmethod
    def parse(text: str, session_mode: str = "MADRE") -> DSL:
        """Parse text into DSL. Returns simple structure."""
        text_lower = text.lower()
        warnings = []

        # Detect destructive intent (HIGHEST priority)
        is_destructive = any(
            verb in text_lower for verb in FallbackParser.DESTRUCTIVE_VERBS
        )
        if is_destructive:
            warnings.append("destructive_intent_detected")
            return DSL(
                domain="system",
                action="delete",
                parameters={"original_message": text},
                confidence=0.9,  # High confidence for destructive
                original_text=text,
                warnings=warnings,
            )

        # Detect mode
        is_audio = any(kw in text_lower for kw in FallbackParser.AUDIO_KEYWORDS)
        detected_mode = "AUDIO_ENGINEER" if is_audio else "MADRE"

        # If session has a preferred mode, respect it
        mode = (
            session_mode
            if session_mode in ["MADRE", "AUDIO_ENGINEER"]
            else detected_mode
        )

        # Extract domain
        domain = "audio" if is_audio else "general"

        # Extract action
        action = "chat"
        for action_name, pattern in FallbackParser.ACTION_PATTERNS.items():
            if re.search(pattern, text_lower):
                action = action_name
                break

        # Calculate confidence (low, since it's fallback)
        confidence = 0.3

        return DSL(
            domain=domain,
            action=action,
            parameters={"original_message": text},
            confidence=confidence,
            original_text=text,
            warnings=warnings,
        )

    @staticmethod
    def extract_parameters(text: str) -> dict:
        """Extract simple key-value parameters from text (stub)."""
        return {}
