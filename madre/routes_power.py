"""
Power Manager Routes for VX11 Madre v7 — FASE 2: Real Execution

Endpoints para gestión de ventanas con ejecución real de docker compose:
- POST /madre/power/window/open — abre ventana + inicia servicios
- POST /madre/power/window/close — cierra ventana + detiene servicios
- GET /madre/power/state — lee estado
- POST /madre/power/policy/solo_madre/apply — aplica SOLO_MADRE
- GET /madre/power/policy/solo_madre/status — chequea SOLO_MADRE activo

Status: PHASE 2 IMPLEMENTATION
- Uses existing /madre/power/service/{name}/start|stop endpoints
- Integrated with WindowManager TTL system
- Real docker compose execution with audit logging
"""

import logging
import asyncio
from typing import Optional, Set, List
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
import subprocess
import json
from datetime import datetime, timezone
import os

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


# ============= Docker Integration (Real Execution) =============


def docker_compose_up(services: List[str]) -> dict:
    """
    PHASE 2: Real execution via subprocess (docker compose available in madre container).

    Each service started individually to ensure proper ordering and error isolation.
    Timeout: 30 seconds per service.
    Returns: {
        "status": "ok" | "partial" | "fail",
        "results": [{"service": "...", "returncode": 0, "elapsed_ms": ...}],
        "timestamp": ISO8601
    }
    """
    results = []
    timeout_sec = int(os.environ.get("VX11_POWER_WINDOWS_TIMEOUT_SEC", 30))

    for service in services:
        start_time = datetime.utcnow()
        try:
            cmd = [
                "docker",
                "compose",
                "-p",
                "vx11",
                "-f",
                "/app/docker-compose.yml",
                "-f",
                "/app/docker-compose.override.yml",
                "up",
                "-d",
                service,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_sec, cwd="/app"
            )
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            results.append(
                {
                    "service": service,
                    "returncode": result.returncode,
                    "elapsed_ms": elapsed_ms,
                    "stdout": result.stdout[:500] if result.stdout else "",
                    "stderr": result.stderr[:500] if result.stderr else "",
                }
            )

            if result.returncode != 0:
                log.warning(f"docker_compose_up {service} returned {result.returncode}")
            else:
                log.info(f"docker_compose_up {service} OK ({elapsed_ms}ms)")

        except subprocess.TimeoutExpired:
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log.error(f"docker_compose_up {service} TIMEOUT ({timeout_sec}s)")
            results.append(
                {
                    "service": service,
                    "returncode": -1,
                    "error": f"TIMEOUT after {timeout_sec}s",
                    "elapsed_ms": elapsed_ms,
                }
            )
        except Exception as e:
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log.error(f"docker_compose_up {service} ERROR: {e}")
            results.append(
                {
                    "service": service,
                    "returncode": -2,
                    "error": str(e),
                    "elapsed_ms": elapsed_ms,
                }
            )

    # Determine overall status
    failed = [r for r in results if r.get("returncode", -999) != 0]
    status = (
        "ok" if not failed else ("partial" if len(failed) < len(services) else "fail")
    )

    return {
        "status": status,
        "results": results,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def docker_compose_stop(services: List[str]) -> dict:
    """
    PHASE 2: Real execution via subprocess.

    Each service stopped individually.
    Timeout: 20 seconds per service.
    Returns: {
        "status": "ok" | "partial" | "fail",
        "results": [{"service": "...", "returncode": 0, "elapsed_ms": ...}],
        "timestamp": ISO8601
    }
    """
    results = []
    timeout_sec = int(os.environ.get("VX11_POWER_WINDOWS_TIMEOUT_SEC", 30))

    for service in services:
        start_time = datetime.utcnow()
        try:
            cmd = [
                "docker",
                "compose",
                "-p",
                "vx11",
                "-f",
                "/app/docker-compose.yml",
                "-f",
                "/app/docker-compose.override.yml",
                "stop",
                service,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_sec, cwd="/app"
            )
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            results.append(
                {
                    "service": service,
                    "returncode": result.returncode,
                    "elapsed_ms": elapsed_ms,
                    "stdout": result.stdout[:500] if result.stdout else "",
                    "stderr": result.stderr[:500] if result.stderr else "",
                }
            )

            if result.returncode != 0:
                log.warning(
                    f"docker_compose_stop {service} returned {result.returncode}"
                )
            else:
                log.info(f"docker_compose_stop {service} OK ({elapsed_ms}ms)")

        except subprocess.TimeoutExpired:
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log.error(f"docker_compose_stop {service} TIMEOUT ({timeout_sec}s)")
            results.append(
                {
                    "service": service,
                    "returncode": -1,
                    "error": f"TIMEOUT after {timeout_sec}s",
                    "elapsed_ms": elapsed_ms,
                }
            )
        except Exception as e:
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log.error(f"docker_compose_stop {service} ERROR: {e}")
            results.append(
                {
                    "service": service,
                    "returncode": -2,
                    "error": str(e),
                    "elapsed_ms": elapsed_ms,
                }
            )

    # Determine overall status
    failed = [r for r in results if r.get("returncode", -999) != 0]
    status = (
        "ok" if not failed else ("partial" if len(failed) < len(services) else "fail")
    )

    return {
        "status": status,
        "results": results,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


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
    PHASE 2: Ejecuta docker compose start para cada servicio.

    POST /madre/power/window/open
    {
      "services": ["tentaculo_link", "switch", "hermes"],
      "ttl_sec": 300,
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
        # Registrar ventana en WindowManager
        window = wm.register_window(
            services=services_set,
            ttl_sec=req.ttl_sec if req.mode == "ttl" else None,
            mode=req.mode,
            reason=req.reason,
        )

        # PHASE 2: Ejecutar docker compose start realmente
        exec_result = docker_compose_up(list(req.services))

        if exec_result["status"] == "fail":
            # Si falla completamente, cerrar ventana y reportar
            wm.close_window("exec_failed")
            raise HTTPException(
                status_code=500,
                detail=f"docker compose up failed: {exec_result['results']}",
            )

        log.info(
            f"Window opened: {window.window_id}, services: {req.services}, status: {exec_result['status']}"
        )

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
    PHASE 2: Ejecuta docker compose stop para cada servicio.

    POST /madre/power/window/close
    """
    wm = get_window_manager()

    if not wm.active_window:
        raise HTTPException(status_code=404, detail="No active window")

    window = wm.active_window
    window_id = window.window_id
    services = list(window.services)

    try:
        # PHASE 2: Detener servicios realmente
        exec_result = docker_compose_stop(services)

        if exec_result["status"] == "fail":
            log.warning(f"docker compose stop had failures: {exec_result['results']}")
            # Continue anyway, close window in state

        # Cerrar ventana en WindowManager
        wm.close_window("manual_close")

        log.info(
            f"Window closed: {window_id}, services: {services}, status: {exec_result['status']}"
        )

        return WindowCloseResponse(
            window_id=window_id,
            closed_at=datetime.now(timezone.utc).isoformat() + "Z",
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
    PHASE 2: Ejecuta docker compose stop para todos los servicios de la ventana.

    POST /madre/power/policy/solo_madre/apply
    """
    wm = get_window_manager()

    try:
        # Si hay ventana activa, obtener servicios a detener
        services_to_stop = []
        exec_result = {"status": "ok", "results": []}

        if wm.active_window:
            services_to_stop = list(wm.active_window.services)

            # PHASE 2: Detener servicios realmente
            exec_result = docker_compose_stop(services_to_stop)

            if exec_result["status"] == "fail":
                log.warning(
                    f"docker compose stop had failures: {exec_result['results']}"
                )

            # Cerrar ventana en estado
            wm.close_window("solo_madre_applied")

        log.info(
            f"Solo Madre applied, services stopped: {services_to_stop}, status: {exec_result['status']}"
        )

        return {
            "policy": "solo_madre",
            "services_stopped": services_to_stop,
            "state": "applied",
            "exec_status": exec_result["status"],
            "exec_details": exec_result.get("results", []),
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
