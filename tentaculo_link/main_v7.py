"""
Tentáculo Link v7.0 - Gateway Refactored

Pure proxy + auth + context-7 middleware + modular clients.
Version: 7.0 | Module: tentaculo_link | Port: 8000

Main HTTP gateway for VX11 with token authentication, circuit breaker,
Context-7 sessions, and intelligent request routing to internal services.
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set, Union

from contextlib import asynccontextmanager
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    JSONResponse,
    StreamingResponse,
    Response,
    FileResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import httpx

from config.forensics import write_log
from config.settings import settings
from config.tokens import get_token, load_tokens
from config.cache import get_cache, cache_startup, cache_shutdown
from config.cache_config import get_ttl, cache_decorator
from config.rate_limit import get_rate_limiter, set_redis_for_limiter
from config.metrics_prometheus import get_prometheus_metrics
from tentaculo_link.clients import get_clients
from tentaculo_link.context7_middleware import get_context7_manager

# Load environment tokens
load_tokens()
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


def _resolve_files_dir() -> Path:
    """Find writable directory for uploads."""
    candidates = [
        Path(settings.DATA_PATH) / "tentaculo_link" / "files",
        Path("/tmp/tentaculo_link/files"),
    ]
    for path in candidates:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except PermissionError:
            continue
    return candidates[-1]


FILES_DIR = _resolve_files_dir()


class TokenGuard:
    """Token validation dependency."""

    def __call__(self, x_vx11_token: str = Header(None)) -> bool:
        if settings.enable_auth:
            if not x_vx11_token:
                raise HTTPException(status_code=401, detail="auth_required")
            if x_vx11_token != VX11_TOKEN:
                raise HTTPException(status_code=403, detail="forbidden")
        return True


token_guard = TokenGuard()


class OperatorChatRequest(BaseModel):
    """Chat message with session context."""

    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "local"
    metadata: Optional[Dict[str, Any]] = None


class OperatorChatResponse(BaseModel):
    """Chat response."""

    session_id: str
    response: str
    metadata: Optional[Dict[str, Any]] = None


class OperatorTaskRequest(BaseModel):
    """TASK/ANALYSIS request routed via Switch."""

    task_type: str
    payload: Dict[str, Any]
    intent_type: Optional[str] = "task"
    session_id: Optional[str] = None
    user_id: Optional[str] = "local"
    metadata: Optional[Dict[str, Any]] = None
    provider_hint: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    clients = get_clients()
    context7 = get_context7_manager()
    cache = get_cache()
    limiter = get_rate_limiter()
    metrics = get_prometheus_metrics()

    await clients.startup()
    await cache_startup()  # Initialize Redis cache

    # Link Redis to rate limiter
    if cache.redis:
        set_redis_for_limiter(cache.redis)

    FILES_DIR.mkdir(parents=True, exist_ok=True)
    write_log(
        "tentaculo_link", "startup:v7_initialized (with cache+rate_limit+metrics)"
    )

    # Yield to allow app to run
    yield

    # Shutdown
    await clients.shutdown()
    await cache_shutdown()
    write_log("tentaculo_link", "shutdown:v7_complete")


# Create app
app = FastAPI(
    title="VX11 Tentáculo Link",
    version="7.0",
    lifespan=lifespan,
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Operator UI static files
operator_ui_path = Path(__file__).parent.parent / "operator" / "frontend" / "dist"
if operator_ui_path.exists():
    app.mount(
        "/operator/ui",
        StaticFiles(directory=str(operator_ui_path), html=True),
        name="operator_ui",
    )
    write_log("tentaculo_link", f"mounted_operator_ui:{operator_ui_path}")
else:
    write_log(
        "tentaculo_link",
        f"WARNING: operator_ui not found:{operator_ui_path}",
        level="WARNING",
    )


# ============ HEALTH & STATUS ============


@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok", "module": "tentaculo_link", "version": "7.0"}


@app.get("/operator")
async def operator_redirect():
    """Redirect /operator to /operator/ui/."""
    return RedirectResponse(url="/operator/ui/", status_code=302)


@app.get("/vx11/status")
async def vx11_status():
    """Aggregate health check for all modules (async parallel)."""
    import datetime

    clients = get_clients()
    health_results = await clients.health_check_all()
    # Defensive: some clients may (incorrectly) return coroutine objects
    # Ensure all module results are resolved to dicts before summarizing.
    for name, val in list(health_results.items()):
        try:
            if asyncio.iscoroutine(val):
                health_results[name] = await val
        except Exception as _exc:
            health_results[name] = {"status": "error", "error": str(_exc)}

    healthy_count = sum(1 for h in health_results.values() if h.get("status") == "ok")
    total_count = len(health_results)

    write_log("tentaculo_link", "vx11_status:aggregated")
    return {
        "ok": True,
        "status": "ok",
        "module": "tentaculo_link",
        "version": "7.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "ports": {
            "tentaculo_link": 8000,
            "gateway": 8000,
            "madre": 8001,
            "switch": 8002,
            "hermes": 8003,
            "hormiguero": 8004,
            "mcp": 8006,
            "shubniggurath": 8007,
            "spawner": 8008,
            "operator": 8011,
        },
        "modules": health_results,
        "summary": {
            "healthy_modules": healthy_count,
            "total_modules": total_count,
            "all_healthy": healthy_count == total_count,
        },
    }


@app.get("/vx11/circuit-breaker/status")
async def circuit_breaker_status(
    _: bool = Depends(token_guard),
):
    """Get circuit breaker status for all modules."""
    clients = get_clients()
    breakers = {}
    for name, client in clients.clients.items():
        breakers[name] = client.circuit_breaker.get_status()
    write_log("tentaculo_link", "circuit_breaker_status:fetched")
    return {
        "status": "ok",
        "breakers": breakers,
        "timestamp": time.time(),
    }


@app.get("/metrics")
async def metrics():
    """Export metrics in Prometheus text format."""
    metrics_obj = get_prometheus_metrics()
    export = metrics_obj.export_prometheus_format()
    write_log("tentaculo_link", "metrics:exported")
    return Response(content=export, media_type="text/plain; charset=utf-8")


# ============ HERMES PROXY (single-entrypoint routing) ============


@app.post("/hermes/get-engine", tags=["proxy-hermes"])
async def proxy_hermes_get_engine(
    body: Dict[str, Any],
    x_vx11_token: str = Header(None),
):
    """
    Proxy: POST /hermes/get-engine (forward to Hermes service)
    Single-entrypoint routing for Hermes engine discovery.
    Auth: X-VX11-Token header required (forwarded to upstream).
    """
    try:

        headers = {}
        if x_vx11_token:
            headers["X-VX11-Token"] = x_vx11_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://hermes:8003/hermes/get-engine",
                json=body,
                headers=headers,
            )
            write_log("tentaculo_link", f"proxy_hermes_get_engine:{resp.status_code}")
            return Response(
                content=resp.text,
                status_code=resp.status_code,
                media_type="application/json",
            )
    except Exception as exc:
        write_log(
            "tentaculo_link", f"proxy_hermes_get_engine_error:{exc}", level="ERROR"
        )
        raise HTTPException(status_code=502, detail="hermes_proxy_error")


@app.post("/hermes/execute", tags=["proxy-hermes"])
async def proxy_hermes_execute(
    body: Dict[str, Any],
    x_vx11_token: str = Header(None),
):
    """
    Proxy: POST /hermes/execute (forward to Hermes service)
    Single-entrypoint routing for Hermes execution requests.
    Auth: X-VX11-Token header required (forwarded to upstream).
    """
    try:

        headers = {}
        if x_vx11_token:
            headers["X-VX11-Token"] = x_vx11_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://hermes:8003/hermes/execute",
                json=body,
                headers=headers,
            )
            write_log("tentaculo_link", f"proxy_hermes_execute:{resp.status_code}")
            return Response(
                content=resp.text,
                status_code=resp.status_code,
                media_type="application/json",
            )
    except Exception as exc:
        write_log("tentaculo_link", f"proxy_hermes_execute_error:{exc}", level="ERROR")
        raise HTTPException(status_code=502, detail="hermes_proxy_error")


@app.get("/shub/rate-limit/status")
async def rate_limit_status(
    token: str = Header(None, alias="X-VX11-GW-TOKEN"),
):
    """Get current rate limit status for the requesting user."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing X-VX11-GW-TOKEN header")

    limiter = get_rate_limiter()
    status = limiter.get_status(token)
    write_log("tentaculo_link", f"rate_limit_status:retrieved for {token[:8]}...")
    return {
        "status": "ok",
        "rate_limit": status,
        "timestamp": time.time(),
    }


