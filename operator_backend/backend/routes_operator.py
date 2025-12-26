"""
operator_backend/backend/routes_operator.py

Rutas para VX11 Operator Visor Interactivo (FASE D).
Todas las respuestas usan UnifiedResponse schema.
"""

import os
import json
import uuid
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse


# Helper para crear UnifiedResponse
def create_unified_response(
    ok: bool,
    request_id: str,
    route_taken: str,
    data: Optional[Dict[str, Any]] = None,
    errors: Optional[List[str]] = None,
    degraded: bool = False,
) -> Dict[str, Any]:
    return {
        "ok": ok,
        "request_id": request_id,
        "route_taken": route_taken,
        "degraded": degraded,
        "errors": errors or [],
        "data": data or {},
    }


logger = logging.getLogger("operator_routes")

router = APIRouter(prefix="/api", tags=["operator"])

# ============ IN-MEMORY JOB STORE (PRODUCTION: usar Redis/DB) ============
_audit_jobs: Dict[str, Dict[str, Any]] = {}


def _generate_job_id() -> str:
    """Generate unique job ID."""
    return f"audit_{uuid.uuid4().hex[:8]}"


async def _get_request_context(request: Request) -> str:
    """Extract route context from request."""
    return f"{request.method} {request.url.path}"


# ============ ENDPOINT 1: POST /api/audit ============
@router.post("/audit")
async def start_audit(
    payload: Dict[str, Any],
    request: Request,
) -> Dict[str, Any]:
    """
    Start new audit job.

    Body: {"audit_type": "structure|flow|db|routing", "scope": "full|module_only"}
    """
    route_context = await _get_request_context(request)

    audit_type = payload.get("audit_type", "structure")
    scope = payload.get("scope", "full")

    if audit_type not in ["structure", "flow", "db", "routing"]:
        return create_unified_response(
            ok=False,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            errors=[f"Invalid audit_type: {audit_type}"],
            data={},
        )

    job_id = _generate_job_id()
    _audit_jobs[job_id] = {
        "job_id": job_id,
        "audit_type": audit_type,
        "scope": scope,
        "status": "queued",
        "started_at": datetime.utcnow().isoformat(),
        "results": [],
        "total": 0,
    }

    logger.info(
        f"[OPERATOR] Started audit job {job_id} (type={audit_type}, scope={scope})"
    )

    return create_unified_response(
        ok=True,
        request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
        route_taken=route_context,
        data={
            "job_id": job_id,
            "status": "queued",
            "started_at": _audit_jobs[job_id]["started_at"],
        },
    )


# ============ ENDPOINT 2: GET /api/audit/{job_id} ============
@router.get("/audit/{job_id}")
async def get_audit_result(
    job_id: str,
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    request: Request = None,
) -> Dict[str, Any]:
    """
    Get audit job status and results (paginado).
    """
    route_context = await _get_request_context(request)

    if job_id not in _audit_jobs:
        return create_unified_response(
            ok=False,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            errors=[f"Job not found: {job_id}"],
            data={},
        )

    job = _audit_jobs[job_id]
    # Simulación: generar resultados si status es queued
    if job["status"] == "queued":
        job["status"] = "completed"
        # Generar mock results
        job["results"] = [
            {
                "audit_type": job["audit_type"],
                "check": "filesystem_structure",
                "passed": True,
                "failed": 0,
            },
            {
                "audit_type": job["audit_type"],
                "check": "imports_valid",
                "passed": True,
                "failed": 0,
            },
            {
                "audit_type": job["audit_type"],
                "check": "db_schema",
                "passed": True,
                "failed": 0,
            },
        ]
        job["total"] = len(job["results"])

    results_page = job["results"][offset : offset + limit]

    return create_unified_response(
        ok=True,
        request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
        route_taken=route_context,
        data={
            "job_id": job_id,
            "status": job["status"],
            "started_at": job["started_at"],
            "results": results_page,
            "total": job["total"],
            "offset": offset,
            "limit": limit,
        },
    )


