"""
Power Windows Manager for VX11 Madre v7

Gestiona ventanas (servicios temporales o indefinidos) con TTL automático.
- window_id: UUID único
- deadline: None (hold) o datetime (ttl)
- mode: "ttl" (temporal) o "hold" (indefinido)
- state: "open" | "closed" | "expired" | "error"
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Set, List, Dict, Any
from uuid import uuid4
import os

log = logging.getLogger("vx11.madre.power_windows")


class Window:
    """Representa una ventana de servicios."""

    def __init__(
        self,
        window_id: str,
        services: Set[str],
        ttl_sec: Optional[int],
        mode: str,
        reason: str,
        created_at: Optional[datetime] = None,
    ):
        self.window_id = window_id
        self.services = services
        self.mode = mode  # "ttl" o "hold"
        self.reason = reason
        self.state = "open"
        self.created_at = created_at or datetime.now(timezone.utc)

        # Deadline (None si hold)
        if mode == "ttl" and ttl_sec:
            self.deadline = self.created_at + timedelta(seconds=ttl_sec)
        else:
            self.deadline = None

        self.closed_at: Optional[datetime] = None
        self.close_reason = ""

    def ttl_remaining_sec(self) -> Optional[int]:
        """Retorna segundos restantes, o None si hold."""
        if self.deadline is None:
            return None
        remaining = (self.deadline - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))

    def is_expired(self) -> bool:
        """True si deadline ha pasado."""
        if self.deadline is None:
            return False
        return datetime.now(timezone.utc) >= self.deadline

    def to_dict(self) -> Dict[str, Any]:
        """Serializa window a dict."""
        return {
            "window_id": self.window_id,
            "services": list(self.services),
            "mode": self.mode,
            "reason": self.reason,
            "state": self.state,
            "created_at": self.created_at.isoformat() + "Z",
            "deadline": self.deadline.isoformat() + "Z" if self.deadline else None,
            "closed_at": self.closed_at.isoformat() + "Z" if self.closed_at else None,
            "ttl_remaining_sec": self.ttl_remaining_sec(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Window":
        """Deserializa window desde dict."""
        created_at = (
            datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            if data.get("created_at")
            else None
        )
        window = cls(
            window_id=data["window_id"],
            services=set(data.get("services", [])),
            ttl_sec=None,  # Ya calculado, deadline está en data
            mode=data.get("mode", "ttl"),
            reason=data.get("reason", ""),
            created_at=created_at,
        )
        window.state = data.get("state", "open")
        if data.get("deadline"):
            window.deadline = datetime.fromisoformat(
                data["deadline"].replace("Z", "+00:00")
            )
        if data.get("closed_at"):
            window.closed_at = datetime.fromisoformat(
                data["closed_at"].replace("Z", "+00:00")
            )
        window.close_reason = data.get("close_reason", "")
        return window


class WindowManager:
    """Gestiona estado de ventanas (window_id, TTL, servicios activos)."""

    # Allowlist de servicios permitidos (sincronizado con docker-compose.yml)
    ALLOWLIST = {
        "tentaculo_link",
        "switch",
        "hermes",
        "hormiguero",
        "manifestator",
        "mcp",
        "shubniggurath",
        "spawner",
        "operator-backend",
        "operator-frontend",
    }

    SOLO_MADRE_SERVICES = {"madre", "redis"}

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or Path("docs/audit/madre_windows_state.json")
        self.active_window: Optional[Window] = None
        self.history: List[Dict[str, Any]] = []
        self._load_state()

    def _load_state(self) -> None:
        """Carga estado desde archivo JSON."""
        if not self.state_file.exists():
            log.info(f"No state file found at {self.state_file}, starting fresh")
            self.active_window = None
            self.history = []
            return

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                if data.get("active_window"):
                    self.active_window = Window.from_dict(data["active_window"])
                self.history = data.get("history", [])
            log.info(f"Loaded state from {self.state_file}")
        except Exception as e:
            log.error(f"Failed to load state: {e}")
            self.active_window = None
            self.history = []

    def _save_state(self) -> None:
        """Guarda estado a archivo JSON."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {
                "active_window": (
                    self.active_window.to_dict() if self.active_window else None
                ),
                "history": self.history,
                "last_update": datetime.now(timezone.utc).isoformat() + "Z",
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f, indent=2)
            log.debug(f"Saved state to {self.state_file}")
        except Exception as e:
            log.error(f"Failed to save state: {e}")

    def is_allowlist_valid(self, services: Set[str]) -> bool:
        """Valida que todos los servicios estén en allowlist."""
        invalid = services - self.ALLOWLIST
        if invalid:
            log.warning(f"Invalid services: {invalid}")
            return False
        return True

    def register_window(
        self, services: Set[str], ttl_sec: Optional[int], mode: str, reason: str
    ) -> Window:
        """
        Registra una nueva ventana.
        Raises: ValueError si hay ventana activa o servicios no válidos
        """
        if self.active_window and self.active_window.state == "open":
            raise ValueError(f"Window already active: {self.active_window.window_id}")

        if not self.is_allowlist_valid(services):
            raise ValueError(f"Services not in allowlist: {services}")

        window_id = str(uuid4())
        window = Window(
            window_id=window_id,
            services=services,
            ttl_sec=ttl_sec,
            mode=mode,
            reason=reason,
        )

        self.active_window = window
        self._save_state()
        log.info(
            f"Registered window {window_id}: {services}, mode={mode}, ttl={ttl_sec}s"
        )
        return window

    def close_window(self, reason: str = "manual") -> Optional[Window]:
        """Cierra ventana activa."""
        if not self.active_window:
            log.warning("No active window to close")
            return None

        window = self.active_window
        window.state = "closed"
        window.closed_at = datetime.now(timezone.utc)
        window.close_reason = reason

        # Agregar a history
        self.history.append(window.to_dict())

        self.active_window = None
        self._save_state()
        log.info(f"Closed window {window.window_id}: {reason}")
        return window

    def check_ttl_expiration(self) -> Optional[Window]:
        """
        Chequea si ventana activa expiró.
        Retorna window si expiró (ya cerrada), None si no o si no hay ventana.
        """
        if not self.active_window or self.active_window.state != "open":
            return None

        if not self.active_window.is_expired():
            return None

        log.warning(f"TTL expired for window {self.active_window.window_id}")
        return self.close_window(reason="ttl_expired")

    def get_window(self, window_id: str) -> Optional[Window]:
        """Obtiene ventana por ID (solo si activa)."""
        if self.active_window and self.active_window.window_id == window_id:
            return self.active_window
        return None

    def get_active_window(self) -> Optional[Window]:
        """Obtiene ventana activa."""
        return self.active_window

    def get_state(self) -> Dict[str, Any]:
        """Retorna estado actual para GET /madre/power/state."""
        if self.active_window:
            policy = "windowed"
            window_info = self.active_window.to_dict()
        else:
            policy = "solo_madre"
            window_info = None

        return {
            "policy": policy,
            "window_info": window_info,
            "solo_madre_services": list(self.SOLO_MADRE_SERVICES),
        }


# Singleton global
_window_manager: Optional[WindowManager] = None


def get_window_manager() -> WindowManager:
    """Obtiene instancia global de WindowManager."""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager()
    return _window_manager


def init_window_manager(state_file: Optional[Path] = None) -> WindowManager:
    """Inicializa el manager (llamado desde main.py)."""
    global _window_manager
    _window_manager = WindowManager(state_file=state_file)
    log.info("WindowManager initialized")
    return _window_manager