# ============ OPERATOR CHAT (CONTEXT-7 INTEGRATED) ============


@app.post("/operator/chat")
async def operator_chat(
    req: OperatorChatRequest,
    _: bool = Depends(token_guard),
):
    """
    Route chat to Operator backend with CONTEXT-7 integration.
    P1 fallback: if switch is offline, use madre chat.
    """
    session_id = req.session_id or str(uuid.uuid4())
    user_id = req.user_id or "local"

    # Track in CONTEXT-7
    context7 = get_context7_manager()
    context7.add_message(session_id, "user", req.message, req.metadata)
    context_hint = context7.get_hint_for_llm(session_id)

    # Route to Switch (canonical pipeline) with fallback to madre
    clients = get_clients()
    metadata = dict(req.metadata or {})
    if context_hint:
        metadata["context_summary"] = context_hint

    # Try switch first
    result = await clients.route_to_switch(
        prompt=req.message, session_id=session_id, metadata=metadata
    )

    # P1 Fallback: if switch is offline (solo_madre mode), use madre chat
    write_log("tentaculo_link", f"operator_chat:result_after_switch={result}")
    if result.get("status") == "service_offline" and result.get("module") == "switch":
        write_log("tentaculo_link", "operator_chat:triggering_fallback_to_madre")
        result = await clients.route_to_madre_chat(
            message=req.message, session_id=session_id, metadata=metadata
        )

    # Track response in CONTEXT-7
    assistant_msg = (
        result.get("response") or result.get("message") or json.dumps(result)
    )
    context7.add_message(session_id, "assistant", str(assistant_msg))

    write_log("tentaculo_link", f"operator_chat:{session_id}")
    return result


@app.post("/operator/task")
async def operator_task(
    req: OperatorTaskRequest,
    _: bool = Depends(token_guard),
):
    """Route TASK/ANALYSIS to Switch (canonical pipeline)."""
    session_id = req.session_id or str(uuid.uuid4())
    user_id = req.user_id or "local"

    payload = dict(req.payload or {})
    payload.setdefault("session_id", session_id)
    payload.setdefault("user_id", user_id)
    if req.intent_type:
        payload.setdefault("intent_type", req.intent_type)
    if req.metadata:
        payload.setdefault("metadata", req.metadata)

    clients = get_clients()
    result = await clients.route_to_switch_task(
        task_type=req.task_type,
        payload=payload,
        metadata=req.metadata,
        provider_hint=req.provider_hint,
        source="operator",
    )

    write_log("tentaculo_link", f"operator_task:{req.task_type}:{session_id}")
    return result


# ============ NEW: /operator/chat/ask (SIMPLIFIED CHAT) ============


@app.post("/operator/chat/ask")
async def operator_chat_ask(
    req: OperatorChatRequest,
    _: bool = Depends(token_guard),
):
    """
    Simplified chat endpoint (alternative to /operator/chat).
    Same behavior: route to Switch with fallback to Madre if solo_madre mode.
    """
    # Delegate to existing chat logic
    return await operator_chat(req, _)


# ============ NEW: /operator/status (AGGREGATED HEALTH) ============


@app.get("/operator/status")
async def operator_status(_: bool = Depends(token_guard)):
    """
    Aggregated health check without waking services.
    Returns health of madre, redis, tentaculo_link, switch (via circuit breaker), and window state.
    """
    import httpx

    status_data = {
        "status": "ok",
        "components": {},
        "windows": {"policy": "solo_madre", "active_count": 0},
    }

    # 1. Check tentaculo_link (localhost, always available)
    status_data["components"]["tentaculo_link"] = {"status": "ok", "port": 8000}

    # 2. Check madre health (fast GET, no spawn)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get("http://madre:8001/health")
            r.raise_for_status()
            madre_health = r.json()
            status_data["components"]["madre"] = {
                "status": madre_health.get("status", "unknown"),
                "port": 8001,
            }
            # Get window state from madre
            r2 = await client.get(
                "http://madre:8001/madre/power/state",
                headers={"x-vx11-token": VX11_TOKEN},
            )
            if r2.status_code == 200:
                power_state = r2.json()
                status_data["windows"]["policy"] = power_state.get(
                    "policy", "solo_madre"
                )
                status_data["windows"]["active_count"] = len(
                    power_state.get("active_windows", [])
                )
    except Exception as e:
        status_data["components"]["madre"] = {
            "status": "unreachable",
            "error": str(e)[:50],
        }
        status_data["status"] = "degraded"

    # 3. Check redis health (fast GET, no spawn)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get("http://redis:6379/ping")
            status_data["components"]["redis"] = {"status": "ok", "port": 6379}
    except Exception as e:
        status_data["components"]["redis"] = {
            "status": "unreachable",
            "error": str(e)[:50],
        }
        if status_data["status"] == "ok":
            status_data["status"] = "degraded"

    # 4. Check switch via circuit breaker (don't call directly)
    try:
        clients = get_clients()
        switch_client = clients.get_client("switch")
        if switch_client and hasattr(switch_client, "circuit_breaker"):
            cb_status = switch_client.circuit_breaker.get_status()
            if cb_status.get("state") == "open":
                status_data["components"]["switch"] = {
                    "status": "offline",
                    "reason": "circuit_open",
                    "port": 8002,
                }
            else:
                status_data["components"]["switch"] = {
                    "status": "available",
                    "port": 8002,
                }
        else:
            status_data["components"]["switch"] = {"status": "available", "port": 8002}
    except Exception as e:
        status_data["components"]["switch"] = {
            "status": "unknown",
            "error": str(e)[:50],
            "port": 8002,
        }

    write_log("tentaculo_link", f"operator_status:overall={status_data['status']}")
    return status_data


# ============ NEW: /operator/power/state (CURRENT POWER WINDOW STATE) ============


@app.get("/operator/power/state")
async def operator_power_state(_: bool = Depends(token_guard)):
    """
    Get current power window state: policy, active windows, running services.
    Fast query to madre (no spawn).
    """
    clients = get_clients()
    madre = clients.get_client("madre")
    if not madre:
        raise HTTPException(status_code=503, detail="madre_client_unavailable")

    try:
        # Query madre for power state
        result = await madre.get("/madre/power/state")
        write_log("tentaculo_link", "operator_power_state:retrieved")
        return result
    except Exception as e:
        write_log(
            "tentaculo_link", f"operator_power_state:error={str(e)[:50]}", level="WARN"
        )
        raise HTTPException(
            status_code=503, detail=f"power_state_unavailable: {str(e)[:50]}"
        )


@app.get("/operator/power/status")
async def operator_power_status(_: bool = Depends(token_guard)):
    """Proxy power status to Madre (single entrypoint)."""
    clients = get_clients()
    madre = clients.get_client("madre")
    if not madre:
        raise HTTPException(status_code=503, detail="madre_client_unavailable")
    result = await madre.get("/madre/power/status")
    write_log("tentaculo_link", "operator_power_status")
    return result


