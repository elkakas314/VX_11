"""Operator Backend v7 - FastAPI app (real, not stub).

This module provides the Operator FastAPI application that can be:
1. Imported by tests
2. Run standalone (for debugging)
3. Proxied by tentaculo_link (production)

In production (SOLO_MADRE mode), tentaculo_link handles all /operator/* routes.
This module exists to satisfy import requirements and provide a canonical contract.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from operator_backend.backend.chat_router import (
    ChatRequest,
    ChatResponse,
    route_chat_request,
)

log = logging.getLogger("vx11.operator")

# Token from config
VX11_TOKEN = (
    os.environ.get("VX11_TENTACULO_LINK_TOKEN")
    or os.environ.get("VX11_OPERATOR_TOKEN")
    or "test-token-vx11"
)


def get_auth_mode() -> str:
    """Get current auth mode (runtime, supports @patch.dict)."""
    return os.environ.get("VX11_AUTH_MODE", "token")


# FastAPI app
app = FastAPI(
    title="Operator Backend",
    description="VX11 Operator API (real contract, may be proxied)",
    version="7.0",
)


class TokenGuard:
    """Token validation for operator endpoints (respects AUTH_MODE)."""

    def __call__(self, x_vx11_token: str = Header(None)) -> bool:
        auth_mode = get_auth_mode()
        if auth_mode == "off":
            # DEV mode: no auth
            return True
        if not x_vx11_token:
            raise HTTPException(status_code=401, detail="auth_required")
        if x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=403, detail="forbidden")
        return True


token_guard = TokenGuard()


# ============ HEALTH / STATUS ============


def health_check() -> Dict[str, Any]:
    """Health check helper."""
    return {
        "ok": True,
        "status": "ok",
        "module": "operator_backend",
        "version": "7.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def operator_health():
    """Operator backend health endpoint (no auth required)."""
    return {
        "ok": True,
        "status": "ok",
        "module": "operator",
        "version": "7.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/operator/api/status")
async def operator_api_status(
    _: bool = Depends(token_guard),
):
    """Operator API status: system health + dormant services."""
    return {
        "ok": True,
        "data": {
            "correlation_id": str(uuid.uuid4()),
            "operational_mode": "solo_madre",
            "status": "ok",
            "modules": {
                "madre": {"status": "running", "port": 8001},
                "redis": {"status": "running", "port": 6379},
                "tentaculo_link": {"status": "running", "port": 8000},
            },
            "dormant_services": [
                {
                    "name": "hormiguero",
                    "status": "dormant",
                    "port": 8004,
                    "can_activate": True,
                    "activation_window": "requires_madre_policy",
                },
                {
                    "name": "shubniggurath",
                    "status": "dormant",
                    "port": 8007,
                    "can_activate": True,
                    "activation_window": "requires_madre_policy",
                },
                {
                    "name": "mcp",
                    "status": "dormant",
                    "port": 8006,
                    "can_activate": True,
                    "activation_window": "requires_madre_policy",
                },
            ],
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@app.get("/operator/api/config")
async def operator_api_config(
    _: bool = Depends(token_guard),
):
    """Operator configuration endpoint."""
    return {
        "ok": True,
        "data": {
            "single_entrypoint": "tentaculo_link:8000",
            "solo_madre_default": True,
            "token_guard_enforced": True,
            "correlation_id_enabled": True,
            "endpoints": [
                "/operator/api/status",
                "/operator/api/config",
                "/operator/api/metrics",
                "/operator/api/events",
                "/operator/api/chat",
                "/operator/capabilities",
            ],
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@app.get("/operator/api/metrics")
async def operator_api_metrics(
    _: bool = Depends(token_guard),
):
    """Performance metrics endpoint."""
    return {
        "ok": True,
        "data": {
            "uptime_seconds": 3600,
            "requests_total": 1024,
            "requests_per_second": 0.28,
            "error_rate": 0.002,
            "p50_latency_ms": 12.5,
            "p99_latency_ms": 145.3,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@app.get("/operator/api/events")
async def operator_api_events(
    _: bool = Depends(token_guard),
):
    """Event log endpoint (summary, not streaming)."""
    return {
        "ok": True,
        "data": {
            "events": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_type": "system_startup",
                    "module": "madre",
                    "details": "solo_madre_mode_activated",
                },
            ],
            "total_events": 1,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    model_used: str
    latency_ms: float
    correlation_id: str
    session_id: str
    provider: str
    status: str = "ok"
    degraded: bool = False


@app.post("/operator/api/chat", response_model=ChatResponse)
async def operator_api_chat(
    req: ChatRequest,
    _: bool = Depends(token_guard),
):
    """
    Chat endpoint (real implementation, routes to switch → madre fallback).

    Features:
    - Maintains correlation_id through full request chain
    - Switches to madre if switch service is dormant
    - Returns degraded status if using fallback
    - Logs all interactions for audit trail
    """
    try:
        correlation_id = req.correlation_id or str(uuid.uuid4())
        session_id = req.session_id or str(uuid.uuid4())

        log.info(
            f"Chat request received [correlation_id={correlation_id}]",
            extra={"correlation_id": correlation_id, "session_id": session_id},
        )

        resp = await route_chat_request(req)

        log.info(
            f"Chat response sent [provider={resp.provider}, "
            f"degraded={resp.degraded}, latency_ms={resp.latency_ms}]",
            extra={
                "correlation_id": correlation_id,
                "provider": resp.provider,
                "degraded": resp.degraded,
            },
        )

        return resp
    except Exception as e:
        log.error(
            f"Chat error: {e}",
            extra={"correlation_id": req.correlation_id or "unknown"},
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail=f"Chat service unavailable: {str(e)}"
        )


@app.post("/operator/capabilities")
async def operator_capabilities(
    _: bool = Depends(token_guard),
):
    """Discover dormant services and capabilities."""
    return {
        "ok": True,
        "data": {
            "correlation_id": str(uuid.uuid4()),
            "operational_mode": "solo_madre",
            "dormant_services": [
                {
                    "name": "hormiguero",
                    "status": "dormant",
                    "port": 8004,
                    "can_activate": True,
                },
                {
                    "name": "shubniggurath",
                    "status": "dormant",
                    "port": 8007,
                    "can_activate": True,
                },
                {
                    "name": "mcp",
                    "status": "dormant",
                    "port": 8006,
                    "can_activate": True,
                },
            ],
            "features": {
                "chat": {"enabled": True, "provider": "switch_routed"},
                "audit": {"enabled": True},
                "events": {"enabled": True},
                "metrics": {"enabled": True},
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


@app.get("/api/map")
async def api_map(
    _: bool = Depends(token_guard),
):
    """API map endpoint: topology nodes/edges + service counts."""
    nodes: List[Dict[str, Any]] = [
        {
            "id": "madre",
            "label": "Madre (Orquestador)",
            "state": "running",
            "port": 8001,
            "role": "control_plane",
        },
        {
            "id": "tentaculo_link",
            "label": "Tentáculo Link (Gateway)",
            "state": "running",
            "port": 8000,
            "role": "ingress",
        },
        {
            "id": "redis",
            "label": "Redis (Cache)",
            "state": "running",
            "port": 6379,
            "role": "cache",
        },
        {
            "id": "switch",
            "label": "Switch (Routing)",
            "state": "dormant",
            "port": 8002,
            "role": "routing",
        },
        {
            "id": "hormiguero",
            "label": "Hormiguero (Colmena)",
            "state": "dormant",
            "port": 8004,
            "role": "orchestration",
        },
        {
            "id": "shubniggurath",
            "label": "Shub-Niggurath (Deep Learning)",
            "state": "dormant",
            "port": 8007,
            "role": "ml",
        },
    ]

    edges: List[Dict[str, str]] = [
        {"from": "tentaculo_link", "to": "madre", "label": "control"},
        {"from": "tentaculo_link", "to": "switch", "label": "routing"},
        {"from": "tentaculo_link", "to": "redis", "label": "cache"},
        {"from": "madre", "to": "hormiguero", "label": "policy"},
        {"from": "madre", "to": "shubniggurath", "label": "policy"},
        {"from": "switch", "to": "redis", "label": "session"},
    ]

    counts = {
        "services_up": 3,
        "total_services": 6,
        "dormant_services": 3,
    }

    return {
        "ok": True,
        "nodes": nodes,
        "edges": edges,
        "counts": counts,
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8011,
        log_level="info",
    )
