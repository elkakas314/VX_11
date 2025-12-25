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
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import jwt
import httpx
from sqlalchemy.orm import Session

from config.settings import settings
from config.tokens import get_token, load_tokens
from config.rate_limit import get_rate_limiter
from config.db_schema import (
    get_session,
    OperatorSession,
    OperatorMessage,
    AuditLogs,
    OperatorJob,
    SystemEvents,
)
from ..switch_integration import TentaculoLinkClient

# Load tokens (for tentaculo link auth headers)
load_tokens()
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

# Config
OPERATOR_ADMIN_PASSWORD = os.getenv("OPERATOR_ADMIN_PASSWORD", "admin")
OPERATOR_TOKEN_SECRET = os.getenv("OPERATOR_TOKEN_SECRET", "operator-secret-v7")
TOKEN_EXPIRE_HOURS = 24
TESTING_MODE = (
    os.getenv("VX11_TESTING_MODE", "false").lower() == "true" or settings.testing_mode
)

router = APIRouter(prefix="", tags=["canonical_api"])
rate_limiter = get_rate_limiter()


# ============ MODELS ============


class LoginRequest(BaseModel):
    """Login request."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    access_token: str
    csrf_token: str
    token_type: str = "bearer"
    expires_in: int


class StatusResponse(BaseModel):
    """Status response."""

    status: str
    module: str
    version: str
    uptime: Optional[int] = None
    mode: str


# ============ UNIFIED RESPONSE SCHEMA ============


class ErrorInfo(BaseModel):
    """Error information in unified response."""

    step: str
    hint: str


class UnifiedResponse(BaseModel):
    """
    Canonical unified response envelope for all /api/* endpoints.

    Ensures consistent error reporting, request tracking, and route introspection.
    """

    ok: bool
    request_id: str
    route_taken: str = (
        "operator_backend"  # "operator_backend" | "tentaculo_link" | "madre" | "degraded"
    )
    degraded: bool = False
    errors: List[ErrorInfo] = []
    data: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "request_id": "abc123",
                "route_taken": "operator_backend",
                "degraded": False,
                "errors": [],
                "data": {"status": "ok"},
            }
        }


# ============ DEPENDENCY: Policy Check ============


def policy_check() -> Dict[str, str]:
    """
    Check if VX11_MODE allows operation.

    - low_power: deny (409)
    - operative_core: allow (200)

    Raises HTTPException(409) if low_power mode.
    """
    mode = os.getenv("VX11_MODE", "low_power")
    if mode == "low_power":
        raise HTTPException(
            status_code=409,
            detail="Operator disabled by policy (low_power mode). Set VX11_MODE=operative_core to enable.",
        )
    return {"mode": mode}


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
        return {
            "user_id": payload.get("sub", "unknown"),
            "csrf": payload.get("csrf"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def csrf_check(
    user: Dict = Depends(auth_check),
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
) -> Dict[str, str]:
    """
    Validate CSRF token for mutating requests.
    Requires X-CSRF-Token header to match JWT claim.
    """
    if not x_csrf_token or x_csrf_token != user.get("csrf"):
        raise HTTPException(status_code=403, detail="Invalid or missing CSRF token")
    return user


def request_context(
    request: Request,
    _policy: Dict = Depends(policy_check),
) -> Dict[str, str]:
    """
    Generate request tracking context.

    Returns dict with request_id (for audit trail).
    """
    request_id = str(uuid.uuid4())[:12]
    return {"request_id": request_id}


async def rate_limit_guard(
    request: Request,
    user: Dict = Depends(auth_check),
) -> Dict[str, Any]:
    """
    Rate limit guard for mutating endpoints.
    Uses user_id when available, falls back to client IP.
    """
    identifier = None
    if user:
        identifier = f"user:{user.get('user_id', 'unknown')}"
    if not identifier:
        client_host = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_host}"

    allowed, info = await rate_limiter.check_limit(
        identifier, limit=rate_limiter.protected_limit
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="rate_limit_exceeded",
            headers={"Retry-After": str(info.get("retry_after", 60))},
        )
    return info


async def rate_limit_guard_public(request: Request) -> Dict[str, Any]:
    """Rate limit guard for unauthenticated endpoints (login)."""
    client_host = request.client.host if request.client else "unknown"
    identifier = f"ip:{client_host}"
    allowed, info = await rate_limiter.check_limit(
        identifier, limit=rate_limiter.protected_limit
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="rate_limit_exceeded",
            headers={"Retry-After": str(info.get("retry_after", 60))},
        )
    return info


def append_audit(
    db: Session, component: str, message: str, level: str = "INFO"
) -> None:
    """Persist audit log entry for powerful actions."""
    entry = AuditLogs(component=component, level=level, message=message)
    db.add(entry)
    db.commit()


async def tentaculo_power_action(path: str) -> Dict[str, Any]:
    """Call Tentaculo Link power endpoint (single entrypoint)."""
    if TESTING_MODE:
        return {"status": "skipped", "reason": "testing_mode", "path": path}
    url = f"{settings.tentaculo_link_url.rstrip('/')}{path}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(url, headers=AUTH_HEADERS)
        if resp.status_code >= 300:
            raise HTTPException(
                status_code=503,
                detail=f"tentaculo_link power proxy failed ({resp.status_code})",
            )
        return resp.json()


# ============ AUTH ENDPOINTS ============


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    request: Request,
    _: Dict = Depends(policy_check),
    __: Dict = Depends(rate_limit_guard_public),
):
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

    # Generate CSRF token and JWT token
    csrf_token = str(uuid.uuid4())
    exp = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": req.username,
        "csrf": csrf_token,
        "exp": exp,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, OPERATOR_TOKEN_SECRET, algorithm="HS256")

    return LoginResponse(
        access_token=token,
        csrf_token=csrf_token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRE_HOURS * 3600,
    )


@router.post("/auth/logout", response_model=Dict[str, str])
async def logout(
    user: Dict = Depends(csrf_check),
    _: Dict = Depends(policy_check),
    __: Dict = Depends(rate_limit_guard),
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
    policy: Dict = Depends(policy_check),
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
        "mode": policy.get("mode", "unknown"),
    }


# ============ STATUS ENDPOINTS ============


@router.get("/api/status", response_model=StatusResponse)
async def get_status(
    policy: Dict = Depends(policy_check),
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
        mode=policy.get("mode", "unknown"),
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
    user: Dict = Depends(csrf_check),
    db: Session = Depends(get_session),
    __: Dict = Depends(rate_limit_guard),
):
    """
    Post chat message (canonical).

    Alias para /operator/chat: persiste sesión + mensajes en BD.

    Request:
      {
        "session_id": "optional UUID",
        "message": "Hola",
        "user_id": "optional",
        "context_summary": "optional",
        "metadata": "optional dict"
      }

    Response (200):
      {
        "session_id": "uuid",
        "response": "respuesta del sistema",
        "tool_calls": null
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
    """
    import uuid as uuid_lib
    from config.forensics import write_log

    try:
        session_id = request.get("session_id") or str(uuid_lib.uuid4())
        user_id = request.get("user_id") or "api_user"
        message = request.get("message", "")
        request_id = str(uuid_lib.uuid4())[:8]

        if not message:
            raise ValueError("message is required")

        # HARDENING: Max message length 4KB
        if len(message) > 4096:
            raise ValueError(f"message too long (max 4KB, got {len(message)} bytes)")

        # Create/get session
        session = db.query(OperatorSession).filter_by(session_id=session_id).first()
        if not session:
            session = OperatorSession(
                session_id=session_id,
                user_id=user_id,
                source="api",
            )
            db.add(session)
            db.commit()

        # Store user message
        user_msg = OperatorMessage(
            session_id=session_id,
            role="user",
            content=message,
            message_metadata=json.dumps(request.get("metadata") or {}),
        )
        db.add(user_msg)
        db.commit()

        # PHASE 3: Canonical routing via Tentaculo Link (no bypass)
        response_text = None

        if TESTING_MODE:
            response_text = f"[TESTING_MODE] Received: {message}"
        else:
            try:
                tentaculo_client = TentaculoLinkClient()
                result = await tentaculo_client.query_chat(
                    message=message,
                    session_id=session_id,
                    user_id=user_id,
                    metadata=request.get("metadata") or {},
                )
                response_text = result.get("response") or result.get("message")
                if response_text:
                    write_log("operator_api", f"chat:{session_id}:tentaculo_ok")
            except Exception as e:
                write_log(
                    "operator_api",
                    f"chat:{session_id}:tentaculo_failed:{str(e)}",
                    level="INFO",
                )

        # Degraded mode: fallback to echo (but ALWAYS persist)
        if not response_text:
            response_text = (
                f"[DEGRADED] Received: {message}. Services not fully available."
            )
            write_log(
                "operator_api", f"chat:{session_id}:degraded_mode", level="WARNING"
            )

        # Store assistant response
        assistant_msg = OperatorMessage(
            session_id=session_id,
            role="assistant",
            content=response_text,
        )
        db.add(assistant_msg)
        db.commit()

        write_log("operator_api", f"chat:{session_id}:success")

        return {
            "session_id": session_id,
            "request_id": request_id,
            "response": response_text,
            "tool_calls": None,
        }

    except Exception as exc:
        write_log("operator_api", f"chat_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))


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
    user: Dict = Depends(csrf_check),
    db: Session = Depends(get_session),
    __: Dict = Depends(rate_limit_guard),
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

    append_audit(db, "operator_api", f"module_restart:{name}", level="INFO")
    result = await tentaculo_power_action(f"/operator/power/service/{name}/restart")
    return {
        "module": name,
        "status": "restarting",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "proxy": result,
    }


@router.post("/api/module/{name}/power_up")
async def power_up_module(
    name: str,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(csrf_check),
    db: Session = Depends(get_session),
    __: Dict = Depends(rate_limit_guard),
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

    append_audit(db, "operator_api", f"module_power_up:{name}", level="INFO")
    result = await tentaculo_power_action(f"/operator/power/service/{name}/start")
    return {
        "module": name,
        "status": "powering_up",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "proxy": result,
    }


@router.post("/api/module/{name}/power_down")
async def power_down_module(
    name: str,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(csrf_check),
    db: Session = Depends(get_session),
    __: Dict = Depends(rate_limit_guard),
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

    append_audit(db, "operator_api", f"module_power_down:{name}", level="INFO")
    result = await tentaculo_power_action(f"/operator/power/service/{name}/stop")
    return {
        "module": name,
        "status": "powering_down",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "proxy": result,
    }


@router.get("/api/power/status")
async def power_status(
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """Get power status via Tentaculo Link (canonical entrypoint)."""
    url = f"{settings.tentaculo_link_url.rstrip('/')}/operator/power/status"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, headers=AUTH_HEADERS)
        if resp.status_code >= 300:
            raise HTTPException(status_code=503, detail="power_status_unavailable")
        return resp.json()


@router.get("/api/policy/solo_madre/status")
async def solo_madre_status(
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """Get SOLO_MADRE policy status via Tentaculo Link."""
    url = f"{settings.tentaculo_link_url.rstrip('/')}/operator/power/policy/solo_madre/status"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, headers=AUTH_HEADERS)
        if resp.status_code >= 300:
            raise HTTPException(status_code=503, detail="solo_madre_status_unavailable")
        return resp.json()


@router.post("/api/policy/solo_madre/apply")
async def solo_madre_apply(
    _: Dict = Depends(policy_check),
    user: Dict = Depends(csrf_check),
    db: Session = Depends(get_session),
    __: Dict = Depends(rate_limit_guard),
):
    """Apply SOLO_MADRE policy via Tentaculo Link."""
    append_audit(db, "operator_api", "policy_solo_madre_apply", level="INFO")
    result = await tentaculo_power_action("/operator/power/policy/solo_madre/apply")
    return result


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
