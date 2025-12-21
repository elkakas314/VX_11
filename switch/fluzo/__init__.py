"""
FLUZO: Low-consumption telemetry signals for adaptive scoring.
Collects system metrics (CPU, RAM, power) without decision-making.
"""

from .signals import FLUZOSignals
from .profile import FLUZOProfile
from .client import FLUZOClient

__all__ = ["FLUZOSignals", "FLUZOProfile", "FLUZOClient"]