@app.get("/operator/power/policy/solo_madre/status")
async def operator_solo_madre_status(_: bool = Depends(token_guard)):
    """Proxy SOLO_MADRE policy status to Madre."""
    clients = get_clients()
    madre = clients.get_client("madre")
    if not madre:
        raise HTTPException(status_code=503, detail="madre_client_unavailable")
    result = await madre.get("/madre/power/policy/solo_madre/status")
    write_log("tentaculo_link", "operator_solo_madre_status")
    return result


@app.post("/operator/power/policy/solo_madre/apply")
async def operator_solo_madre_apply(_: bool = Depends(token_guard)):
    """Proxy SOLO_MADRE apply to Madre."""
    clients = get_clients()
    madre = clients.get_client("madre")
    if not madre:
        raise HTTPException(status_code=503, detail="madre_client_unavailable")
    result = await madre.post("/madre/power/policy/solo_madre/apply", payload={})
    write_log("tentaculo_link", "operator_solo_madre_apply")
    return result


@app.post("/operator/power/service/{name}/start")
async def operator_power_start(name: str, _: bool = Depends(token_guard)):
    """Proxy service start to Madre."""
    clients = get_clients()
    madre = clients.get_client("madre")
    if not madre:
        raise HTTPException(status_code=503, detail="madre_client_unavailable")
    result = await madre.post(f"/madre/power/service/{name}/start", payload={})
    write_log("tentaculo_link", f"operator_power_start:{name}")
    return result


@app.post("/operator/power/service/{name}/stop")
async def operator_power_stop(name: str, _: bool = Depends(token_guard)):
    """Proxy service stop to Madre."""
    clients = get_clients()
    madre = clients.get_client("madre")
    if not madre:
        raise HTTPException(status_code=503, detail="madre_client_unavailable")
    result = await madre.post(f"/madre/power/service/{name}/stop", payload={})
    write_log("tentaculo_link", f"operator_power_stop:{name}")
    return result


@app.post("/operator/power/service/{name}/restart")
async def operator_power_restart(name: str, _: bool = Depends(token_guard)):
    """Proxy service restart to Madre."""
    clients = get_clients()
    madre = clients.get_client("madre")
    if not madre:
        raise HTTPException(status_code=503, detail="madre_client_unavailable")
    result = await madre.post(f"/madre/power/service/{name}/restart", payload={})
    write_log("tentaculo_link", f"operator_power_restart:{name}")
    return result


# ============= POWER WINDOWS (Phase 2) =============
# TODO: These endpoints cannot be fully implemented in Phase 1 due to
# architectural constraints: tentaculo_link runs in Docker and does not
# have access to docker daemon or host-level docker compose execution.
#
# For Phase 1, use the metadata-only power windows API in madre:
#   POST /madre/power/window/open
#   POST /madre/power/window/close
#   GET /madre/power/state
#
# Phase 2 will implement full execution via:
#   - Host-level daemon wrapper, OR
#   - SSH delegation, OR
#   - New power-daemon microservice on host

# See: docs/audit/*/ARCHITECTURE_ANALYSIS.md


# ============ INEE EXTENDED ENDPOINTS (Proxy to Hormiguero) ============


@app.post("/operator/inee/builder/patchset", tags=["proxy-inee"])
async def operator_inee_builder_patchset(
    request: Request,
    _: bool = Depends(token_guard),
):
    """
    Proxy: Builder → create patchset (no execution, only INTENT).
    Dormant if HORMIGUERO_BUILDER_ENABLED != 1.
    """
    clients = get_clients()
    hormiguero = clients.get_client("hormiguero")
    if not hormiguero:
        raise HTTPException(status_code=503, detail="hormiguero_unavailable")

    body = await request.json()
    result = await hormiguero.post(
        "/hormiguero/inee/extended/builder/patchset", payload=body
    )
    write_log("tentaculo_link", "inee:builder:patchset:proxied")
    return result


@app.post("/operator/inee/colony/register", tags=["proxy-inee"])
async def operator_inee_colony_register(
    request: Request,
    _: bool = Depends(token_guard),
):
    """Proxy: Register remote colony."""
    clients = get_clients()
    hormiguero = clients.get_client("hormiguero")
    if not hormiguero:
        raise HTTPException(status_code=503, detail="hormiguero_unavailable")

    body = await request.json()
    result = await hormiguero.post(
        "/hormiguero/inee/extended/colony/register", payload=body
    )
    write_log("tentaculo_link", "inee:colony:register:proxied")
    return result


@app.post("/operator/inee/colony/envelope", tags=["proxy-inee"])
async def operator_inee_colony_envelope(
    request: Request,
    _: bool = Depends(token_guard),
):
    """Proxy: Create HMAC-signed envelope (remote colony communication)."""
    clients = get_clients()
    hormiguero = clients.get_client("hormiguero")
    if not hormiguero:
        raise HTTPException(status_code=503, detail="hormiguero_unavailable")

    body = await request.json()
    result = await hormiguero.post(
        "/hormiguero/inee/extended/colony/envelope", payload=body
    )
    write_log("tentaculo_link", "inee:colony:envelope:proxied")
    return result


@app.get("/operator/inee/status", tags=["proxy-inee"])
async def operator_inee_status(
    _: bool = Depends(token_guard),
):
    """Proxy: Get INEE extended status."""
    clients = get_clients()
    hormiguero = clients.get_client("hormiguero")
    if not hormiguero:
        raise HTTPException(status_code=503, detail="hormiguero_unavailable")

    result = await hormiguero.get("/hormiguero/inee/extended/status")
    write_log("tentaculo_link", "inee:status:proxied")
    return result


@app.get("/operator/session/{session_id}")
async def operator_session(
    session_id: str,
    _: bool = Depends(token_guard),
):
    """Get CONTEXT-7 session history."""
    context7 = get_context7_manager()
    session = context7.get_session(session_id)
    if not session:
        return {"error": "session_not_found", "session_id": session_id}
    write_log("tentaculo_link", f"operator_session_retrieved:{session_id}")
    return session.to_dict()


# ============ EVENT INGESTION ============


class EventIngestionRequest(BaseModel):
    """Event ingestion request model."""

    source: str
    type: str
    payload: Dict[str, Any]
    broadcast: bool = False
    metadata: Optional[Dict[str, Any]] = None


@app.post("/events/ingest")
async def events_ingest(
    req: EventIngestionRequest,
    _: bool = Depends(token_guard),
):
    """
    Ingest events from modules (madre, spawner, etc).
    Optionally broadcast via WebSocket if broadcast=True.
    Non-canonical events are accepted but not validated against schema.
    """
    event = {
        "source": req.source,
        "type": req.type,
        "payload": req.payload,
        "timestamp": int(time.time() * 1000),
        "metadata": req.metadata or {},
    }

    # Validate event against canonical schemas (if canonical)
    # Otherwise, accept as-is (non-canonical events bypass schema validation)
    if req.type in CANONICAL_EVENT_WHITELIST:
        validated = await validate_and_filter_event(event)
        if not validated:
            write_log(
                "tentaculo_link",
                f"event_ingest_rejected:source={req.source}:type={req.type}",
                level="WARNING",
            )
            return {
                "status": "rejected",
                "reason": "schema_validation_failed",
                "source": req.source,
            }
    else:
        # Non-canonical events are accepted as-is (for backward compatibility)
        validated = event
        write_log(
            "tentaculo_link",
            f"event_ingest_non_canonical:source={req.source}:type={req.type}",
            level="DEBUG",
        )

    # Increment cardinality counter
    cardinality_counter.increment(req.type)

    # Optionally broadcast via WebSocket
    if req.broadcast:
        try:
            await manager.broadcast(validated)
            write_log(
                "tentaculo_link",
                f"event_ingested_and_broadcast:source={req.source}:type={req.type}",
            )
        except Exception as e:
            write_log(
                "tentaculo_link",
                f"event_broadcast_error:{str(e)}",
                level="WARNING",
            )
            return {
                "status": "ingested_no_broadcast",
                "reason": "broadcast_failed",
                "error": str(e),
            }
    else:
        write_log(
            "tentaculo_link",
            f"event_ingested:source={req.source}:type={req.type}",
        )

    return {"status": "received", "source": req.source, "type": req.type}