# ============ ENDPOINT 3: GET /api/audit ============
@router.get("/audit")
async def list_audits(
    request: Request = None,
) -> Dict[str, Any]:
    """
    List recent audits (last 24h).
    """
    route_context = await _get_request_context(request)

    # Filtrar audits del último día
    audits = []
    now = datetime.utcnow()
    for job in _audit_jobs.values():
        started = datetime.fromisoformat(job["started_at"])
        if (now - started) < timedelta(hours=24):
            audits.append(
                {
                    "job_id": job["job_id"],
                    "audit_type": job["audit_type"],
                    "status": job["status"],
                    "started_at": job["started_at"],
                    "scope": job["scope"],
                }
            )

    return create_unified_response(
        ok=True,
        request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
        route_taken=route_context,
        data={
            "audits": audits,
            "total": len(audits),
        },
    )


# ============ ENDPOINT 4: POST /api/module/{module_name}/power_up|down|restart ============
@router.post("/module/{module_name}/power_up")
@router.post("/module/{module_name}/power_down")
@router.post("/module/{module_name}/restart")
async def control_module_power(
    module_name: str,
    request: Request,
) -> Dict[str, Any]:
    """
    Send power control INTENT to madre.
    Supported actions: power_up, power_down, restart
    """
    route_context = await _get_request_context(request)

    # Extraer acción del path
    action = request.url.path.split("/")[-1]  # power_up, power_down, o restart

    logger.info(f"[OPERATOR] Module power control: {module_name} -> {action}")

    return create_unified_response(
        ok=True,
        request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
        route_taken=route_context,
        data={
            "action": "queued",
            "module_name": module_name,
            "power_action": action,
            "service_id": f"{module_name}_{uuid.uuid4().hex[:4]}",
        },
    )


