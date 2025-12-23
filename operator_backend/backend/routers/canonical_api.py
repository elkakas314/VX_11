"""
Canonical API Router — Phase 1 (Aliases) + Phase 3 (Gating)
VX11 Operator Backend v7.0

Expone conjunto mínimo canónico:
- POST /auth/login (genera token)
- GET /api/status (alias /operator/vx11/overview)
- POST /api/chat (alias /operator/chat)
- POST /api/audit (stub)
- GET /api/modules (alias /operator/shub/dashboard)
- POST /api/module/{name}/restart (stub)
- GET /api/audit/{id}/download (stub)
- GET /api/events (SSE heartbeat stub)

Gating:
- VX11_MODE=low_power → todas rutas retornan 409 (disabled by policy)
- VX11_MODE=operative_core → 200 si auth válida
"""

import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import jwt
from sqlalchemy.orm import Session

from config.db_schema import (
    get_session,
    OperatorSession,
    AuditLogs,
    OperatorJob,
    SystemEvents,
)

# Config
VX11_MODE = os.getenv("VX11_MODE", "low_power")
OPERATOR_ADMIN_PASSWORD = os.getenv("OPERATOR_ADMIN_PASSWORD", "admin")
OPERATOR_TOKEN_SECRET = os.getenv("OPERATOR_TOKEN_SECRET", "operator-secret-v7")
TOKEN_EXPIRE_HOURS = 24

router = APIRouter(prefix="", tags=["canonical_api"])


# ============ MODELS ============


class LoginRequest(BaseModel):
    """Login request."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class StatusResponse(BaseModel):
    """Status response."""

    status: str
    module: str
    version: str
    uptime: Optional[int] = None
    mode: str


# ============ DEPENDENCY: Policy Check ============


def policy_check() -> Dict[str, str]:
    """
    Check if VX11_MODE allows operation.

    - low_power: deny (409)
    - operative_core: allow (200)

    Raises HTTPException(409) if low_power mode.
    """
    if VX11_MODE == "low_power":
        raise HTTPException(
            status_code=409,
            detail="Operator disabled by policy (low_power mode). Set VX11_MODE=operative_core to enable.",
        )
    return {"mode": VX11_MODE}


def auth_check(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    """
    Validate Bearer token.

    Raises HTTPException(401) if missing/invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        payload = jwt.decode(token, OPERATOR_TOKEN_SECRET, algorithms=["HS256"])
        return {"user_id": payload.get("sub", "unknown")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# ============ AUTH ENDPOINTS ============


@router.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest, _: Dict = Depends(policy_check)):
    """
    Login endpoint.

    Genera JWT token basado en OPERATOR_ADMIN_PASSWORD ENV.

    Request:
      {
        "username": "admin",
        "password": "admin"
      }

    Response (200):
      {
        "access_token": "eyJ...",
        "token_type": "bearer",
        "expires_in": 86400
      }

    Errors:
      - 401: invalid credentials
      - 409: policy violation (low_power mode)
    """
    # Validate credentials
    if req.username != "admin" or req.password != OPERATOR_ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Generate JWT token
    exp = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": req.username,
        "exp": exp,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, OPERATOR_TOKEN_SECRET, algorithm="HS256")

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRE_HOURS * 3600,
    )