# ============ VX11 OVERVIEW (AGGREGATED) ============


@app.get("/vx11/overview")
async def vx11_overview(_: bool = Depends(token_guard)):
    """Get aggregated overview of all VX11 modules."""
    clients = get_clients()
    health_results = await clients.health_check_all()

    overview = {
        "status": "ok",
        "gateway": "tentaculo_link",
        "version": "7.0",
        "modules_health": health_results,
        "summary": {
            "total_modules": len(health_results),
            "healthy": sum(
                1 for h in health_results.values() if h.get("status") == "ok"
            ),
            "unhealthy": sum(
                1 for h in health_results.values() if h.get("status") != "ok"
            ),
        },
    }
    write_log("tentaculo_link", "vx11_overview:aggregated")
    return overview


# ============ SHUB ROUTING ============


@app.get("/shub/dashboard")
async def shub_dashboard(_: bool = Depends(token_guard)):
    """Get Shub dashboard info."""
    clients = get_clients()
    result = await clients.route_to_shub("/shub/dashboard", {})
    write_log("tentaculo_link", "route_shub:dashboard")
    return result


# ============ RESOURCES (HERMES) ============


@app.get("/resources")
async def resources(_: bool = Depends(token_guard)):
    """Get available resources (CLI tools + models)."""
    clients = get_clients()

    # Query Hermes for resources
    hermes_client = clients.get_client("hermes")
    if not hermes_client:
        return {"error": "hermes_unavailable"}

    result = await hermes_client.get("/hermes/resources")
    write_log("tentaculo_link", "route_hermes:resources")
    return result


# ============ HORMIGUERO ROUTING ============


@app.get("/hormiguero/queen/status")
async def hormiguero_status(_: bool = Depends(token_guard)):
    """Get Hormiguero Queen status."""
    clients = get_clients()
    result = await clients.route_to_hormiguero("/queen/status")
    write_log("tentaculo_link", "route_hormiguero:queen_status")
    return result


@app.get("/hormiguero/report")
async def hormiguero_report(limit: int = 50, _: bool = Depends(token_guard)):
    """Get recent Hormiguero incidents."""
    clients = get_clients()
    result = await clients.route_to_hormiguero(f"/report?limit={limit}")
    write_log("tentaculo_link", f"route_hormiguero:report:limit={limit}")
    return result


# ============ OPERATOR EXTENSIONS (v8.1) ============


@app.get("/operator/snapshot")
async def operator_snapshot(t: int = 0, _: bool = Depends(token_guard)):
    """Request VX11 state snapshot at timestamp t (v8.1 stub - returns current state if t=0)."""
    # TODO: When BD snapshots are available, query data/runtime/vx11.db for state at timestamp t
    # For now, return current state as fallback
    write_log("tentaculo_link", f"operator_snapshot:request:t={t}")
    return {
        "timestamp": t if t > 0 else int(time.time() * 1000),
        "state": {
            "madre": {"status": "active"},
            "switch": {"routing": "adaptive"},
            "hormiguero": {"queen_alive": True},
        },
    }


