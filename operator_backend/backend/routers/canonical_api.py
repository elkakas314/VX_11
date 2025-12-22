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
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import jwt

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


@router.post("/api/audit")
async def post_audit(
    request: Dict[str, Any],
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Create audit entry (stub).

    Response (501):
      {
        "error": "not implemented yet",
        "detail": "Audit endpoint is a stub"
      }
    """
    return JSONResponse(
        status_code=501,
        content={
            "error": "not_implemented",
            "detail": "Audit POST is a stub (Phase 2)",
        },
    )


@router.get("/api/audit/{audit_id}/download")
async def download_audit(
    audit_id: str,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Download audit entry (stub).

    Response (501):
      {
        "error": "not implemented yet",
        "detail": "Audit download is a stub"
      }
    """
    return JSONResponse(
        status_code=501,
        content={
            "error": "not_implemented",
            "detail": f"Audit download for {audit_id} is a stub (Phase 2)",
        },
    )


# ============ MODULE CONTROL ENDPOINTS ============


@router.post("/api/module/{name}/restart")
async def restart_module(
    name: str,
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Restart module (stub).

    Response (501):
      {
        "error": "not implemented yet",
        "detail": "Module control is a stub"
      }
    """
    return JSONResponse(
        status_code=501,
        content={
            "error": "not_implemented",
            "detail": f"Module restart for {name} is a stub (Phase 2)",
        },
    )


# ============ EVENTS (SSE) ============


@router.get("/api/events")
async def get_events(
    _: Dict = Depends(policy_check),
    user: Dict = Depends(auth_check),
):
    """
    Server-Sent Events (SSE) heartbeat (stub).

    Emits heartbeat event every 30s.

    Example curl:
      curl -N -H "Authorization: Bearer $TOKEN" http://localhost:8011/api/events

    Response (200):
      data: {"type": "heartbeat", "timestamp": "2024-12-22T19:44:00Z"}
      ...
    """

    async def event_generator():
        while True:
            import asyncio

            event = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            yield f"data: {event}\n\n"
            await asyncio.sleep(30)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
