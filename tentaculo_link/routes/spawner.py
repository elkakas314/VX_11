"""
VX11 Operator Routes: Spawner
tentaculo_link/routes/spawner.py

Endpoints:
- GET /api/spawner/status
- GET /api/spawner/runs
- POST /api/spawner/submit
"""

from typing import Any, Dict, Optional
import os
import sqlite3

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from config.settings import settings
from config.tokens import get_token
from tentaculo_link.clients import get_clients
from tentaculo_link.db.events_metrics import get_db_path, log_event
from tentaculo_link.routes.window import get_madre_window_status

router = APIRouter(prefix="/api", tags=["spawner"])

VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


def check_auth(x_vx11_token: Optional[str] = Header(None)) -> bool:
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    if not x_vx11_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if x_vx11_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


def _events_enabled() -> bool:
    return os.environ.get("VX11_EVENTS_ENABLED", "false").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def _log_spawn_event(summary: str, payload: Dict[str, Any]) -> None:
    if not _events_enabled():
        return
    log_event(
        event_type="spawn",
        summary=summary,
        module="spawner",
        severity="info",
        payload=payload,
    )


def _normalize_window(status: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mode": status.get("mode", "solo_madre"),
        "ttl_seconds": status.get("ttl_seconds"),
        "window_id": status.get("window_id"),
        "services": status.get("services", ["madre", "redis"]),
        "degraded": status.get("degraded", False),
        "reason": status.get("reason"),
    }


def _summarize_log(value: Optional[str], limit: int = 160) -> str:
    if not value:
        return ""
    return value.strip().replace("\n", " ")[:limit]


def _fetch_spawn_runs(limit: int, offset: int) -> Dict[str, Any]:
    db_path = get_db_path()
    if not db_path.exists():
        return {"runs": [], "total": 0}
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM spawns")
    total = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT id, uuid, name, cmd, status, started_at, ended_at, exit_code,
               stdout, stderr, parent_task_id, created_at
        FROM spawns
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    rows = cursor.fetchall()
    conn.close()

    runs = []
    for row in rows:
        runs.append(
            {
                "id": row["id"],
                "uuid": row["uuid"],
                "name": row["name"],
                "cmd": row["cmd"],
                "status": row["status"],
                "started_at": row["started_at"],
                "ended_at": row["ended_at"],
                "exit_code": row["exit_code"],
                "parent_task_id": row["parent_task_id"],
                "created_at": row["created_at"],
                "stdout_preview": _summarize_log(row["stdout"]),
                "stderr_preview": _summarize_log(row["stderr"]),
            }
        )
    return {"runs": runs, "total": total}


def _fetch_spawn_summary() -> Dict[str, Any]:
    db_path = get_db_path()
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status, COUNT(*) as count FROM spawns GROUP BY status"
    )
    rows = cursor.fetchall()
    conn.close()
    return {row["status"] or "unknown": row["count"] for row in rows}


@router.get("/spawner/status")
async def spawner_status(auth: bool = Depends(check_auth)):
    window = _normalize_window(await get_madre_window_status())
    allowed = window.get("mode") == "window_active" and "spawner" in window.get(
        "services", []
    )
    payload: Dict[str, Any] = {
        "policy": window.get("mode"),
        "allowed": allowed,
        "window": window,
        "summary": {"runs_by_status": _fetch_spawn_summary()},
    }

    if not allowed:
        payload.update(
            {
                "status": "off_by_policy",
                "message": "Spawner disabled by solo_madre policy",
            }
        )
        return JSONResponse(status_code=200, content=payload)

    clients = get_clients()
    spawner_client = clients.get_client("spawner")
    if not spawner_client:
        payload.update({"status": "degraded", "message": "Spawner client unavailable"})
        return JSONResponse(status_code=503, content=payload)

    health = await spawner_client.get("/health")
    payload.update({"status": "ok", "health": health})
    return payload


@router.get("/spawner/runs")
async def spawner_runs(
    limit: int = 20,
    offset: int = 0,
    auth: bool = Depends(check_auth),
):
    window = _normalize_window(await get_madre_window_status())
    allowed = window.get("mode") == "window_active" and "spawner" in window.get(
        "services", []
    )
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    data = _fetch_spawn_runs(limit, offset)
    return {
        "status": "ok",
        "policy": window.get("mode"),
        "allowed": allowed,
        "window": window,
        "runs": data["runs"],
        "total": data["total"],
        "limit": limit,
        "offset": offset,
    }


@router.post("/spawner/submit")
async def spawner_submit(
    payload: Dict[str, Any],
    x_correlation_id: Optional[str] = Header(None),
    auth: bool = Depends(check_auth),
):
    correlation_id = x_correlation_id or ""
    window = _normalize_window(await get_madre_window_status())
    allowed = window.get("mode") == "window_active" and "spawner" in window.get(
        "services", []
    )

    if not allowed:
        _log_spawn_event(
            "spawn_blocked",
            {
                "correlation_id": correlation_id,
                "payload": payload,
                "policy": window.get("mode"),
            },
        )
        return JSONResponse(
            status_code=403,
            content={
                "status": "blocked_in_solo_madre",
                "message": "blocked in solo_madre",
                "policy": window.get("mode"),
                "window": window,
                "correlation_id": correlation_id,
            },
        )

    madre_payload = {
        "type": "spawn",
        "payload": payload,
        "correlation_id": correlation_id,
        "source": "operator",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "http://madre:8001/madre/intent",
            json=madre_payload,
            headers=AUTH_HEADERS,
        )

    if response.status_code >= 400:
        return JSONResponse(
            status_code=response.status_code,
            content={
                "status": "error",
                "message": response.text,
                "policy": window.get("mode"),
                "correlation_id": correlation_id,
            },
        )

    madre_result = response.json()
    requested_name = payload.get("task_name") or payload.get("name") or "operator_spawn"
    ttl_seconds = 1
    safe_cmd = "echo 'vx11 spawner ok'"

    spawn_payload = {
        "name": requested_name,
        "cmd": safe_cmd,
        "task_type": payload.get("task_type") or "operator_spawn",
        "description": payload.get("description") or "operator_spawn_intent",
        "ttl_seconds": ttl_seconds,
        "trace_id": correlation_id,
        "source": "operator",
        "metadata": {
            "intent_id": madre_result.get("intent_id"),
            "task_id": madre_result.get("task_id"),
            "policy": "observer_mode",
            "cmd_overridden": payload.get("cmd") not in (None, "", safe_cmd),
        },
    }

    clients = get_clients()
    spawner_client = clients.get_client("spawner")
    if not spawner_client:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "spawner_client_unavailable",
                "policy": window.get("mode"),
                "correlation_id": correlation_id,
            },
        )

    spawner_result = await spawner_client.post(
        "/spawn",
        payload=spawn_payload,
        timeout=10.0,
    )

    _log_spawn_event(
        "spawn_submit",
        {
            "correlation_id": correlation_id,
            "payload": spawn_payload,
            "madre_status": madre_result,
            "spawner_status": spawner_result,
        },
    )

    return {
        "status": "queued",
        "policy": window.get("mode"),
        "correlation_id": correlation_id,
        "intent": madre_result,
        "spawn": spawner_result,
        "note": "cmd overridden to safe echo; ttl forced to 1s",
    }
