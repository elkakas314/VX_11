"""
FLUZO client: simple API to get signals and profile.
"""

import os
from typing import Dict, Optional
from datetime import datetime
from .signals import FLUZOSignals
from .profile import FLUZOProfile, FLUZOMode


class FLUZOClient:
    """Simple FLUZO client interface."""

    def __init__(self):
        """Initialize client."""
        self.signals = FLUZOSignals()
        self.profile = FLUZOProfile()
        self._persist_enabled = os.getenv("VX11_FLUZO_PERSIST", "0") == "1"

    def get_signals(self) -> Dict[str, any]:
        """Get current system signals."""
        return self.signals.collect()

    def get_profile(self) -> Dict[str, any]:
        """Get FLUZO profile (mode + reasoning)."""
        signals = self.get_signals()
        profile = self.profile.get_profile(signals)

        if self._persist_enabled:
            self._persist_to_db(signals)

        return profile

    def get_mode(self) -> FLUZOMode:
        """Get current FLUZO mode."""
        return self.get_profile()["mode"]

    def _persist_to_db(self, signals: Dict[str, any]):
        """Optionally persist signals to database."""
        try:
            from config.db_schema import get_session, FluzoSignal

            db = get_session()
            sig = FluzoSignal(
                timestamp=signals["timestamp"],
                cpu_load_1m=signals["cpu_load_1m"],
                mem_pct=signals["memory_pct"],
                on_ac=signals["on_ac"],
                battery_pct=signals["battery_pct"],
                profile=self.profile.derive_mode(signals),
            )
            db.add(sig)
            db.commit()
        except Exception:
            pass  # Silently fail if DB unavailable
        finally:
            try:
                db.close()
            except:
                pass
