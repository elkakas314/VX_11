"""
Lightweight compression helpers (heuristic only).
"""

from __future__ import annotations

from typing import Dict, List


class CompressionOps:
    def suggest_gain(self, samples: List[float]) -> float:
        if not samples:
            return 0.0
        peak = max(abs(s) for s in samples)
        if peak == 0:
            return 0.0
        if peak > 0.9:
            return -3.0
        if peak > 0.6:
            return -1.5
        return 0.0

    def envelope(self, samples: List[float]) -> List[float]:
        # Placeholder envelope follower
        env = []
        prev = 0.0
        for s in samples:
            level = abs(s) * 0.2 + prev * 0.8
            env.append(level)
            prev = level
        return env
