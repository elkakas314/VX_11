"""
Window Manager for Madre - TTL-gated service activation.

INVARIANT: SOLO_MADRE default. Windows expire after TTL.
Purpose: Control when switch/spawner are allowed to execute.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Literal, Tuple
from threading import Lock
import asyncio
import uuid

WindowTarget = Literal["switch", "spawner", "hermes"]


class Window:
    """Represents an open window for a service."""

    def __init__(
        self, target: WindowTarget, ttl_seconds: int, reason: Optional[str] = None
    ):
        self.target = target
        self.ttl_seconds = ttl_seconds
        self.reason = reason
        self.opened_at = datetime.utcnow()
        self.expires_at = self.opened_at + timedelta(seconds=ttl_seconds)
        self.window_id = str(uuid.uuid4())

    def is_expired(self) -> bool:
        """Check if window TTL has passed."""
        return datetime.utcnow() >= self.expires_at

    def ttl_remaining(self) -> int:
        """Seconds remaining until expiration."""
        remaining = (self.expires_at - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))

    def to_dict(self) -> dict:
        """Convert to response format."""
        return {
            "target": self.target,
            "is_open": not self.is_expired(),
            "ttl_remaining_seconds": self.ttl_remaining(),
            "opened_at": self.opened_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "window_id": self.window_id,
        }


class WindowManager:
    """
    Centralized window management for Madre.

    INVARIANT:
    - SOLO_MADRE policy always on (default)
    - Windows are temporary, TTL-gated
    - Cleanup happens automatically when TTL expires
    - Thread-safe: uses lock for concurrent access
    """

    def __init__(self):
        self._windows: Dict[WindowTarget, Optional[Window]] = {
            "switch": None,
            "spawner": None,
            "hermes": None,
        }
        self._lock = Lock()

    def open_window(
        self, target: WindowTarget, ttl_seconds: int = 300, reason: Optional[str] = None
    ) -> Dict:
        """
        Open a time-gated window for a service.

        Returns: Window state dict
        """
        with self._lock:
            # Close any existing window for this target
            if self._windows[target] is not None:
                old_window = self._windows[target]
                old_was_open = not old_window.is_expired()
            else:
                old_was_open = False

            # Create new window
            window = Window(target, ttl_seconds, reason)
            self._windows[target] = window

            return {
                "target": target,
                "opened": True,
                "previous_was_open": old_was_open,
                "window": window.to_dict(),
            }

    def close_window(self, target: WindowTarget, reason: Optional[str] = None) -> Dict:
        """
        Explicitly close a window.

        Returns: Closure confirmation dict
        """
        with self._lock:
            window = self._windows[target]
            was_open = window is not None and not window.is_expired()

            self._windows[target] = None

            return {
                "target": target,
                "closed": True,
                "was_open": was_open,
                "reason": reason,
            }

    def get_window_status(self, target: WindowTarget) -> Dict:
        """
        Get current window status for a target.

        Returns: Status dict
        """
        with self._lock:
            window = self._windows[target]

            if window is None:
                return {
                    "target": target,
                    "is_open": False,
                    "ttl_remaining_seconds": None,
                    "opened_at": None,
                    "expires_at": None,
                }

            if window.is_expired():
                # Auto-cleanup if expired
                self._windows[target] = None
                return {
                    "target": target,
                    "is_open": False,
                    "ttl_remaining_seconds": 0,
                    "opened_at": window.opened_at.isoformat(),
                    "expires_at": window.expires_at.isoformat(),
                }

            return {
                "target": target,
                "is_open": True,
                "ttl_remaining_seconds": window.ttl_remaining(),
                "opened_at": window.opened_at.isoformat(),
                "expires_at": window.expires_at.isoformat(),
            }

    def is_window_open(self, target: WindowTarget) -> bool:
        """Check if window is currently open (not expired, not closed)."""
        status = self.get_window_status(target)
        return status.get("is_open", False)

    def cleanup_expired_windows(self) -> Dict[str, bool]:
        """
        Cleanup any expired windows (called periodically).

        Returns: Dict of cleaned targets
        """
        with self._lock:
            cleaned = {}
            targets: Tuple[WindowTarget, ...] = ("switch", "spawner", "hermes")
            for target in targets:
                window = self._windows[target]
                if window is not None and window.is_expired():
                    self._windows[target] = None
                    cleaned[target] = True
                else:
                    cleaned[target] = False
            return cleaned

    def get_all_window_states(self) -> Dict:
        """Get status of all windows."""
        return {
            "switch": self.get_window_status("switch"),
            "spawner": self.get_window_status("spawner"),
            "hermes": self.get_window_status("hermes"),
            "policy": "SOLO_MADRE (default)",
            "cleanup_scheduled": True,
        }


# Global singleton instance
_window_manager: Optional[WindowManager] = None


def get_window_manager() -> WindowManager:
    """Get or create the global window manager."""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager()
    return _window_manager


async def window_cleanup_worker():
    """
    Background worker to cleanup expired windows.
    Run this periodically (e.g., every 10 seconds).
    """
    manager = get_window_manager()
    while True:
        try:
            cleaned = manager.cleanup_expired_windows()
            # Log cleaned windows if needed
            if any(cleaned.values()):
                pass  # Silent cleanup
        except Exception as e:
            # Log error but continue
            pass

        await asyncio.sleep(10)  # Check every 10 seconds