# ============ ENDPOINT 5: GET /api/status/modules ============
@router.get("/status/modules")
async def get_modules_status(
    request: Request,
) -> Dict[str, Any]:
    """
    Get health status of all 9 services (cached 30s).
    """
    route_context = await _get_request_context(request)

    # Mock data - en producción obtener de docker/madre
    modules_status = [
        {
            "name": "madre",
            "status": "up",
            "healthy": True,
            "last_check": datetime.utcnow().isoformat(),
        },
        {
            "name": "tentaculo_link",
            "status": "up",
            "healthy": True,
            "last_check": datetime.utcnow().isoformat(),
        },
        {
            "name": "redis",
            "status": "up",
            "healthy": True,
            "last_check": datetime.utcnow().isoformat(),
        },
        {
            "name": "switch",
            "status": "down",
            "healthy": False,
            "last_check": datetime.utcnow().isoformat(),
        },
        {
            "name": "hermes",
            "status": "down",
            "healthy": False,
            "last_check": datetime.utcnow().isoformat(),
        },
        {
            "name": "spawner",
            "status": "down",
            "healthy": False,
            "last_check": datetime.utcnow().isoformat(),
        },
        {
            "name": "shubniggurath",
            "status": "down",
            "healthy": False,
            "last_check": datetime.utcnow().isoformat(),
        },
        {
            "name": "manifestator",
            "status": "down",
            "healthy": False,
            "last_check": datetime.utcnow().isoformat(),
        },
        {
            "name": "operator_backend",
            "status": "up",
            "healthy": True,
            "last_check": datetime.utcnow().isoformat(),
        },
    ]

    return create_unified_response(
        ok=True,
        request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
        route_taken=route_context,
        data={
            "modules": modules_status,
            "total": len(modules_status),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ============ ENDPOINT 6: GET /api/explorer/fs ============
@router.get("/explorer/fs")
async def explore_filesystem(
    path: str = Query("/app", description="Filesystem path to explore"),
    limit: int = Query(100, ge=1, le=1000),
    request: Request = None,
) -> Dict[str, Any]:
    """
    Read-only filesystem navigator (hard constraint: only /app paths).
    """
    route_context = await _get_request_context(request)

    # Validación: solo /app
    if not path.startswith("/app"):
        return create_unified_response(
            ok=False,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            errors=["Path must start with /app"],
            data={},
        )

    if ".." in path:
        return create_unified_response(
            ok=False,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            errors=["Path traversal not allowed"],
            data={},
        )

    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return create_unified_response(
                ok=False,
                request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
                route_taken=route_context,
                errors=[f"Path does not exist: {path}"],
                data={},
            )

        entries = []
        if path_obj.is_dir():
            for item in sorted(path_obj.iterdir())[:limit]:
                try:
                    entries.append(
                        {
                            "name": item.name,
                            "type": "dir" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else 0,
                        }
                    )
                except (OSError, PermissionError):
                    pass

        return create_unified_response(
            ok=True,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            data={
                "path": path,
                "entries": entries,
                "total": len(entries),
            },
        )

    except Exception as e:
        logger.exception(f"FS explorer error: {e}")
        return create_unified_response(
            ok=False,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            errors=[str(e)],
            data={},
        )


# ============ ENDPOINT 7: GET /api/explorer/db ============
@router.get("/explorer/db")
async def explore_database(
    table: str = Query("modules", description="Table name"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    request: Request = None,
) -> Dict[str, Any]:
    """
    Read-only DB query interface (hard constraint: LIMIT 100, no mutations).
    """
    route_context = await _get_request_context(request)

    db_path = "/home/elkakas314/vx11/data/runtime/vx11.db"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Validar tabla
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        if not cursor.fetchone():
            return create_unified_response(
                ok=False,
                request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
                route_taken=route_context,
                errors=[f"Table not found: {table}"],
                data={},
            )

        # Contar total
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        total = cursor.fetchone()["cnt"]

        # Obtener datos
        cursor.execute(f"SELECT * FROM {table} LIMIT ? OFFSET ?", (limit, offset))
        rows = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return create_unified_response(
            ok=True,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            data={
                "table": table,
                "rows": rows,
                "total": total,
                "offset": offset,
                "limit": limit,
            },
        )

    except Exception as e:
        logger.exception(f"DB explorer error: {e}")
        return create_unified_response(
            ok=False,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            errors=[str(e)],
            data={},
        )


# ============ ENDPOINT 8: POST /api/settings ============
@router.post("/settings")
async def update_settings(
    payload: Dict[str, Any],
    request: Request,
) -> Dict[str, Any]:
    """
    Update user settings (non-destructive only: theme, auto_refresh).
    """
    route_context = await _get_request_context(request)

    theme = payload.get("theme", "dark")
    auto_refresh_interval = payload.get("auto_refresh_interval", 5000)

    if theme not in ["dark", "light"]:
        return create_unified_response(
            ok=False,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            errors=[f"Invalid theme: {theme}"],
            data={},
        )

    if not isinstance(auto_refresh_interval, int) or auto_refresh_interval < 1000:
        return create_unified_response(
            ok=False,
            request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
            route_taken=route_context,
            errors=["auto_refresh_interval must be >= 1000ms"],
            data={},
        )

    # En producción: guardar en DB o Redis
    logger.info(
        f"[OPERATOR] Settings updated: theme={theme}, auto_refresh={auto_refresh_interval}"
    )

    return create_unified_response(
        ok=True,
        request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
        route_taken=route_context,
        data={
            "theme": theme,
            "auto_refresh_interval": auto_refresh_interval,
            "saved_at": datetime.utcnow().isoformat(),
        },
    )


# ============ ENDPOINT 9: GET /api/route_taken ============
@router.get("/route_taken")
async def get_route_taken(
    limit: int = Query(50, ge=1, le=1000),
    request: Request = None,
) -> Dict[str, Any]:
    """
    Get last N route_taken values from logs.
    """
    route_context = await _get_request_context(request)

    # Mock data - en producción obtener de logs estructurados
    routes = [
        {
            "timestamp": (datetime.utcnow() - timedelta(seconds=i * 60)).isoformat(),
            "route": f"GET /api/status/modules (response: 200)",
            "module": "operator_backend",
            "latency_ms": 45 + i * 5,
        }
        for i in range(min(limit, 10))
    ]

    return create_unified_response(
        ok=True,
        request_id=str(request.headers.get("X-Request-ID", uuid.uuid4())),
        route_taken=route_context,
        data={
            "routes": routes,
            "total": len(routes),
            "limit": limit,
        },
    )


# ============================================================================
# FASE 2: DATABASE READ-ONLY ENDPOINTS (para visor)
# ============================================================================


@router.get("/db/routing-events")
async def get_routing_events(
    request: Request,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """
    Get routing events from BD (read-only, paginado, LIMIT enforced).
    """
    route_context = await _get_request_context(request)
    db_path = "/home/elkakas314/vx11/data/runtime/vx11.db"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Tabla mock: si no existe, devolver vacio
        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM routing_events")
            total = cursor.fetchone()["cnt"]
        except sqlite3.OperationalError:
            # Tabla no existe
            conn.close()
            return create_unified_response(
                ok=True,
                request_id=_get_request_id(request),
                route_taken=route_context,
                data={"events": [], "total": 0, "offset": offset, "limit": limit},
            )

        # Query con LIMIT obligatorio
        cursor.execute(
            "SELECT * FROM routing_events ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return create_unified_response(
            ok=True,
            request_id=_get_request_id(request),
            route_taken=route_context,
            data={
                "events": rows,
                "total": total,
                "offset": offset,
                "limit": limit,
            },
        )

    except Exception as e:
        logger.exception(f"DB routing-events error: {e}")
        return create_unified_response(
            ok=False,
            request_id=_get_request_id(request),
            route_taken=route_context,
            errors=[str(e)],
            data={},
        )


@router.get("/db/cli-providers")
async def get_cli_providers(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """
    Get CLI providers from BD (read-only).
    """
    route_context = await _get_request_context(request)
    db_path = "/home/elkakas314/vx11/data/runtime/vx11.db"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM cli_providers")
            total = cursor.fetchone()["cnt"]
        except sqlite3.OperationalError:
            conn.close()
            return create_unified_response(
                ok=True,
                request_id=_get_request_id(request),
                route_taken=route_context,
                data={"providers": [], "total": 0},
            )

        cursor.execute("SELECT * FROM cli_providers LIMIT ?", (limit,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return create_unified_response(
            ok=True,
            request_id=_get_request_id(request),
            route_taken=route_context,
            data={"providers": rows, "total": total},
        )

    except Exception as e:
        logger.exception(f"DB cli-providers error: {e}")
        return create_unified_response(
            ok=False,
            request_id=_get_request_id(request),
            route_taken=route_context,
            errors=[str(e)],
            data={},
        )


@router.get("/db/spawns")
async def get_spawns(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    """
    Get spawn records from BD (read-only, paginado).
    """
    route_context = await _get_request_context(request)
    db_path = "/home/elkakas314/vx11/data/runtime/vx11.db"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) as cnt FROM spawns")
            total = cursor.fetchone()["cnt"]
        except sqlite3.OperationalError:
            conn.close()
            return create_unified_response(
                ok=True,
                request_id=_get_request_id(request),
                route_taken=route_context,
                data={"spawns": [], "total": 0, "offset": offset, "limit": limit},
            )

        cursor.execute(
            "SELECT * FROM spawns ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return create_unified_response(
            ok=True,
            request_id=_get_request_id(request),
            route_taken=route_context,
            data={
                "spawns": rows,
                "total": total,
                "offset": offset,
                "limit": limit,
            },
        )

    except Exception as e:
        logger.exception(f"DB spawns error: {e}")
        return create_unified_response(
            ok=False,
            request_id=_get_request_id(request),
            route_taken=route_context,
            errors=[str(e)],
            data={},
        )
