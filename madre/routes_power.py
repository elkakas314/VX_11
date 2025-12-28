"""
Power Manager Routes for VX11 Madre v7

Endpoints para gestión de ventanas:
- POST /madre/power/window/open — abre ventana
- POST /madre/power/window/close — cierra ventana
- GET /madre/power/state — lee estado
- POST /madre/power/policy/solo_madre/apply — aplica SOLO_MADRE
- GET /madre/power/policy/solo_madre/status — chequea SOLO_MADRE activo
"""

import logging
import asyncio
from typing import Optional, Set, List
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
import subprocess
import json
from datetime import datetime

from .power_windows import get_window_manager, Window

log = logging.getLogger("vx11.madre.routes_power")


# Token validation dependency
class TokenGuard:
    """Valida X-VX11-Token header."""

    def __init__(self, expected_token: Optional[str] = None):
        # Por defecto usa variable de entorno
        import os

        self.expected_token = (
            expected_token
            or os.environ.get("VX11_TENTACULO_LINK_TOKEN")
            or os.environ.get("VX11_TOKEN")
            or "vx11-token-production"
        )

    def __call__(self, x_vx11_token: str = Header(None)) -> bool:
        if not x_vx11_token:
            raise HTTPException(
                status_code=401, detail="auth_required: X-VX11-Token header missing"
            )
        if x_vx11_token != self.expected_token:
            raise HTTPException(status_code=403, detail="forbidden: invalid token")
        return True


token_guard = TokenGuard()
router = APIRouter()


# ============= Request/Response Models =============


class WindowOpenRequest(BaseModel):
    services: List[str]
    ttl_sec: Optional[int] = None
    mode: str = "ttl"  # "ttl" o "hold"
    reason: str = "manual"


class WindowOpenResponse(BaseModel):
    window_id: str
    created_at: str
    deadline: Optional[str]
    services_started: List[str]
    state: str
    ttl_remaining_sec: Optional[int]


class WindowCloseResponse(BaseModel):
    window_id: str
    closed_at: str
    services_stopped: List[str]
    state: str


class PowerStateResponse(BaseModel):
    policy: str  # "solo_madre" o "windowed"
    window_id: Optional[str]
    created_at: Optional[str]
    deadline: Optional[str]
    ttl_remaining_sec: Optional[int]
    active_services: List[str]


class SoloMadreStatusResponse(BaseModel):
    policy_active: bool
    running_services: List[str]
    expected_services: List[str]


# ============= Docker Integration (mínimo) =============


def docker_compose_up(services: List[str]) -> bool:
    """
    DEPRECATED: Docker execution delegated to tentaculo_link (host-level executor).
    This function is a stub. Actual execution happens via tentaculo POST /power/window/open.
    """
    log.warning(
        f"docker_compose_up called (deprecated): {services}. "
        "Execution delegated to tentaculo_link. Window registration complete."
    )
    return True


def docker_compose_stop(services: List[str]) -> bool:
    """
    DEPRECATED: Docker execution delegated to tentaculo_link (host-level executor).
    This function is a stub. Actual execution happens via tentaculo POST /power/window/close.
    """
    log.warning(
        f"docker_compose_stop called (deprecated): {services}. "
        "Execution delegated to tentaculo_link. Window closure recorded."
    )
    return True


def get_docker_ps() -> List[dict]:
    """Retorna estado de servicios (docker compose ps)."""
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        log.error(f"get_docker_ps error: {e}")
    return []


def await_health_check(
    services: List[str], timeout_sec: int = 10, attempt_retries: int = 3
) -> bool:
    """
    Espera a que servicios estén healthy (simulado: chequea si contendores están running).
    En producción, esto invocaría /health de cada servicio.
    """
    import time

    deadline = time.time() + timeout_sec

    while time.time() < deadline:
        try:
            ps = get_docker_ps()
            running = {
                item.get("Service")
                for item in ps
                if "running" in item.get("State", "").lower()
            }
            if all(svc in running for svc in services):
                log.info(f"All services healthy: {services}")
                return True
        except Exception as e:
            log.debug(f"Health check error: {e}")

        time.sleep(1)

    log.error(f"Health check timeout for {services}")
    return False


# ============= Endpoints =============


