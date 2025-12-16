"""
FLUZO profile: derives mode (low_power, balanced, performance) from signals.
"""

from typing import Dict, Literal
from .signals import FLUZOSignals


FLUZOMode = Literal["low_power", "balanced", "performance"]


class FLUZOProfile:
    """Derives FLUZO mode from system signals."""

    def __init__(
        self,
        cpu_threshold_low: float = 30.0,
        cpu_threshold_high: float = 70.0,
        memory_threshold_low: float = 40.0,
        memory_threshold_high: float = 75.0,
        battery_threshold_low: int = 20,
    ):
        """Initialize profiler with thresholds."""
        self.cpu_threshold_low = cpu_threshold_low
        self.cpu_threshold_high = cpu_threshold_high
        self.memory_threshold_low = memory_threshold_low
        self.memory_threshold_high = memory_threshold_high
        self.battery_threshold_low = battery_threshold_low

    def derive_mode(self, signals: Dict[str, any]) -> FLUZOMode:
        """
        Derive mode from signals.

        Logic:
        - low_power: battery < threshold OR (cpu+memory high)
        - high_perf: AC power AND (cpu+memory low)
        - balanced: otherwise
        """
        cpu_1m = signals.get("cpu_load_1m", 0.0)
        memory_pct = signals.get("memory_pct", 0.0)
        on_ac = signals.get("on_ac", True)
        battery_pct = signals.get("battery_pct")

        # Check power state
        is_low_power_battery = (
            not on_ac and battery_pct and battery_pct <= self.battery_threshold_low
        )

        # Check system load
        cpu_high = cpu_1m > self.cpu_threshold_high
        memory_high = memory_pct > self.memory_threshold_high
        cpu_low = cpu_1m < self.cpu_threshold_low
        memory_low = memory_pct < self.memory_threshold_low

        if is_low_power_battery or (cpu_high and memory_high):
            return "low_power"
        elif on_ac and cpu_low and memory_low:
            return "performance"
        else:
            return "balanced"

    def get_profile(self, signals: Dict[str, any]) -> Dict[str, any]:
        """
        Get complete profile.

        Returns:
            {
                "mode": "low_power" | "balanced" | "performance",
                "signals": {...},
                "reasoning": str,
            }
        """
        mode = self.derive_mode(signals)

        reasoning = ""
        if mode == "low_power":
            reasoning = "Low power: battery critical or high load"
        elif mode == "performance":
            reasoning = "Performance: AC power and low system load"
        else:
            reasoning = "Balanced: normal operation"

        return {
            "mode": mode,
            "signals": signals,
            "reasoning": reasoning,
        }