# ============ ERROR HANDLERS ============


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with logging."""
    write_log(
        "tentaculo_link", f"http_error:{exc.status_code}:{exc.detail}", level="WARNING"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


# ============ CANONICAL EVENT SCHEMAS & VALIDATION ============

CANONICAL_EVENT_SCHEMAS = {
    "system.alert": {
        "required": ["alert_id", "severity", "message", "timestamp"],
        "types": {"alert_id": str, "severity": str, "message": str, "timestamp": int},
        "nature": "incident",
        "max_payload": 2048,
    },
    "system.correlation.updated": {
        "required": ["correlation_id", "related_events", "strength", "timestamp"],
        "types": {
            "correlation_id": str,
            "related_events": list,
            "strength": (int, float),
            "timestamp": int,
        },
        "nature": "meta",
        "max_payload": 2048,
    },
    "forensic.snapshot.created": {
        "required": ["snapshot_id", "reason", "timestamp"],
        "types": {"snapshot_id": str, "reason": str, "timestamp": int},
        "nature": "forensic",
        "max_payload": 1024,
    },
    "madre.decision.explained": {
        "required": ["decision_id", "summary", "confidence", "timestamp"],
        "types": {
            "decision_id": str,
            "summary": str,
            "confidence": (int, float),
            "timestamp": int,
        },
        "nature": "decision",
        "max_payload": 3072,
    },
    "switch.tension.updated": {
        "required": ["value", "components", "timestamp"],
        "types": {"value": int, "components": dict, "timestamp": int},
        "nature": "state",
        "max_payload": 1024,
    },
    "shub.action.narrated": {
        "required": ["action", "reason", "next_step", "timestamp"],
        "types": {"action": str, "reason": str, "next_step": str, "timestamp": int},
        "nature": "narration",
        "max_payload": 2048,
    },
}

CANONICAL_EVENT_WHITELIST: Set[str] = set(CANONICAL_EVENT_SCHEMAS.keys())


def validate_event_type(event_type: str) -> bool:
    """Check if event type is in canonical whitelist."""
    return event_type in CANONICAL_EVENT_WHITELIST


def log_event_rejection(event_type: str, reason: str):
    """Log rejected event as DEBUG (minimal noise)."""
    write_log(
        "tentaculo_link",
        f"event_rejected:type={event_type}:reason={reason}",
        level="DEBUG",
    )


def validate_event_schema(event: dict) -> Optional[dict]:
    """
    PHASE V1: Validate event against canonical schema.
    - Check required fields
    - Validate basic types
    - Check payload size

    Returns normalized event or None if invalid.
    """
    event_type = event.get("type")

    if not event_type:
        log_event_rejection("unknown", "missing type field")
        return None

    if not validate_event_type(event_type):
        log_event_rejection(event_type, "not in canonical whitelist")
        return None

    schema = CANONICAL_EVENT_SCHEMAS[event_type]

    # Check required fields
    for field in schema["required"]:
        if field not in event:
            log_event_rejection(event_type, f"missing required field: {field}")
            return None

    # Validate types
    for field, expected_type in schema["types"].items():
        if field in event:
            value = event[field]
            if isinstance(expected_type, tuple):
                # Multiple types allowed (e.g., int or float)
                if not isinstance(value, expected_type):
                    log_event_rejection(
                        event_type,
                        f"invalid type for {field}: expected {expected_type}, got {type(value).__name__}",
                    )
                    return None
            else:
                if not isinstance(value, expected_type):
                    log_event_rejection(
                        event_type,
                        f"invalid type for {field}: expected {expected_type.__name__}, got {type(value).__name__}",
                    )
                    return None

    # Check payload size
    payload_json = json.dumps(event)
    if len(payload_json.encode("utf-8")) > schema["max_payload"]:
        log_event_rejection(
            event_type,
            f"payload exceeds max size: {len(payload_json)} > {schema['max_payload']}",
        )
        return None

    return event


def normalize_event(event: dict) -> dict:
    """
    PHASE V2: Normalize and tag event internally.
    - Ensure timestamp (milliseconds)
    - Add _schema_version (internal tag, will be stripped before sending to UI)
    - Add _nature (semantic classification, internal only)
    - Track in correlation graph
    """
    if "timestamp" not in event:
        event["timestamp"] = int(time.time() * 1000)

    # Tag with schema version for internal tracking
    event["_schema_version"] = "v1.0"

    # Add nature (from schema)
    event_type = event.get("type")
    if event_type in CANONICAL_EVENT_SCHEMAS:
        event["_nature"] = CANONICAL_EVENT_SCHEMAS[event_type]["nature"]

    # Track in correlation graph for visualization
    correlation_tracker.add_event(event)

    return event


async def validate_and_filter_event(event: dict) -> Optional[dict]:
    """
    Complete event validation pipeline:
    1. Schema validation (PHASE V1)
    2. Normalization (PHASE V2)
    3. Return None if invalid, dict if valid
    """
    validated = validate_event_schema(event)
    if validated is None:
        return None

    normalized = normalize_event(validated)
    event_type = normalized.get("type", "unknown")
    write_log(
        "tentaculo_link",
        f"event_validated_and_normalized:type={event_type}",
        level="DEBUG",
    )
    return normalized


async def create_system_alert(message: str, source: str, severity: str = "L3") -> dict:
    """Synthesize system.alert event (ONLY in Tentáculo Link)."""
    alert_id = str(uuid.uuid4())
    return {
        "type": "system.alert",
        "alert_id": alert_id,
        "severity": severity,
        "message": message,
        "timestamp": int(time.time() * 1000),
    }


async def create_system_state_summary() -> dict:
    """Synthesize system.correlation.updated event (ONLY in Tentáculo Link)."""
    correlation_id = str(uuid.uuid4())
    return {
        "type": "system.correlation.updated",
        "correlation_id": correlation_id,
        "related_events": [],
        "strength": 0.0,
        "timestamp": int(time.time() * 1000),
    }


# ============ EVENT CARDINALITY TRACKING (DEBUG OBSERVABILITY) ============


class EventCardinalityCounter:
    """Track event frequencies for debugging and spam detection."""

    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.window_start = time.time()

    def increment(self, event_type: str):
        """Increment counter for event type."""
        if event_type not in self.counters:
            self.counters[event_type] = 0
        self.counters[event_type] += 1

    def get_stats(self) -> Dict[str, int]:
        """Return events/min. Reset window if > 60s elapsed."""
        now = time.time()
        elapsed = now - self.window_start

        if elapsed > 60:
            # Reset window
            stats = self.counters.copy()
            self.counters = {}
            self.window_start = now
            return stats

        return self.counters.copy()

    def get_stats_with_rate(self) -> Dict[str, Dict[str, float]]:
        """Return counts and rates (events/min)."""
        now = time.time()
        elapsed = max(now - self.window_start, 1)  # Avoid division by zero

        result = {}
        for event_type, count in self.counters.items():
            rate_per_min = (count / elapsed) * 60
            result[event_type] = {
                "count": count,
                "rate_per_min": round(rate_per_min, 2),
            }

        return result


cardinality_counter = EventCardinalityCounter()


# ============ EVENT CORRELATION TRACKER (VISUALIZATION) ============


class EventCorrelationTracker:
    """Track event correlations for DAG visualization (lightweight)."""

    def __init__(self, max_nodes: int = 50, ttl_seconds: int = 300):
        self.edges: Dict[str, Dict[str, Any]] = (
            {}
        )  # {event_id: {target_id: strength, ...}}
        self.nodes: Dict[str, Dict[str, Any]] = {}  # {event_id: {type, timestamp, ...}}
        self.max_nodes = max_nodes
        self.ttl_seconds = ttl_seconds

    def add_event(self, event: dict):
        """Register event as node in correlation graph."""
        event_id = (
            event.get("alert_id")
            or event.get("decision_id")
            or event.get("snapshot_id")
            or str(uuid.uuid4())
        )
        now = int(time.time() * 1000)

        self.nodes[event_id] = {
            "type": event.get("type", "unknown"),
            "timestamp": event.get("timestamp", now),
            "severity": event.get("severity", "L1"),
            "nature": event.get("_nature", "default"),
        }

        # Cleanup old nodes if exceeds max
        if len(self.nodes) > self.max_nodes:
            self._cleanup_old_nodes()

    def add_correlation(self, source_id: str, target_id: str, strength: float = 0.5):
        """Add edge between two events (temporal correlation)."""
        if source_id not in self.edges:
            self.edges[source_id] = {}
        self.edges[source_id][target_id] = round(min(strength, 1.0), 2)

    def get_graph(self) -> Dict[str, Any]:
        """Export graph as {nodes, edges} for visualization."""
        return {
            "nodes": list(self.nodes.values()),
            "edges": [
                {"source": src, "target": tgt, "strength": str_dict[tgt]}
                for src, str_dict in self.edges.items()
                for tgt in str_dict
            ],
            "total_nodes": len(self.nodes),
            "total_edges": sum(len(v) for v in self.edges.values()),
        }

    def _cleanup_old_nodes(self):
        """Remove oldest nodes when exceeding max_nodes."""
        now = int(time.time() * 1000)
        sorted_nodes = sorted(self.nodes.items(), key=lambda x: x[1]["timestamp"])

        # Keep newest 80% of nodes
        to_keep = int(self.max_nodes * 0.8)
        nodes_to_remove = sorted_nodes[:-to_keep]

        for node_id, _ in nodes_to_remove:
            del self.nodes[node_id]
            self.edges.pop(node_id, None)
            # Remove references to this node
            for src in self.edges:
                self.edges[src].pop(node_id, None)


correlation_tracker = EventCorrelationTracker(max_nodes=50)


# ============ WEBSOCKET (PLACEHOLDER FOR FUTURE) ============


class ConnectionManager:
    """Track WebSocket connections."""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.connections[client_id] = websocket
        write_log("tentaculo_link", f"ws_connect:{client_id}")

    async def disconnect(self, client_id: str):
        self.connections.pop(client_id, None)
        write_log("tentaculo_link", f"ws_disconnect:{client_id}")

    async def broadcast(self, event: dict):
        """
        PHASE V3: Broadcast canonical event to Operator clients only.
        - Final validation before broadcast
        - Remove internal tags (_schema_version) before sending
        - Track cardinality for observability
        - Log errors as DEBUG only
        """
        event_type = event.get("type", "unknown")

        # Final validation (redundant but safe)
        if not validate_event_type(event_type):
            log_event_rejection(
                event_type, "broadcast attempted with non-canonical type"
            )
            return

        # Track event frequency for DEBUG observability
        cardinality_counter.increment(event_type)

        # Remove internal tags before sending to Operator
        event_clean = {k: v for k, v in event.items() if not k.startswith("_")}

        for client_id, conn in list(self.connections.items()):
            try:
                await conn.send_json(event_clean)
                write_log(
                    "tentaculo_link",
                    f"broadcast_sent:type={event_type}:client={client_id}",
                    level="DEBUG",
                )
            except Exception as e:
                # Client disconnected or error; silently skip
                write_log(
                    "tentaculo_link",
                    f"broadcast_failed:client={client_id}:error={str(e)}",
                    level="DEBUG",
                )


manager = ConnectionManager()


# ============ DEBUG ENDPOINTS ============


@app.get("/debug/events/cardinality")
async def debug_events_cardinality():
    """
    DEBUG endpoint: Get event cardinality statistics.
    Returns event counts and rates (events/min) for monitoring.
    """
    stats = cardinality_counter.get_stats_with_rate()
    window_elapsed = time.time() - cardinality_counter.window_start

    return {
        "status": "ok",
        "timestamp": int(time.time() * 1000),
        "window_seconds": round(window_elapsed, 2),
        "events": stats,
        "total_events": sum(s["count"] for s in stats.values()) if stats else 0,
    }


@app.get("/debug/events/correlations")
async def debug_events_correlations():
    """
    DEBUG endpoint: Get event correlation graph (DAG).
    Returns nodes and edges for visualization (Operator timeline).
    """
    graph = correlation_tracker.get_graph()
    return {
        "status": "ok",
        "timestamp": int(time.time() * 1000),
        "graph": graph,
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, channel: str = "event", client_id: str = "anonymous"
):
    """
    WebSocket endpoint for Operator clients (v7).
    - Sends initial 'control' message to confirm connection.
    - Echoes client messages (if valid JSON) back to sender.
    - Broadcasts to other clients if message is canonical.
    - Graceful disconnect handling.
    """
    await manager.connect(websocket, client_id)
    try:
        # Send initial control message to confirm connection
        control_msg = {
            "channel": "control",
            "type": "connected",
            "client_id": client_id,
        }
        await websocket.send_json(control_msg)
        write_log("tentaculo_link", f"ws_sent_control:{client_id}")

        # Echo loop: accept messages and send back
        while True:
            try:
                data = await websocket.receive_text()
                try:
                    event = json.loads(data)
                    # Echo event back to sender
                    await websocket.send_json(event)
                    write_log(
                        "tentaculo_link",
                        f"ws_echo:{client_id}:type={event.get('type')}",
                    )

                    # Validate and broadcast if canonical
                    validated = await validate_and_filter_event(event)
                    if validated:
                        await manager.broadcast(validated)
                except json.JSONDecodeError:
                    log_event_rejection("malformed", "invalid JSON")
                    # Connection stays open; client can retry
            except RuntimeError:
                # Connection issue; silently close
                break
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
        write_log("tentaculo_link", f"ws_disconnect_normal:{client_id}")


# ============================================================================
# PHASE 2: SHUB PROXY — /shub/{path:path} -> http://shubniggurath:8007/{path}
# ============================================================================

import os
import time as time_module

SHUB_UPSTREAM = os.environ.get("VX11_SHUB_UPSTREAM", "http://shubniggurath:8007")
SHUB_GATEWAY_TOKEN = os.environ.get("VX11_GATEWAY_TOKEN", VX11_TOKEN)


# ===== PHASE 3: CACHED ENDPOINTS =====


@app.get("/shub/health")
async def proxy_shub_health_cached(x_correlation_id: str = Header(None)):
    """
    Proxy /shub/health with Redis cache (TTL 60s).

    Cache hit → 1ms latency
    Cache miss → forward to Shub + cache result
    """
    cache = get_cache()
    cache_key = "shub:health"
    cache_ttl = get_ttl(cache_key)
    correlation_id = x_correlation_id or str(uuid.uuid4())

    # Try cache first
    cached = await cache.get(cache_key)
    if cached:
        write_log(
            "tentaculo_link",
            f"shub_proxy_cache_hit:path=/shub/health:correlation_id={correlation_id}",
        )
        # Add correlation_id to cached response
        if isinstance(cached, dict):
            cached["correlation_id"] = correlation_id
        return cached

    # Cache miss: forward to Shub
    try:
        upstream_url = f"{SHUB_UPSTREAM}/health"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(upstream_url)

        result = response.json()

        # Cache the result
        await cache.set(cache_key, result, ttl=cache_ttl)

        write_log(
            "tentaculo_link",
            f"shub_proxy_cache_miss:path=/shub/health:status={response.status_code}:correlation_id={correlation_id}",
        )

        if isinstance(result, dict):
            result["correlation_id"] = correlation_id
        return result

    except (httpx.ConnectError, httpx.TimeoutException):
        write_log(
            "tentaculo_link",
            f"shub_proxy_unavailable:path=/shub/health:correlation_id={correlation_id}",
        )
        return JSONResponse(
            status_code=503,
            content={
                "error": "shub_unavailable",
                "correlation_id": correlation_id,
            },
        )


@app.post("/shub/cache/clear")
async def cache_clear_handler(x_vx11_gw_token: str = Header(None)):
    """
    Manual cache invalidation endpoint.
    Requires X-VX11-GW-TOKEN header.
    """
    if not x_vx11_gw_token or x_vx11_gw_token != SHUB_GATEWAY_TOKEN:
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden"},
        )

    cache = get_cache()
    count = await cache.delete("shub:health", "shub:ready", "shub:openapi")

    write_log(
        "tentaculo_link",
        f"cache_clear:keys_deleted={count}",
    )

    return {
        "status": "cleared",
        "keys_deleted": count,
        "timestamp": time_module.time(),
    }


# ===== GENERIC PROXY HANDLER =====


@app.api_route(
    "/shub/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    tags=["proxy-shub"],
    response_model=None,
)
async def proxy_shub(
    request: Request,
    path: str,
    x_correlation_id: str = Header(None),
) -> Union[JSONResponse, StreamingResponse]:
    """
    Proxy all /shub/* requests to internal shubniggurath service.

    Security:
    - /shub/health and /shub/openapi.json: allowed without token
    - Other endpoints: require X-VX11-GW-TOKEN header
    - Rate limiting: Per-user 1000 req/min, per-IP 5000 req/min, protected 100 req/min

    Correlation ID:
    - If X-Correlation-ID provided, pass through
    - Otherwise, generate new UUID

    Error Handling:
    - If shubniggurath unavailable: return 503
    - If rate limited: return 429

    Logging:
    - Structured event with status_code, path, latency_ms, correlation_id
    """

    start_time = time_module.time()

    # Initialize limiter and metrics
    limiter = get_rate_limiter()
    metrics = get_prometheus_metrics()

    # Generate or use provided correlation_id
    correlation_id = x_correlation_id or str(uuid.uuid4())

    # Endpoints that don't require gateway token
    public_endpoints = {"/shub/health", "/shub/openapi.json", "/shub/ready"}
    request_path = f"/shub/{path}" if path else "/shub/"

    # Token validation for protected endpoints
    gw_token = None
    if request_path not in public_endpoints:
        gw_token = request.headers.get("X-VX11-GW-TOKEN")
        if not gw_token or gw_token != SHUB_GATEWAY_TOKEN:
            write_log(
                "tentaculo_link",
                f"shub_proxy_auth_fail:path={request_path}:correlation_id={correlation_id}",
            )
            return JSONResponse(
                status_code=403,
                content={"error": "forbidden", "correlation_id": correlation_id},
            )

    # Rate limiting check
    identifier = gw_token or request.client.host if request.client else "unknown"
    is_protected = request_path not in public_endpoints

    if limiter:
        limit_count = limiter.protected_limit if is_protected else limiter.default_limit
        allowed, limit_info = await limiter.check_limit(identifier, limit_count)

        if not allowed:
            latency_ms = (time_module.time() - start_time) * 1000
            metrics.record_rate_limit_rejection()

            write_log(
                "tentaculo_link",
                f"shub_proxy_rate_limited:path={request_path}:identifier={identifier[:8]}:latency_ms={latency_ms:.1f}:correlation_id={correlation_id}",
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "too_many_requests",
                    "detail": f"Rate limit exceeded. Retry after {limit_info.get('retry_after', 60)}s",
                    "retry_after": limit_info.get("retry_after", 60),
                    "correlation_id": correlation_id,
                },
                headers={"Retry-After": str(limit_info.get("retry_after", 60))},
            )

    # Build upstream URL
    query_string = str(request.url.query) if request.url.query else ""
    upstream_url = f"{SHUB_UPSTREAM}/{path}"
    if query_string:
        upstream_url = f"{upstream_url}?{query_string}"

    # Prepare headers for upstream
    upstream_headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ["host", "connection"]:
            upstream_headers[key] = value

    # Add/update correlation_id header
    upstream_headers["X-Correlation-ID"] = correlation_id
    upstream_headers["X-Forwarded-By"] = "tentaculo_link"

    try:
        # Forward request to shubniggurath
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=upstream_url,
                headers=upstream_headers,
                content=(
                    await request.body()
                    if request.method in ["POST", "PUT", "PATCH"]
                    else None
                ),
                follow_redirects=True,
            )

        latency_ms = (time_module.time() - start_time) * 1000

        # Record metrics
        if metrics:
            metrics.record_proxy_request(
                response.status_code, request_path, request.method, latency_ms
            )

        # Log successful proxy
        write_log(
            "tentaculo_link",
            f"shub_proxy:status={response.status_code}:path={request_path}:latency_ms={latency_ms:.1f}:correlation_id={correlation_id}",
        )

        # Return proxied response
        return StreamingResponse(
            iter([response.content]),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type", "application/json"),
        )

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        latency_ms = (time_module.time() - start_time) * 1000

        # Record error metrics
        if metrics:
            metrics.record_proxy_request(503, request_path, request.method, latency_ms)

        # Shubniggurath unavailable
        write_log(
            "tentaculo_link",
            f"shub_proxy_unavailable:path={request_path}:error={type(e).__name__}:latency_ms={latency_ms:.1f}:correlation_id={correlation_id}",
        )

        return JSONResponse(
            status_code=503,
            content={
                "error": "shub_unavailable",
                "detail": "Audio engine service is temporarily unavailable",
                "correlation_id": correlation_id,
            },
        )

    except Exception as e:
        latency_ms = (time_module.time() - start_time) * 1000

        # Unexpected error
        write_log(
            "tentaculo_link",
            f"shub_proxy_error:path={request_path}:error={type(e).__name__}:{str(e)[:50]}:correlation_id={correlation_id}",
        )

        return JSONResponse(
            status_code=502,
            content={
                "error": "gateway_error",
                "detail": "Error forwarding request to audio engine",
                "correlation_id": correlation_id,
            },
        )


# ============================================================================
# FASE 2: OPERATOR VISOR ENDPOINTS
# ============================================================================


@app.get("/operator/observe")
async def operator_observe():
    """
    Aggregate status for Operator Visor (read-only, fast).

    Returns: High-level status of key services.
    Designed for Operator UI to display module health without detailed query.
    """
    import datetime

    clients = get_clients()
    health_results = await clients.health_check_all()

    # Defensive: resolve coroutines
    for name, val in list(health_results.items()):
        try:
            if asyncio.iscoroutine(val):
                health_results[name] = await val
        except Exception as _exc:
            health_results[name] = {"status": "error", "error": str(_exc)}

    # Prepare "observed" modules for UI
    observed_services = {
        "tentaculo_link": health_results.get("tentaculo_link", {}),
        "madre": health_results.get("madre", {}),
        "switch": health_results.get("switch", {}),
        "spawner": health_results.get("spawner", {}),
        "hormiguero": health_results.get("hormiguero", {}),
    }

    # Add latency and timestamp
    for service_name, status_data in observed_services.items():
        if isinstance(status_data, dict):
            status_data.setdefault("latency_ms", 0)
            status_data.setdefault("timestamp", datetime.datetime.utcnow().isoformat())

    write_log("tentaculo_link", "operator_observe:aggregated")

    # FASE 3: REAL tracing from BD (canonical source of truth)
    trace_info = None
    try:
        import sqlite3

        db_path = "/app/data/runtime/vx11.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Leer ÚLTIMO ruteo real de BD (canonical)
        cursor.execute(
            """
            SELECT id, trace_id, provider_id, route_type, timestamp
            FROM routing_events
            ORDER BY timestamp DESC LIMIT 1
        """
        )
        row = cursor.fetchone()

        if row:
            provider_id = row["provider_id"]
            trace_id = row["trace_id"]

            # Tratar de resolver nombre amigable desde cli_providers
            provider_name = provider_id
            cursor.execute(
                """
                SELECT name FROM cli_providers
                WHERE id = ? OR provider_id = ? LIMIT 1
            """,
                (provider_id, provider_id),
            )
            provider_row = cursor.fetchone()
            if provider_row:
                provider_name = provider_row["name"]

            trace_info = {
                "trace_id": trace_id,
                "provider_id": provider_id,
                "provider_name": provider_name,
                "route_type": row["route_type"],
                "timestamp": row["timestamp"],
            }

        conn.close()
    except Exception as trace_exc:
        write_log("tentaculo_link", f"operator_observe:trace_read_failed:{trace_exc}")
        trace_info = None

    # Build response with REAL tracing (not env-var fake)
    response = {
        "ok": True,
        "request_id": str(__import__("uuid").uuid4()),
        "route_taken": "GET /operator/observe",
        "degraded": False,
        "data": {
            "services": observed_services,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "trace": trace_info,  # REAL tracing from BD
        },
        "errors": [],
    }

    # Add provider/model from trace IF available (not invented)
    if trace_info:
        response["provider_used"] = trace_info["provider_name"]

    return response


# ============ AUTH ENDPOINTS (Public, Proxy to Operator Backend) ============


@app.post("/auth/login")
async def auth_login(request: dict):
    """
    Proxy login to Operator Backend.

    Request: {"username": "admin", "password": "admin"}
    Response: {"access_token": "...", "token_type": "bearer", "expires_in": 3600}
    """
    clients = get_clients()
    operator = clients.get_client("operator-backend")
    if not operator:
        raise HTTPException(status_code=503, detail="operator_backend_unavailable")

    result = await operator.post("/auth/login", payload=request)
    write_log("tentaculo_link", "auth_login")
    return result


@app.post("/auth/logout")
async def auth_logout(_: bool = Depends(token_guard)):
    """Proxy logout to Operator Backend (requires token)."""
    clients = get_clients()
    operator = clients.get_client("operator-backend")
    if not operator:
        raise HTTPException(status_code=503, detail="operator_backend_unavailable")

    result = await operator.post("/auth/logout", payload={})
    write_log("tentaculo_link", "auth_logout")
    return result


# ============ OPERATOR API — P0 NATIVE ENDPOINTS (NO operator_backend dependency) ============


@app.get("/operator/api/status", tags=["operator-api-p0"])
async def operator_api_status(_: bool = Depends(token_guard)):
    """
    P0: Stable status shape for Operator UI.
    Does NOT call operator_backend (archived).
    Returns current policy + core service health + OFF_BY_POLICY state.
    """
    clients = get_clients()
    health_results = await clients.health_check_all()

    return {
        "status": "ok",
        "policy": "solo_madre",  # Always solo_madre by default
        "core_services": {
            "madre": health_results.get("madre", {}).get("status") == "healthy",
            "redis": health_results.get("redis", {}).get("status") == "healthy",
            "tentaculo_link": health_results.get("tentaculo_link", {}).get("status")
            == "healthy",
        },
        "optional_services": {
            "switch": {"status": "OFF_BY_POLICY", "reason": "solo_madre policy"},
            "hermes": {"status": "OFF_BY_POLICY", "reason": "solo_madre policy"},
            "hormiguero": {"status": "OFF_BY_POLICY", "reason": "solo_madre policy"},
            "spawner": {"status": "OFF_BY_POLICY", "reason": "solo_madre policy"},
            "operator_backend": {
                "status": "ARCHIVED",
                "reason": "UI moved to tentaculo_link",
            },
        },
        "degraded": not all(
            health_results.get(s, {}).get("status") == "healthy"
            for s in ["madre", "redis", "tentaculo_link"]
        ),
    }


@app.get("/operator/api/modules", tags=["operator-api-p0"])
async def operator_api_modules(_: bool = Depends(token_guard)):
    """
    P0: List all modules with state + reason.
    OFF_BY_POLICY modules shown as inactive (not error).
    """
    clients = get_clients()
    health_results = await clients.health_check_all()

    modules = {}

    # Core (always should be up in solo_madre)
    for name in ["madre", "redis", "tentaculo_link"]:
        info = health_results.get(name, {})
        modules[name] = {
            "status": "healthy" if info.get("status") == "healthy" else "unhealthy",
            "port": {"madre": 8001, "redis": 6379, "tentaculo_link": 8000}.get(name),
            "reason": (
                "Core service" if info.get("status") == "healthy" else "Check logs"
            ),
            "category": "core",
        }

    # Optional (OFF_BY_POLICY in solo_madre)
    for name in ["switch", "hermes", "hormiguero", "spawner"]:
        modules[name] = {
            "status": "OFF_BY_POLICY",
            "port": {
                "switch": 8002,
                "hermes": 8003,
                "hormiguero": 8004,
                "spawner": 8006,
            }.get(name),
            "reason": "solo_madre policy active",
            "category": "optional",
        }

    # Archived
    modules["operator_backend"] = {
        "status": "ARCHIVED",
        "port": 8011,
        "reason": "Operator API migrated to tentaculo_link:/operator/*",
        "category": "archived",
    }

    return {"modules": modules}


@app.post("/operator/api/chat", tags=["operator-api-p0"])
async def operator_api_chat(req: OperatorChatRequest, _: bool = Depends(token_guard)):
    """
    P0: Chat endpoint (degraded mode in solo_madre).
    If switch is available, route to it; otherwise return degraded response.
    """
    session_id = req.session_id or f"session_{int(time.time())}"

    # Attempt to use switch if available, else fallback to degraded
    clients = get_clients()
    switch_client = clients.get_client("switch")

    if switch_client:
        try:
            result = await switch_client.post(
                "/switch/chat",
                payload={"message": req.message, "session_id": session_id},
                timeout=4.0,
            )
            return result
        except Exception as e:
            write_log("tentaculo_link", f"chat_switch_failed:{str(e)}", level="WARNING")

    # Degraded response
    return {
        "message_id": f"msg_{int(time.time())}",
        "session_id": session_id,
        "response": f"[DEGRADED MODE] Switch service unavailable (solo_madre policy). Your message: {req.message}",
        "degraded": True,
        "reason": "Switch service OFF_BY_POLICY in solo_madre mode",
    }


@app.get("/operator/api/events", tags=["operator-api-p0"])
async def operator_api_events(limit: int = 10, _: bool = Depends(token_guard)):
    """
    P0: Events polling endpoint (no SSE yet).
    Returns recent events or empty array (not stub, not error).
    """
    # TODO: Implement event storage in SQLite (P1+)
    # For now, return empty but valid response
    return {
        "events": [],
        "total": 0,
        "limit": limit,
        "note": "Event storage P1+ feature",
    }


@app.get("/operator/api/scorecard", tags=["operator-api-p0"])
async def operator_api_scorecard(_: bool = Depends(token_guard)):
    """
    P0: Scorecard (PERCENTAGES + SCORECARD from audit dir or defaults).
    If files exist, parse them; else return nulls with reason.
    """
    percentages_path = Path("/app/docs/audit/PERCENTAGES.json")
    scorecard_path = Path("/app/docs/audit/SCORECARD.json")

    percentages = None
    scorecard = None

    try:
        if percentages_path.exists():
            percentages = json.loads(percentages_path.read_text())
    except Exception as e:
        write_log("tentaculo_link", f"scorecard_read_error:{str(e)}", level="WARNING")

    try:
        if scorecard_path.exists():
            scorecard = json.loads(scorecard_path.read_text())
    except Exception as e:
        write_log("tentaculo_link", f"scorecard_read_error:{str(e)}", level="WARNING")

    return {
        "percentages": percentages,
        "scorecard": scorecard,
        "files_found": {
            "percentages": percentages_path.exists(),
            "scorecard": scorecard_path.exists(),
        },
    }


@app.get("/operator/api/topology", tags=["operator-api-p0"])
async def operator_api_topology(_: bool = Depends(token_guard)):
    """
    P0: Static topology graph (minimal, annotated with policy state).
    Shows core + optional services + policy context.
    """
    return {
        "policy": "solo_madre",
        "graph": {
            "nodes": [
                {
                    "id": "madre",
                    "label": "Madre",
                    "status": "UP",
                    "port": 8001,
                    "type": "core",
                },
                {
                    "id": "redis",
                    "label": "Redis",
                    "status": "UP",
                    "port": 6379,
                    "type": "core",
                },
                {
                    "id": "tentaculo_link",
                    "label": "Tentáculo Link",
                    "status": "UP",
                    "port": 8000,
                    "type": "core",
                },
                {
                    "id": "switch",
                    "label": "Switch",
                    "status": "OFF_BY_POLICY",
                    "port": 8002,
                    "type": "optional",
                },
                {
                    "id": "hermes",
                    "label": "Hermes",
                    "status": "OFF_BY_POLICY",
                    "port": 8003,
                    "type": "optional",
                },
                {
                    "id": "hormiguero",
                    "label": "Hormiguero",
                    "status": "OFF_BY_POLICY",
                    "port": 8004,
                    "type": "optional",
                },
                {
                    "id": "spawner",
                    "label": "Spawner",
                    "status": "OFF_BY_POLICY",
                    "port": 8006,
                    "type": "optional",
                },
            ],
            "edges": [
                {"from": "tentaculo_link", "to": "madre", "label": "proxy"},
                {"from": "tentaculo_link", "to": "redis", "label": "cache"},
                {"from": "madre", "to": "redis", "label": "state"},
            ],
        },
        "policy_note": "solo_madre: Only core services up. Optional services OFF_BY_POLICY (not an error).",
    }


@app.get("/operator/api/audit", tags=["operator-api-p0"])
async def operator_api_audit(_: bool = Depends(token_guard)):
    """
    P0: List audit runs (placeholder for P1+ persistence).
    Currently returns empty list or recent runs from runtime memory.
    """
    return {
        "runs": [],
        "total": 0,
        "note": "Audit storage P1+ feature (currently no persistence)",
    }


@app.get("/operator/api/audit/{run_id}", tags=["operator-api-p0"])
async def operator_api_audit_detail(run_id: str, _: bool = Depends(token_guard)):
    """
    P0: Get details of a specific audit run by ID (placeholder).
    """
    return {
        "error": "run_not_found",
        "run_id": run_id,
        "note": "Audit storage P1+ feature",
    }


@app.get("/operator/api/audit/{run_id}/download", tags=["operator-api-p0"])
async def operator_api_audit_download(run_id: str, _: bool = Depends(token_guard)):
    """
    P0: Download audit run as JSON (placeholder).
    """
    return {
        "error": "run_not_found",
        "run_id": run_id,
        "note": "Audit download P1+ feature",
    }


@app.get("/operator/api/settings", tags=["operator-api-p0"])
async def operator_api_settings(_: bool = Depends(token_guard)):
    """
    P0: Get current operator settings (UI preferences).
    Returns default settings on first call.
    """
    return {
        "appearance": {"theme": "dark", "language": "en"},
        "chat": {"model": "deepseek-r1", "temperature": 0.7},
        "security": {"enable_api_logs": False, "enable_debug_mode": False},
        "notifications": {"enable_events": True, "events_level": "info"},
    }


@app.post("/operator/api/settings", tags=["operator-api-p0"])
async def operator_api_settings_update(settings: dict, _: bool = Depends(token_guard)):
    """
    P0: Update operator settings (UI preferences).
    Returns updated settings (no persistence in solo_madre).
    """
    return {
        "status": "ok",
        "message": "Settings updated (not persisted in solo_madre mode)",
        "settings": settings,
    }


@app.api_route(
    "/operator/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    tags=["operator-api-fallback"],
)
async def operator_api_fallback(path: str, _: bool = Depends(token_guard)):
    """
    Fallback for unmatched /operator/api/* paths.
    Returns 404 with helpful message (not 500).
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "endpoint_not_found",
            "path": f"/operator/api/{path}",
            "available_endpoints": [
                "GET  /operator/api/status",
                "GET  /operator/api/modules",
                "POST /operator/api/chat",
                "GET  /operator/api/events",
                "GET  /operator/api/scorecard",
                "GET  /operator/api/topology",
            ],
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
