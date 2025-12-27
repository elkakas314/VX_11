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
from config.forensics import write_log
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


def auth_check(
    authorization: Optional[str] = Header(None),
    x_vx11_token: Optional[str] = Header(None),
) -> Dict[str, Optional[str]]:
    """
    Validate auth based on VX11_AUTH_MODE policy.

    - off: returns empty dict (bypass)
    - token: validates x-vx11-token header
    - jwt: validates Bearer token (JWT)

    Raises HTTPException(401) if validation fails.
    """
    auth_mode = os.getenv("VX11_AUTH_MODE", "off")

    if auth_mode == "off":
        # DEV: bypass auth
        return {"user_id": "dev", "csrf": "dev"}

    if auth_mode == "token":
        # Token mode: validate x-vx11-token
        if not x_vx11_token:
            raise HTTPException(status_code=401, detail="auth_required")
        if x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=403, detail="forbidden")
        return {"user_id": "token_auth", "csrf": None}

    if auth_mode == "jwt":
        # JWT mode: validate Authorization Bearer
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
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

    # Unknown mode: deny
    raise HTTPException(status_code=500, detail=f"Unknown VX11_AUTH_MODE: {auth_mode}")


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


# ============ HEALTH ENDPOINT ============


@router.get("/health")
async def health():
    """
    Health check endpoint (no auth required, always 200).

    Returns basic module status for liveness/readiness probes.
    """
    return {
        "status": "ok",
        "module": "operator",
        "version": "7.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


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


@router.get("/api/map")
async def get_map(
    _: Dict = Depends(policy_check),
    __: Dict = Depends(auth_check),
):
    """
    Get system architecture map (canonical).

    Returns minimal graph: nodes (services) + edges (connections) + counts.
    Canonical structure from CANONICAL_FLOWS_VX11.json.

    NOTE: Uses policy_check only (not auth_check) to allow frontend MapTab
    to poll /api/map in DEV mode (VX11_AUTH_MODE=off).

    Response (200):
      {
        "nodes": [
          {"id": "madre", "label": "Madre (v7)", "state": "up", "port": 8001},
          ...
        ],
        "edges": [
          {"from": "operator_backend", "to": "tentaculo_link", "label": "proxy"},
          ...
        ],
        "counts": {
          "services_up": 4,
          "total_services": 4,
          "routing_events": 1234
        },
        "timestamp": "2025-12-27T10:45:00Z"
      }

    Errors:
      - 409: policy violation (low_power mode)
    """
    # Minimal canonical map
    nodes = [
        {"id": "madre", "label": "Madre (v7)", "state": "unknown", "port": 8001},
        {
            "id": "tentaculo_link",
            "label": "Tentáculo Link (v7)",
            "state": "unknown",
            "port": 8000,
        },
        {"id": "redis", "label": "Redis Cache", "state": "unknown", "port": 6379},
        {
            "id": "operator_backend",
            "label": "Operator Backend",
            "state": "up",
            "port": 8011,
        },
    ]

    # Canonical edges (connections)
    edges = [
        {"from": "operator_backend", "to": "tentaculo_link", "label": "proxy"},
        {"from": "tentaculo_link", "to": "madre", "label": "route"},
        {"from": "madre", "to": "redis", "label": "cache"},
    ]

    # Check each node state
    tentaculo_url = os.getenv("VX11_TENTACULO_URL", "http://tentaculo_link:8000")
    madre_url = os.getenv("VX11_MADRE_URL", "http://madre:8001")

    async with httpx.AsyncClient(timeout=1.5) as client:
        # Check tentaculo_link
        try:
            resp = await client.get(f"{tentaculo_url}/health")
            for node in nodes:
                if node["id"] == "tentaculo_link":
                    node["state"] = "up" if resp.status_code == 200 else "down"
        except:
            for node in nodes:
                if node["id"] == "tentaculo_link":
                    node["state"] = "down"

        # Check madre
        try:
            resp = await client.get(f"{madre_url}/health")
            for node in nodes:
                if node["id"] == "madre":
                    node["state"] = "up" if resp.status_code == 200 else "down"
        except:
            for node in nodes:
                if node["id"] == "madre":
                    node["state"] = "down"

    # Redis check (simple TCP ping via tentaculo)
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(f"{tentaculo_url}/vx11/status")
            if resp.status_code == 200:
                data = resp.json()
                redis_state = "up" if data.get("redis") == "ok" else "down"
            else:
                redis_state = "down"
    except:
        redis_state = "down"

    for node in nodes:
        if node["id"] == "redis":
            node["state"] = redis_state

    # Basic counts from DB (if available)
    counts = {
        "services_up": sum(1 for n in nodes if n.get("state") == "up"),
        "total_services": len(nodes),
    }

    # Try to get routing events count
    try:
        from config.db_schema import get_session, RoutingEvent
        from sqlalchemy import func

        with get_session() as db:
            count = db.query(func.count(RoutingEvent.id)).scalar() or 0
            counts["routing_events"] = count
    except:
        counts["routing_events"] = 0

    result = {
        "nodes": nodes,
        "edges": edges,
        "counts": counts,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return result


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
    ctx: Dict = Depends(request_context),
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
        "ok": true,
        "request_id": "...",
        "route_taken": "tentaculo_link|degraded",
        "degraded": bool,
        "errors": [...],
        "data": {
          "session_id": "uuid",
          "response": "respuesta del sistema",
          "tool_calls": null
        }
      }

    Errors:
      - 401: auth required
      - 409: policy violation (low_power mode)
      - 500: internal error (returns unified error envelope)
    """
    import uuid as uuid_lib

    request_id = ctx.get("request_id", str(uuid_lib.uuid4())[:12])
    route_taken = "operator_backend"  # default
    degraded = False
    errors = []

    try:
        session_id = request.get("session_id") or str(uuid_lib.uuid4())
        user_id = request.get("user_id") or "api_user"
        message = request.get("message", "")

        if not message:
            errors.append(
                ErrorInfo(step="input_validation", hint="message is required")
            )
            return UnifiedResponse(
                ok=False,
                request_id=request_id,
                route_taken=route_taken,
                degraded=False,
                errors=errors,
                data=None,
            )

        # HARDENING: Max message length 4KB
        if len(message) > 4096:
            errors.append(
                ErrorInfo(
                    step="input_validation",
                    hint=f"message too long (max 4KB, got {len(message)} bytes)",
                )
            )
            return UnifiedResponse(
                ok=False,
                request_id=request_id,
                route_taken=route_taken,
                degraded=False,
                errors=errors,
                data=None,
            )

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
        route_taken = "tentaculo_link"  # Attempt primary route

        if TESTING_MODE:
            response_text = f"[TESTING_MODE] Received: {message}"
            route_taken = "operator_backend"
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
                    route_taken = "tentaculo_link"
            except Exception as e:
                write_log(
                    "operator_api",
                    f"chat:{session_id}:tentaculo_failed:{str(e)}",
                    level="INFO",
                )
                errors.append(ErrorInfo(step="tentaculo_link", hint=str(e)))

        # Degraded mode: fallback to echo (but ALWAYS persist)
        if not response_text:
            response_text = (
                f"[DEGRADED] Received: {message}. Services not fully available."
            )
            route_taken = "degraded"
            degraded = True
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

        return UnifiedResponse(
            ok=True,
            request_id=request_id,
            route_taken=route_taken,
            degraded=degraded,
            errors=errors,
            data={
                "session_id": session_id,
                "response": response_text,
                "tool_calls": None,
            },
        )

    except Exception as exc:
        write_log("operator_api", f"chat_error:{exc}", level="ERROR")
        errors.append(ErrorInfo(step="handler", hint=str(exc)))
        return UnifiedResponse(
            ok=False,
            request_id=request_id,
            route_taken=route_taken,
            degraded=degraded,
            errors=errors,
            data=None,
        )


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
                    item.created_at.isoformat() + "Z"
                    if item.created_at is not None
                    else None
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
        "created_at": (
            item.created_at.isoformat() + "Z" if item.created_at is not None else None
        ),
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
    Server-Sent Events (SSE) infinite stream (Phase 2c enhanced - infinite reconnect).

    Emits system events from DB in real-time. Stream never closes (reconnectable).

    Query params (optional filters):
      - source: filter by event source (e.g., 'madre', 'shubniggurath')
      - event_type: filter by event type (e.g., 'startup', 'shutdown', 'error')
      - severity: filter by severity (info, warning, error, critical)

    Example curl:
      curl -N -H "Authorization: Bearer $TOKEN" http://localhost:8011/api/events
      curl -N -H "Authorization: Bearer $TOKEN" 'http://localhost:8011/api/events?source=madre&severity=error'

    Response (200 stream - INFINITE):
      data: {"id": 1, "type": "startup", "source": "madre", "severity": "info", "request_id": "req-123", "payload": {...}, "timestamp": "2024-12-22T19:44:00Z"}
      data: {"id": 2, "type": "error", "source": "shubniggurath", "severity": "error", "request_id": "req-123", "payload": {...}, "timestamp": "2024-12-22T19:45:00Z"}
      data: {"type": "heartbeat", "request_id": "req-123", "timestamp": "2024-12-22T19:46:00Z"}
      ... (stream continues indefinitely, client reconnects on disconnect)
    """

    async def event_generator():
        import asyncio
        import json
        from datetime import datetime

        # Generate request context for this SSE stream
        request_id = str(uuid.uuid4())[:12]
        last_event_id = 0
        heartbeat_interval = 30  # Send heartbeat every 30 seconds
        last_heartbeat = datetime.utcnow()

        while True:  # INFINITE LOOP - never closes
            try:
                # Check for new events since last_event_id (poll every 5s)
                query = db.query(SystemEvents).filter(SystemEvents.id > last_event_id)
                if source:
                    query = query.filter(SystemEvents.source == source)
                if event_type:
                    query = query.filter(SystemEvents.event_type == event_type)
                if severity:
                    query = query.filter(SystemEvents.severity == severity)

                new_events = query.order_by(SystemEvents.timestamp.asc()).all()

                # Emit new events
                for event in new_events:
                    event_data = {
                        "id": event.id,
                        "type": event.event_type,
                        "source": event.source,
                        "severity": event.severity,
                        "request_id": request_id,  # Track which client received this
                        "payload": event.payload,
                        "timestamp": (
                            event.timestamp.isoformat() + "Z"
                            if event.timestamp is not None
                            else None
                        ),
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    last_event_id = event.id
                    last_heartbeat = datetime.utcnow()  # Reset heartbeat timer
                    await asyncio.sleep(0.01)

                # Emit heartbeat if no events for heartbeat_interval seconds
                now = datetime.utcnow()
                if (now - last_heartbeat).total_seconds() >= heartbeat_interval:
                    heartbeat = {
                        "type": "heartbeat",
                        "request_id": request_id,
                        "timestamp": now.isoformat() + "Z",
                    }
                    yield f"data: {json.dumps(heartbeat)}\n\n"
                    last_heartbeat = now

                # Poll for new events every 5 seconds
                await asyncio.sleep(5)

            except Exception as e:
                # Log error but keep stream alive (client can reconnect)
                error_event = {
                    "type": "error",
                    "source": "api/events",
                    "severity": "error",
                    "request_id": request_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                await asyncio.sleep(5)  # Back off on error

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
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
                    item.created_at.isoformat() + "Z"
                    if item.created_at is not None
                    else None
                ),
                "updated_at": (
                    item.updated_at.isoformat() + "Z"
                    if item.updated_at is not None
                    else None
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
    # Cast status to str to satisfy type checkers that may expose SQLAlchemy Column types
    status_key = str(item.status) if item.status is not None else ""
    progress = progress_map.get(status_key, {"percent": 0, "message": "Unknown status"})

    return {
        "id": item.id,
        "job_id": item.job_id,
        "intent": item.intent,
        "status": item.status,
        "payload": item.payload,
        "result": item.result,
        "created_at": (
            item.created_at.isoformat() + "Z" if item.created_at is not None else None
        ),
        "updated_at": (
            item.updated_at.isoformat() + "Z" if item.updated_at is not None else None
        ),
        "progress": progress,
    }


# ============ METRICS ENDPOINTS ============


@router.get("/api/percentages")
async def get_percentages(
    _: Dict = Depends(policy_check),
    ctx: Dict = Depends(request_context),
):
    """
    Get current percentages metrics from docs/audit/PERCENTAGES.json.

    Returns: normalized metrics JSON or 404 if file not found.
    """
    import json as json_lib
    import os
    from pathlib import Path

    try:
        # Default path: docs/audit/PERCENTAGES.json
        percentages_path = Path(
            os.getenv("VX11_PERCENTAGES_PATH", "docs/audit/PERCENTAGES.json")
        )

        if not percentages_path.exists():
            return JSONResponse(
                status_code=404,
                content={"ok": False, "detail": "PERCENTAGES.json not found"},
            )

        with open(percentages_path, "r") as f:
            data = json_lib.load(f)

        write_log(
            "operator_backend",
            f"percentages:retrieved:{ctx.get('request_id', 'unknown')}",
        )

        return {
            "ok": True,
            "data": data,
            "timestamp": data.get("generated_at", ""),
        }

    except Exception as exc:
        write_log("operator_backend", f"percentages:error:{exc}", level="ERROR")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "detail": "Error reading PERCENTAGES"},
        )


@router.get("/api/scorecard")
async def get_scorecard(
    _: Dict = Depends(policy_check),
    ctx: Dict = Depends(request_context),
):
    """
    Get current scorecard metrics from docs/audit/SCORECARD.json.

    Returns: normalized scorecard JSON or 404 if file not found.
    """
    import json as json_lib
    import os
    from pathlib import Path

    try:
        # Default path: docs/audit/SCORECARD.json
        scorecard_path = Path(
            os.getenv("VX11_SCORECARD_PATH", "docs/audit/SCORECARD.json")
        )

        if not scorecard_path.exists():
            return JSONResponse(
                status_code=404,
                content={"ok": False, "detail": "SCORECARD.json not found"},
            )

        with open(scorecard_path, "r") as f:
            data = json_lib.load(f)

        write_log(
            "operator_backend",
            f"scorecard:retrieved:{ctx.get('request_id', 'unknown')}",
        )

        return {
            "ok": True,
            "data": data,
            "timestamp": data.get("generated_ts", ""),
        }

    except Exception as exc:
        write_log("operator_backend", f"scorecard:error:{exc}", level="ERROR")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "detail": "Error reading SCORECARD"},
        )