@router.post("/window/open", response_model=WindowOpenResponse)
async def window_open(
    req: WindowOpenRequest, authorized: bool = Depends(token_guard)
) -> WindowOpenResponse:
    """
    Abre una ventana temporal (TTL) o indefinida (hold).

    POST /madre/power/window/open
    {
      "services": ["tentaculo_link", "switch", "hermes"],
      "ttl_sec": 30,
      "mode": "ttl",
      "reason": "e2e_test"
    }
    """
    wm = get_window_manager()

    # Validar allowlist
    services_set = set(req.services)
    if not wm.is_allowlist_valid(services_set):
        invalid = services_set - wm.ALLOWLIST
        log.warning(f"Allowlist violation: {invalid}")
        raise HTTPException(
            status_code=422, detail=f"Services not in allowlist: {invalid}"
        )

    # Validar que no hay ventana activa
    if wm.active_window and wm.active_window.state == "open":
        raise HTTPException(
            status_code=409,
            detail=f"Window already active: {wm.active_window.window_id}. Close it first.",
        )

    try:
        # Registrar ventana (metadata only, execution delegated to tentaculo)
        window = wm.register_window(
            services=services_set,
            ttl_sec=req.ttl_sec if req.mode == "ttl" else None,
            mode=req.mode,
            reason=req.reason,
        )

        # In Phase 1, skip docker execution (metadata-only mode)
        # In Phase 2, this will trigger actual docker compose commands

        # Retornar estado
        return WindowOpenResponse(
            window_id=window.window_id,
            created_at=window.created_at.isoformat() + "Z",
            deadline=window.deadline.isoformat() + "Z" if window.deadline else None,
            services_started=req.services,
            state="open",
            ttl_remaining_sec=window.ttl_remaining_sec(),
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"window_open error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/window/close", response_model=WindowCloseResponse)
async def window_close(authorized: bool = Depends(token_guard)) -> WindowCloseResponse:
    """
    Cierra ventana activa (manual).

    POST /madre/power/window/close
    """
    wm = get_window_manager()

    if not wm.active_window:
        raise HTTPException(status_code=404, detail="No active window")

    window = wm.active_window
    window_id = window.window_id
    services = list(window.services)

    try:
        # Detener servicios
        docker_compose_stop(services)

        # Cerrar ventana
        wm.close_window("manual_close")

        return WindowCloseResponse(
            window_id=window_id,
            closed_at=datetime.utcnow().isoformat() + "Z",
            services_stopped=services,
            state="closed",
        )

    except Exception as e:
        log.error(f"window_close error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/state", response_model=PowerStateResponse)
async def get_power_state(
    authorized: bool = Depends(token_guard),
) -> PowerStateResponse:
    """
    Lee estado actual (policy, ventana activa, TTL restante).

    GET /madre/power/state
    """
    wm = get_window_manager()
    window = wm.active_window

    if window:
        active_services = list(window.services) + list(wm.SOLO_MADRE_SERVICES)
    else:
        active_services = list(wm.SOLO_MADRE_SERVICES)

    return PowerStateResponse(
        policy="windowed" if window else "solo_madre",
        window_id=window.window_id if window else None,
        created_at=window.created_at.isoformat() + "Z" if window else None,
        deadline=(
            window.deadline.isoformat() + "Z" if window and window.deadline else None
        ),
        ttl_remaining_sec=window.ttl_remaining_sec() if window else None,
        active_services=active_services,
    )


@router.post("/policy/solo_madre/apply")
async def apply_solo_madre(authorized: bool = Depends(token_guard)) -> dict:
    """
    Aplica policy SOLO_MADRE (cierra ventana + detiene todo excepto madre+redis).

    POST /madre/power/policy/solo_madre/apply
    """
    wm = get_window_manager()

    try:
        # Si hay ventana activa, obtener servicios a detener
        services_to_stop = []
        if wm.active_window:
            services_to_stop = list(wm.active_window.services)
            wm.close_window("solo_madre_applied")

        # Detener servicios (si los hay)
        if services_to_stop:
            docker_compose_stop(services_to_stop)

        return {
            "policy": "solo_madre",
            "services_stopped": services_to_stop,
            "state": "applied",
        }

    except Exception as e:
        log.error(f"apply_solo_madre error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/policy/solo_madre/status", response_model=SoloMadreStatusResponse)
async def check_solo_madre_status(
    authorized: bool = Depends(token_guard),
) -> SoloMadreStatusResponse:
    """
    Chequea si policy SOLO_MADRE está activo.

    GET /madre/power/policy/solo_madre/status
    """
    wm = get_window_manager()
    ps = get_docker_ps()

    # collect service names that are running, filter out None and coerce to str
    running_services_list = [
        str(item.get("Service"))
        for item in ps
        if "running" in (item.get("State") or "").lower()
        and item.get("Service") is not None
    ]
    # compare as sets to ignore ordering and ensure type-compatibility
    policy_active = set(running_services_list) == set(wm.SOLO_MADRE_SERVICES)

    return SoloMadreStatusResponse(
        policy_active=policy_active,
        running_services=running_services_list,
        expected_services=list(wm.SOLO_MADRE_SERVICES),
    )