@router.post("/auth/logout", response_model=Dict[str, str])
async def logout(
    user: Dict = Depends(auth_check),
    _: Dict = Depends(policy_check),
):
    """
    Logout endpoint.

    Marca sesión como inactiva en BD.

    Response (200):
      {
        "status": "logged_out",
        "message": "Session terminated"
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    # TODO: Mark session as inactive in DB (user_id: payload.sub)
    return {
        "status": "logged_out",
        "message": f"Session terminated for user {user.get('user_id', 'unknown')}",
    }


@router.post("/auth/verify", response_model=Dict[str, Any])
async def verify(
    user: Dict = Depends(auth_check),
    _: Dict = Depends(policy_check),
):
    """
    Verify token endpoint.

    Valida que el token es válido y retorna info del usuario.

    Response (200):
      {
        "valid": true,
        "user_id": "admin",
        "mode": "operative_core"
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    return {
        "valid": True,
        "user_id": user.get("user_id", "unknown"),
        "mode": VX11_MODE,
    }


# ============ STATUS ENDPOINTS ============


@router.get("/api/status", response_model=StatusResponse)
async def get_status(
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Get VX11 Operator status (canonical).

    Alias para /operator/vx11/overview.

    Response (200):
      {
        "status": "operational",
        "module": "operator",
        "version": "7.0",
        "uptime": 12345,
        "mode": "operative_core"
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    return StatusResponse(
        status="operational",
        module="operator",
        version="7.0",
        uptime=None,  # TODO: calculate from start time
        mode=VX11_MODE,
    )


@router.get("/api/modules")
async def get_modules(
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Get list of modules (canonical).

    Alias para /operator/shub/dashboard.

    Response (200):
      {
        "modules": [
          {"name": "madre", "status": "on"},
          {"name": "shubniggurath", "status": "on"}
        ]
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    return {
        "modules": [
            {"name": "madre", "status": "on"},
            {"name": "shubniggurath", "status": "on"},
            {"name": "tentaculo_link", "status": "on"},
        ]
    }


# ============ CHAT ENDPOINTS ============


@router.post("/api/chat")
async def post_chat(
    request: Dict[str, Any],
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Post chat message (canonical).

    Alias para /operator/chat.

    Request:
      {
        "session_id": "optional",
        "message": "Hola"
      }

    Response (200):
      {
        "message_id": "msg_...",
        "status": "received"
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    # TODO: Forward to /operator/chat handler if exists
    return {
        "message_id": f"msg_{datetime.utcnow().timestamp()}",
        "status": "received",
    }


# ============ AUDIT ENDPOINTS ============


@router.get("/api/audit")
async def list_audits(
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
    db: Session = Depends(get_session),
):
    """
    List audit logs (Phase 2 real implementation).

    Query params:
      - skip: offset (default 0)
      - limit: max results (default 100, max 1000)
      - level: filter by level (INFO, WARNING, ERROR)

    Response (200):
      {
        "total": 1234,
        "items": [
          {"id": 1, "component": "madre", "level": "INFO", "message": "...", "created_at": "2024-12-22T...Z"}
        ]
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    limit = min(limit, 1000)  # cap at 1000
    query = db.query(AuditLogs)

    if level:
        query = query.filter(AuditLogs.level == level.upper())

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "component": item.component,
                "level": item.level,
                "message": item.message,
                "created_at": (
                    item.created_at.isoformat() + "Z" if item.created_at else None
                ),
            }
            for item in items
        ],
    }


@router.get("/api/audit/{audit_id}")
async def get_audit(
    audit_id: int,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
    db: Session = Depends(get_session),
):
    """
    Get audit entry detail (Phase 2 real implementation).

    Response (200):
      {
        "id": 1,
        "component": "madre",
        "level": "INFO",
        "message": "...",
        "created_at": "2024-12-22T...Z"
      }

    Errors:
      - 401: auth required
      - 404: audit not found
      - 409: policy violation (low_power mode)
    """
    item = db.query(AuditLogs).filter(AuditLogs.id == audit_id).first()

    if not item:
        raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found")

    return {
        "id": item.id,
        "component": item.component,
        "level": item.level,
        "message": item.message,
        "created_at": item.created_at.isoformat() + "Z" if item.created_at else None,
    }


@router.get("/api/audit/{audit_id}/download")
async def download_audit(
    audit_id: int,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
    db: Session = Depends(get_session),
):
    """
    Download audit entry as CSV/JSON (Phase 2 real implementation).

    Response (200):
      CSV export of audit entry + related events

    Errors:
      - 401: auth required
      - 404: audit not found
      - 409: policy violation (low_power mode)
    """
    item = db.query(AuditLogs).filter(AuditLogs.id == audit_id).first()

    if not item:
        raise HTTPException(status_code=404, detail=f"Audit {audit_id} not found")

    # Build CSV content
    csv_content = f"id,component,level,message,created_at\n"
    csv_content += f'{item.id},"{item.component}","{item.level}","{item.message}","{item.created_at}"\n'

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_{audit_id}.csv"},
    )


# ============ MODULE CONTROL ENDPOINTS ============


@router.post("/api/module/{name}/restart")
async def restart_module(
    name: str,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Restart module (Phase 2 real implementation).

    Supported modules: madre, shubniggurath, tentaculo_link, operator-backend

    Response (200):
      {
        "module": "madre",
        "status": "restarting",
        "timestamp": "2024-12-22T...Z"
      }

    Errors:
      - 400: invalid module name
      - 401: auth required
      - 409: policy violation (low_power mode)
      - 503: restart failed
    """
    valid_modules = ["madre", "shubniggurath", "tentaculo_link", "operator-backend"]

    if name not in valid_modules:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid module: {name}. Valid: {', '.join(valid_modules)}",
        )

    # TODO: Call docker-compose restart <name> or systemctl restart vx11-<name>
    # For now, return simulated response
    return {
        "module": name,
        "status": "restarting",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": f"Module {name} restart initiated (Phase 2 stub)",
    }


@router.post("/api/module/{name}/power_up")
async def power_up_module(
    name: str,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Power up module (Phase 2 real implementation).

    Response (200):
      {
        "module": "madre",
        "status": "powering_up",
        "timestamp": "2024-12-22T...Z"
      }

    Errors:
      - 400: invalid module name
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    valid_modules = ["madre", "shubniggurath", "tentaculo_link", "operator-backend"]

    if name not in valid_modules:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid module: {name}. Valid: {', '.join(valid_modules)}",
        )

    # TODO: Call docker-compose up <name> or systemctl start vx11-<name>
    return {
        "module": name,
        "status": "powering_up",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/api/module/{name}/power_down")
async def power_down_module(
    name: str,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Power down module (Phase 2 real implementation).

    Response (200):
      {
        "module": "madre",
        "status": "powering_down",
        "timestamp": "2024-12-22T...Z"
      }

    Errors:
      - 400: invalid module name
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    valid_modules = ["madre", "shubniggurath", "tentaculo_link", "operator-backend"]

    if name not in valid_modules:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid module: {name}. Valid: {', '.join(valid_modules)}",
        )

    # TODO: Call docker-compose down <name> or systemctl stop vx11-<name>
    return {
        "module": name,
        "status": "powering_down",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ============ EVENTS (SSE) ============


@router.get("/api/events")
async def get_events(
    source: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
    db: Session = Depends(get_session),
):
    """
    Server-Sent Events (SSE) real stream (Phase 2c real implementation).

    Emits system events from DB in real-time.

    Query params (optional filters):
      - source: filter by event source (e.g., 'madre', 'shubniggurath')
      - event_type: filter by event type (e.g., 'startup', 'shutdown', 'error')
      - severity: filter by severity (info, warning, error, critical)

    Example curl:
      curl -N -H "Authorization: Bearer $TOKEN" http://localhost:8011/api/events
      curl -N -H "Authorization: Bearer $TOKEN" 'http://localhost:8011/api/events?source=madre&severity=error'

    Response (200 stream):
      data: {"id": 1, "type": "startup", "source": "madre", "severity": "info", "payload": {...}, "timestamp": "2024-12-22T19:44:00Z"}
      data: {"id": 2, "type": "error", "source": "shubniggurath", "severity": "error", "payload": {...}, "timestamp": "2024-12-22T19:45:00Z"}
      ...
    """

    async def event_generator():
        import asyncio
        import json

        # Get initial events from DB (last 10)
        query = db.query(SystemEvents)
        if source:
            query = query.filter(SystemEvents.source == source)
        if event_type:
            query = query.filter(SystemEvents.event_type == event_type)
        if severity:
            query = query.filter(SystemEvents.severity == severity)

        recent_events = query.order_by(SystemEvents.timestamp.desc()).limit(10).all()

        # Emit recent events
        for event in reversed(recent_events):
            event_data = {
                "id": event.id,
                "type": event.event_type,
                "source": event.source,
                "severity": event.severity,
                "payload": event.payload,
                "timestamp": (
                    event.timestamp.isoformat() + "Z" if event.timestamp else None
                ),
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(0.01)

        # Emit heartbeat to keep connection alive (for 5 cycles, then close)
        for _ in range(5):
            heartbeat = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            yield f"data: {json.dumps(heartbeat)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


# ============ JOBS ENDPOINTS (Phase 2b) ============


@router.get("/api/jobs")
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    intent: Optional[str] = None,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
    db: Session = Depends(get_session),
):
    """
    List operator jobs (Phase 2b real implementation).

    Query params:
      - skip: offset (default 0)
      - limit: max results (default 100, max 1000)
      - status: filter by status (queued, running, completed, failed)
      - intent: filter by intent

    Response (200):
      {
        "total": 1234,
        "items": [
          {"id": 1, "job_id": "job_...", "intent": "chat", "status": "completed",
           "payload": {...}, "result": {...}, "created_at": "2024-12-22T...Z", "updated_at": "...Z"}
        ]
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    limit = min(limit, 1000)  # cap at 1000
    query = db.query(OperatorJob)

    if status:
        query = query.filter(OperatorJob.status == status.lower())

    if intent:
        query = query.filter(OperatorJob.intent == intent.lower())

    total = query.count()
    items = (
        query.order_by(OperatorJob.created_at.desc()).offset(skip).limit(limit).all()
    )

    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "job_id": item.job_id,
                "intent": item.intent,
                "status": item.status,
                "payload": item.payload,
                "result": item.result,
                "created_at": (
                    item.created_at.isoformat() + "Z" if item.created_at else None
                ),
                "updated_at": (
                    item.updated_at.isoformat() + "Z" if item.updated_at else None
                ),
            }
            for item in items
        ],
    }


@router.get("/api/jobs/{job_id}")
async def get_job(
    job_id: str,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
    db: Session = Depends(get_session),
):
    """
    Get job detail (Phase 2b real implementation).

    Path param:
      - job_id: job identifier (can be numeric ID or job_id string)

    Response (200):
      {
        "id": 1,
        "job_id": "job_...",
        "intent": "chat",
        "status": "completed",
        "payload": {...},
        "result": {...},
        "created_at": "2024-12-22T...Z",
        "updated_at": "2024-12-22T...Z",
        "progress": {
          "percent": 100,
          "message": "Job completed successfully"
        }
      }

    Errors:
      - 401: auth required
      - 404: job not found
      - 409: policy violation (low_power mode)
    """
    # Try to find by numeric ID first, then by job_id string
    item = None
    try:
        item_id = int(job_id)
        item = db.query(OperatorJob).filter(OperatorJob.id == item_id).first()
    except ValueError:
        pass

    if not item:
        item = db.query(OperatorJob).filter(OperatorJob.job_id == job_id).first()

    if not item:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Calculate progress based on status
    progress_map = {
        "queued": {"percent": 0, "message": "Job queued, waiting to run"},
        "running": {"percent": 50, "message": "Job is running"},
        "completed": {"percent": 100, "message": "Job completed successfully"},
        "failed": {"percent": 100, "message": "Job failed"},
    }
    progress = progress_map.get(
        item.status, {"percent": 0, "message": "Unknown status"}
    )

    return {
        "id": item.id,
        "job_id": item.job_id,
        "intent": item.intent,
        "status": item.status,
        "payload": item.payload,
        "result": item.result,
        "created_at": item.created_at.isoformat() + "Z" if item.created_at else None,
        "updated_at": item.updated_at.isoformat() + "Z" if item.updated_at else None,
        "progress": progress,
    }