# ============ NEW ENDPOINTS (FASE 2 - SPEC ALIGN) ============


@router.get("/api/topology")
async def get_topology(
    _: Dict = Depends(policy_check),
    ctx: Dict = Depends(request_context),
):
    """
    Get VX11 system topology (canonical endpoint).

    Returns structured nodes, edges, and architecture metadata.
    This is the canonical topology endpoint; /api/map is an alias for backward compatibility.

    Returns: {ok, data: {nodes, edges, metadata}, timestamp}
    """
    import json as json_lib
    from pathlib import Path

    try:
        # Try to read from canonical topology file if it exists
        topology_path = Path(
            os.getenv("VX11_TOPOLOGY_PATH", "docs/canon/topology_snapshot.json")
        )

        if topology_path.exists():
            with open(topology_path, "r") as f:
                data = json_lib.load(f)
            write_log(
                "operator_backend",
                f"topology:retrieved_from_file:{ctx.get('request_id', 'unknown')}",
            )
            return {
                "ok": True,
                "data": data,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        # Fallback: return minimal canonical topology (from settings if available)
        fallback_topology = {
            "nodes": [
                {"id": "madre", "label": "Madre", "status": "healthy", "port": 8001},
                {
                    "id": "tentaculo_link",
                    "label": "Tentáculo Link",
                    "status": "healthy",
                    "port": 8000,
                },
                {"id": "redis", "label": "Redis", "status": "healthy", "port": 6379},
            ],
            "edges": [
                {"from": "tentaculo_link", "to": "madre", "label": "proxy"},
                {"from": "redis", "to": "madre", "label": "cache"},
            ],
            "metadata": {
                "policy": "SOLO_MADRE",
                "entrypoint": "tentaculo_link:8000",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        }

        write_log(
            "operator_backend",
            f"topology:retrieved_fallback:{ctx.get('request_id', 'unknown')}",
        )
        return {
            "ok": True,
            "data": fallback_topology,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as exc:
        write_log("operator_backend", f"topology:error:{exc}", level="ERROR")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "detail": "Error reading topology"},
        )


@router.get("/api/audit/runs")
async def list_audit_runs(
    _: Dict = Depends(auth_check),
    ctx: Dict = Depends(request_context),
    limit: int = 10,
    offset: int = 0,
):
    """
    List recent audit run outdirs from docs/audit/vx11_*.

    Returns: {ok, data: [{run_id, timestamp, reason, status}], total}
    """
    from pathlib import Path
    import json as json_lib
    from datetime import datetime

    try:
        audit_base = Path("docs/audit")
        if not audit_base.exists():
            return JSONResponse(
                status_code=404, content={"ok": False, "detail": "No audit directory"}
            )

        # Find all vx11_* directories
        runs = []
        for run_dir in sorted(audit_base.glob("vx11_*"), reverse=True):
            if not run_dir.is_dir():
                continue

            # Extract timestamp from dirname (e.g., vx11_prompt8_operatorjson_align_1766836243 -> 1766836243)
            parts = run_dir.name.split("_")
            ts = parts[-1] if parts else "unknown"

            # Try to read summary metadata
            summary_file = run_dir / "PHASE1_AUDIT_FINDINGS.md"
            reason = "audit run"
            status_val = "completed"

            if not summary_file.exists():
                summary_file = run_dir / "COMPLETION_REPORT.md"
            if not summary_file.exists():
                summary_file = run_dir / "FINAL_STATUS.md"

            runs.append(
                {
                    "run_id": run_dir.name,
                    "timestamp": ts,
                    "reason": reason,
                    "status": status_val,
                    "path": str(run_dir),
                }
            )

        # Apply pagination
        total = len(runs)
        paginated = runs[offset : offset + limit]

        write_log("operator_backend", f"audit_runs:listed:{len(paginated)} of {total}")
        return {
            "ok": True,
            "data": paginated,
            "total": total,
            "offset": offset,
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as exc:
        write_log("operator_backend", f"audit_runs:error:{exc}", level="ERROR")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "detail": f"Error listing audit runs: {str(exc)}"},
        )


@router.get("/api/audit/runs/{run_id}")
async def get_audit_run_detail(
    run_id: str,
    _: Dict = Depends(auth_check),
    ctx: Dict = Depends(request_context),
):
    """
    Read metadata and key files from a specific audit run outdir.

    Returns: {ok, data: {files, metadata}, timestamp}
    Whitelist: PHASE1_AUDIT_FINDINGS.md, COMPLETION_REPORT.md, FINAL_STATUS.md, git_log.txt, etc.
    """
    from pathlib import Path
    import json as json_lib

    try:
        # Validate run_id to prevent path traversal
        if ".." in run_id or "/" in run_id:
            return JSONResponse(
                status_code=400, content={"ok": False, "detail": "Invalid run_id"}
            )

        run_path = Path("docs/audit") / run_id
        if not run_path.exists() or not run_path.is_dir():
            return JSONResponse(
                status_code=404,
                content={"ok": False, "detail": f"Run {run_id} not found"},
            )

        # Whitelist of allowed files to read
        whitelist = {
            "PHASE1_AUDIT_FINDINGS.md",
            "COMPLETION_REPORT.md",
            "FINAL_STATUS.md",
            "git_log.txt",
            "docker_ps_solo_madre.txt",
            "npm_build_*.txt",
            "tests_p0_final.txt",
            "BACKEND_CONSOLIDATION.md",
            "FRONTEND_BUILD_FIX.md",
        }

        files_content = {}
        for fname in run_path.glob("*"):
            if fname.is_file() and (
                fname.name in whitelist or fname.name.startswith("npm_build_")
            ):
                try:
                    with open(fname, "r") as f:
                        content = f.read(5000)  # Limit to 5KB per file
                    files_content[fname.name] = content[
                        :1000
                    ]  # Truncate to 1KB in response
                except Exception:
                    pass

        write_log("operator_backend", f"audit_run_detail:retrieved:{run_id}")
        return {
            "ok": True,
            "data": {
                "run_id": run_id,
                "files": list(files_content.keys()),
                "file_previews": files_content,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as exc:
        write_log("operator_backend", f"audit_run_detail:error:{exc}", level="ERROR")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "detail": f"Error reading audit run: {str(exc)}"},
        )


@router.get("/api/settings")
async def get_settings(
    _: Dict = Depends(auth_check),
    ctx: Dict = Depends(request_context),
):
    """
    Read operator UI settings (theme, polling, filters, etc.).

    Returns: {ok, data: {theme, poll_interval, redaction_level, default_tab}, timestamp}
    """
    try:
        # Read from environment or config file
        settings_data = {
            "theme": os.getenv("VX11_OPERATOR_THEME", "dark"),
            "poll_interval": int(os.getenv("VX11_OPERATOR_POLL_INTERVAL", "5")),
            "redaction_level": os.getenv("VX11_OPERATOR_REDACTION", "medium"),
            "default_tab": os.getenv("VX11_OPERATOR_DEFAULT_TAB", "overview"),
            "telemetry_enabled": os.getenv("VX11_OPERATOR_TELEMETRY", "true").lower()
            == "true",
        }

        write_log(
            "operator_backend", f"settings:retrieved:{ctx.get('request_id', 'unknown')}"
        )
        return {
            "ok": True,
            "data": settings_data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as exc:
        write_log("operator_backend", f"settings:error:{exc}", level="ERROR")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "detail": "Error reading settings"},
        )


@router.post("/api/settings")
async def update_settings(
    settings_update: Dict[str, Any],
    _: Dict = Depends(auth_check),
    ctx: Dict = Depends(request_context),
):
    """
    Update operator UI settings (restricted schema).

    Allowed fields:
    - theme: "dark" | "light"
    - poll_interval: 1-60 seconds
    - redaction_level: "low" | "medium" | "high"
    - default_tab: "overview" | "topology" | "metrics" | "audit" | "settings"

    Returns: {ok, data: {updated_settings}, timestamp}
    """
    try:
        # Validate inputs (restricted schema)
        validated = {}

        if "theme" in settings_update:
            if settings_update["theme"] in ["dark", "light"]:
                validated["theme"] = settings_update["theme"]

        if "poll_interval" in settings_update:
            try:
                interval = int(settings_update["poll_interval"])
                if 1 <= interval <= 60:
                    validated["poll_interval"] = interval
            except (ValueError, TypeError):
                pass

        if "redaction_level" in settings_update:
            if settings_update["redaction_level"] in ["low", "medium", "high"]:
                validated["redaction_level"] = settings_update["redaction_level"]

        if "default_tab" in settings_update:
            if settings_update["default_tab"] in [
                "overview",
                "topology",
                "metrics",
                "audit",
                "settings",
            ]:
                validated["default_tab"] = settings_update["default_tab"]

        # For now, settings are ephemeral (not persisted to disk)
        # In production, these would be stored in database or config file

        write_log("operator_backend", f"settings:updated:{len(validated)} fields")
        return {
            "ok": True,
            "data": {
                "updated": validated,
                "note": "Settings updated for this session (ephemeral)",
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as exc:
        write_log("operator_backend", f"settings:error:{exc}", level="ERROR")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "detail": "Error updating settings"},
        )
