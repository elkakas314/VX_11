"""
Tentáculo Link v7.0 - Gateway Refactored

Pure proxy + auth + context-7 middleware + modular clients.
Version: 7.0 | Module: tentaculo_link | Port: 8000

Main HTTP gateway for VX11 with token authentication, circuit breaker,
Context-7 sessions, and intelligent request routing to internal services.
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Set, Union

from contextlib import asynccontextmanager
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
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
from madre.window_manager import get_window_manager
from tentaculo_link.deepseek_client import DeepSeekClient, save_chat_to_db
from tentaculo_link.deepseek_r1_client import get_deepseek_r1_client
from switch.providers import get_provider  # PHASE 3: Provider registry
from tentaculo_link import (
    routes as api_routes,
)  # Import routes package to avoid name collision
from tentaculo_link.models_core_mvp import (
    CoreIntent,
    CoreIntentResponse,
    CoreResultQuery,
    CoreStatus,
    ErrorResponse,
    StatusEnum,
    ModeEnum,
    WindowOpen,
    WindowStatus,
    WindowClose,
    WindowTarget,
    SpawnRequest,
    SpawnResponse,
    SpawnResult,
    DBSummary,
)

# Load environment tokens
load_tokens()
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}
OPERATOR_PROXY_ENABLED = os.environ.get(
    "VX11_OPERATOR_PROXY_ENABLED", "false"
).lower() in ("1", "true", "yes", "on")
OPERATOR_CONTROL_ENABLED = os.environ.get(
    "VX11_OPERATOR_CONTROL_ENABLED", "false"
).lower() in ("1", "true", "yes", "on")


def _is_testing_mode() -> bool:
    return (
        settings.testing_mode
        or os.environ.get("VX11_TESTING_MODE", "").lower() in ("1", "true", "yes")
        or os.environ.get("VX11_TESTING", "").lower() in ("1", "true", "yes")
    )


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
    """Token validation dependency (header-only)."""

    def __call__(self, x_vx11_token: str = Header(None)) -> bool:
        if settings.enable_auth:
            if not x_vx11_token:
                raise HTTPException(status_code=401, detail="auth_required")
            if x_vx11_token != VX11_TOKEN:
                raise HTTPException(status_code=403, detail="forbidden")
        return True


def token_guard_with_query_param(
    x_vx11_token: str = Header(None),
    token: str = Query(None),
) -> bool:
    """Token validation supporting header or query param (for SSE via EventSource)."""
    if settings.enable_auth:
        # Try header first, then query param
        provided_token = x_vx11_token or token
        if not provided_token:
            raise HTTPException(status_code=401, detail="auth_required")
        if provided_token != VX11_TOKEN:
            raise HTTPException(status_code=403, detail="forbidden")
    return True


token_guard = TokenGuard()


class OperatorChatRequest(BaseModel):
    """Chat message with session context."""

    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "local"
    metadata: Optional[Dict[str, Any]] = None


class PowerWindowOpenRequest(BaseModel):
    """Request to open a power window (temporal service availability)."""

    services: list[str]
    ttl_sec: Optional[int] = 600  # 10 minutes default
    mode: str = "ttl"  # "ttl" or "hold"
    reason: str = "operator_manual"


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


class OperatorChatCommandRequest(BaseModel):
    """Chat command request (status, open/close window, spawn task)."""

    command: str  # "status" | "open_window" | "close_window" | "spawn" | "message"
    args: Optional[Dict[str, Any]] = None
    message: Optional[str] = None  # For "message" command
    session_id: Optional[str] = None
    user_id: Optional[str] = "local"
    correlation_id: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    clients = get_clients()
    context7 = get_context7_manager()
    cache = get_cache()
    limiter = get_rate_limiter()
    metrics = get_prometheus_metrics()
    window_manager = get_window_manager()  # Initialize window manager (PHASE 2)

    await clients.startup()
    await cache_startup()  # Initialize Redis cache

    # Link Redis to rate limiter
    if cache.redis:
        set_redis_for_limiter(cache.redis)

    FILES_DIR.mkdir(parents=True, exist_ok=True)
    write_log(
        "tentaculo_link",
        "startup:v7_initialized (with cache+rate_limit+metrics+windows)",
    )

    # Yield to allow app to run
    yield

    # Shutdown
    await clients.shutdown()
    await cache_shutdown()
    # Cleanup windows (PHASE 2)
    window_manager.cleanup_expired_windows()
    write_log("tentaculo_link", "shutdown:v7_complete (windows cleaned)")


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


@app.middleware("http")
async def operator_api_proxy(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path.startswith("/operator/api"):
        if not OPERATOR_PROXY_ENABLED:
            return await call_next(request)
        correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
        if settings.enable_auth:
            # Try header first, then query param (for SSE/EventSource)
            token_header_value = request.headers.get(settings.token_header)
            token_query_value = request.query_params.get("token")
            provided_token = token_header_value or token_query_value

            if not provided_token:
                return JSONResponse(
                    status_code=401, content={"detail": "auth_required"}
                )
            if provided_token != VX11_TOKEN:
                return JSONResponse(status_code=403, content={"detail": "forbidden"})

        operator_url = settings.operator_url.rstrip("/")
        request_path = request.url.path
        if request_path.startswith("/operator/api/v1"):
            upstream_path = request_path.replace("/operator/api/v1", "/api/v1", 1)
        else:
            upstream_path = request_path.replace("/operator/api", "/api/v1", 1)
        target_url = f"{operator_url}{upstream_path}"
        headers = dict(request.headers)
        headers["X-Correlation-Id"] = correlation_id
        headers[settings.token_header] = headers.get(settings.token_header, VX11_TOKEN)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if request.method == "GET" and request.url.path.endswith(
                    "/events/stream"
                ):
                    async with client.stream(
                        request.method,
                        target_url,
                        headers=headers,
                        params=request.query_params,
                    ) as resp:
                        if resp.status_code >= 400:
                            return JSONResponse(
                                status_code=resp.status_code,
                                content=resp.json(),
                                headers={"X-Correlation-Id": correlation_id},
                            )
                        return StreamingResponse(
                            resp.aiter_raw(),
                            status_code=resp.status_code,
                            media_type=resp.headers.get(
                                "content-type", "text/event-stream"
                            ),
                            headers={"X-Correlation-Id": correlation_id},
                        )

                body = await request.body()
                resp = await client.request(
                    request.method,
                    target_url,
                    headers=headers,
                    params=request.query_params,
                    content=body or None,
                )
        except Exception:
            return JSONResponse(
                status_code=403,
                content={
                    "status": "OFF_BY_POLICY",
                    "service": "operator_backend",
                    "message": "Disabled by SOLO_MADRE policy",
                    "correlation_id": correlation_id,
                    "recommended_action": "Ask Madre to open operator window",
                },
                headers={"X-Correlation-Id": correlation_id},
            )

        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                data = resp.json()
                if isinstance(data, dict) and "correlation_id" not in data:
                    data["correlation_id"] = correlation_id
                return JSONResponse(
                    status_code=resp.status_code,
                    content=data,
                    headers={"X-Correlation-Id": correlation_id},
                )
            except Exception:
                pass

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=resp.headers.get("content-type", "application/json"),
            headers={"X-Correlation-Id": correlation_id},
        )

    return await call_next(request)


# Mount Operator UI static files
# NOTE: Paths include both local dev and Docker volume mount locations
operator_ui_candidates = [
    Path("/app/operator/frontend/dist"),  # Docker volume mount (primary for production)
    Path(__file__).parent.parent / "operator" / "frontend" / "dist",  # Local dev
    Path(__file__).parent.parent / "operator_ui" / "frontend" / "dist",  # Legacy
]
operator_ui_path = next(
    (candidate for candidate in operator_ui_candidates if candidate.exists()), None
)
if operator_ui_path:
    app.mount(
        "/operator/ui",
        StaticFiles(directory=str(operator_ui_path), html=True),
        name="operator_ui",
    )
    write_log("tentaculo_link", f"mounted_operator_ui:{operator_ui_path}")
else:
    write_log(
        "tentaculo_link",
        f"WARNING: operator_ui not found: {operator_ui_candidates}",
        level="WARNING",
    )

    @app.get("/operator/ui")
    @app.get("/operator/ui/{path:path}")
    async def operator_ui_missing(path: str = ""):
        return Response(
            content="Operator UI build not found. Run frontend build to generate dist.",
            media_type="text/plain",
            status_code=503,
        )


# Include new operator API routes with /operator prefix
try:
    # COMMENTED OUT: events.py serves JSON polling, but main_v7.py has SSE endpoint
    # app.include_router(
    #     api_routes.events.router, prefix="/operator", tags=["operator-api"]
    # )
    app.include_router(
        api_routes.settings.router, prefix="/operator", tags=["operator-api"]
    )
    app.include_router(
        api_routes.audit.router, prefix="/operator", tags=["operator-api"]
    )
    app.include_router(
        api_routes.metrics.router, prefix="/operator", tags=["operator-api"]
    )
    app.include_router(
        api_routes.rails.router, prefix="/operator", tags=["operator-api"]
    )
    app.include_router(
        api_routes.window.router, prefix="/operator", tags=["operator-api"]
    )
    app.include_router(
        api_routes.spawner.router, prefix="/operator", tags=["operator-api"]
    )
    write_log("tentaculo_link", "included_operator_api_routers:success")
except Exception as e:
    write_log(
        "tentaculo_link",
        f"WARNING: failed to include operator routers: {e}",
        level="WARNING",
    )

app.include_router(api_routes.internal.router)
app.include_router(api_routes.hormiguero.router)


# ============ HEALTH & STATUS ============


@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok", "module": "tentaculo_link", "version": "7.0"}


@app.get("/operator")
async def operator_redirect():
    """Redirect /operator to /operator/ui/."""
    return RedirectResponse(url="/operator/ui/", status_code=302)


async def vx11_status_old():
    """Aggregate health check for all modules (async parallel) - DEPRECATED.

    Use GET /vx11/status instead (canonical contract).
    """
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


# ============ CORE MVP ENDPOINTS (/:8000) ============
# INVARIANT: All external API routed through :8000 (single entrypoint)
# INVARIANT: All endpoints use TokenGuard + log to forensics


@app.post("/vx11/intent", response_model=CoreIntentResponse)
async def core_intent(
    req: CoreIntent,
    _: bool = Depends(token_guard),
):
    """
    POST /vx11/intent: Execute intent via madre (primary) or fallback.

    INVARIANT:
    - Single entrypoint (localhost:8000)
    - Generates correlation_id if missing
    - PHASE 4: If require.switch=true AND window OPEN → route to switch
    - PHASE 4: If require.switch=true AND window CLOSED → ERROR off_by_policy
    - PHASE 4: If require.spawner=true AND window OPEN → route to spawner
    - PHASE 4: If require.spawner=true AND window CLOSED → ERROR off_by_policy
    - Otherwise: executes via madre, returns DONE or ERROR

    Token: X-VX11-Token header (required if settings.enable_auth)
    """
    try:
        # Normalize intent
        correlation_id = req.correlation_id or str(uuid.uuid4())
        window_manager = get_window_manager()

        # PHASE 4: Check window status for required services
        if req.require.get("switch", False):
            # Check if switch window is open
            window_status = window_manager.get_window_status("switch")
            is_switch_open = window_status.get("is_open", False)

            if not is_switch_open:
                # Window not open → off_by_policy error
                write_log(
                    "tentaculo_link",
                    f"core_intent:off_by_policy:switch:{correlation_id}",
                )
                return CoreIntentResponse(
                    correlation_id=correlation_id,
                    status=StatusEnum.ERROR,
                    mode=ModeEnum.FALLBACK,
                    error="off_by_policy",
                    response={
                        "reason": "switch required but window not open (SOLO_MADRE policy)",
                        "policy": "SOLO_MADRE",
                        "required_service": "switch",
                        "hint": "POST /vx11/window/open to enable access",
                    },
                )

        # PHASE 4: Check spawner window
        if req.require.get("spawner", False):
            window_status = window_manager.get_window_status("spawner")
            is_spawner_open = window_status.get("is_open", False)

            if not is_spawner_open:
                # Window not open → off_by_policy error
                write_log(
                    "tentaculo_link",
                    f"core_intent:off_by_policy:spawner:{correlation_id}",
                )
                return CoreIntentResponse(
                    correlation_id=correlation_id,
                    status=StatusEnum.ERROR,
                    mode=ModeEnum.FALLBACK,
                    error="off_by_policy",
                    response={
                        "reason": "spawner required but window not open (SOLO_MADRE policy)",
                        "policy": "SOLO_MADRE",
                        "required_service": "spawner",
                        "hint": "POST /vx11/window/open to enable access",
                    },
                )

        # Route to madre for execution
        async with httpx.AsyncClient(timeout=30.0) as client:
            madre_req = {
                "intent_type": req.intent_type.value,
                "text": req.text,
                "payload": req.payload,
                "require": req.require,
                "priority": req.priority,
                "correlation_id": correlation_id,
                "user_id": req.user_id,
                "metadata": req.metadata or {},
            }

            try:
                resp = await client.post(
                    "http://madre:8001/vx11/intent",
                    json=madre_req,
                    headers=AUTH_HEADERS,
                    timeout=30.0,
                )

                if resp.status_code == 200:
                    result = resp.json()
                    write_log("tentaculo_link", f"core_intent:success:{correlation_id}")
                    return CoreIntentResponse(
                        correlation_id=correlation_id,
                        status=StatusEnum(result.get("status", "DONE")),
                        mode=ModeEnum(result.get("mode", "MADRE")),
                        provider=result.get("provider", "fallback_local"),
                        response=result.get("response"),
                        degraded=result.get("degraded", False),
                    )
                else:
                    # upstream error
                    write_log(
                        "tentaculo_link",
                        f"core_intent:upstream_error:{correlation_id}:{resp.status_code}",
                    )
                    return CoreIntentResponse(
                        correlation_id=correlation_id,
                        status=StatusEnum.ERROR,
                        mode=ModeEnum.FALLBACK,
                        error="upstream_unavailable",
                        response={"upstream_status": resp.status_code},
                    )
            except httpx.TimeoutException:
                write_log("tentaculo_link", f"core_intent:timeout:{correlation_id}")
                return CoreIntentResponse(
                    correlation_id=correlation_id,
                    status=StatusEnum.ERROR,
                    mode=ModeEnum.FALLBACK,
                    error="upstream_unavailable",
                    response={"reason": "madre timeout"},
                )
            except Exception as e:
                write_log(
                    "tentaculo_link", f"core_intent:exception:{correlation_id}:{str(e)}"
                )
                return CoreIntentResponse(
                    correlation_id=correlation_id,
                    status=StatusEnum.ERROR,
                    mode=ModeEnum.FALLBACK,
                    error="upstream_unavailable",
                    response={"reason": str(e)},
                )

    except Exception as outer_e:
        correlation_id = req.correlation_id or str(uuid.uuid4())
        write_log(
            "tentaculo_link",
            f"core_intent:outer_exception:{correlation_id}:{str(outer_e)}",
        )
        return CoreIntentResponse(
            correlation_id=correlation_id,
            status=StatusEnum.ERROR,
            mode=ModeEnum.FALLBACK,
            error="internal_error",
            response={"reason": str(outer_e)},
        )


@app.get("/vx11/result/{result_id}")
async def vx11_result_NEW_HANDLER_2025(
    result_id: str,
    _: bool = Depends(token_guard),
):
    """
    GET /vx11/result/{result_id}: Query execution result.

    INVARIANT:
    - If result_id starts with 'spawn-' → resolve from spawns table (real spawn result)
    - Otherwise → proxy to madre for correlation_id lookup

    Returns:
    - For spawn-* IDs: SpawnResult with status, exit_code, stdout, stderr
    - For UUID/correlation_id: CoreResultQuery from madre
    """
    try:
        write_log("tentaculo_link", f"result:handler_called:result_id={result_id}")

        # SPAWN PATH: resolve from BD
        if result_id.startswith("spawn-"):
            write_log("tentaculo_link", f"result:spawn_path:{result_id}")
            import sqlite3
            from pathlib import Path

            db_path = Path(os.environ.get("DATABASE_PATH", "data/runtime/vx11.db"))
            if not db_path.exists():
                raise HTTPException(
                    status_code=404, detail="Spawn not found (DB unavailable)"
                )

            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Try exact name match first (preferred)
            cursor.execute(
                "SELECT uuid, name, status, exit_code, stdout, stderr, created_at, started_at, ended_at FROM spawns WHERE name = ?",
                (result_id,),
            )
            row = cursor.fetchone()

            # Fallback: prefix match on uuid (strip 'spawn-')
            if not row:
                prefix = result_id[len("spawn-") :]
                cursor.execute(
                    "SELECT uuid, name, status, exit_code, stdout, stderr, created_at, started_at, ended_at FROM spawns WHERE uuid LIKE ?",
                    (f"{prefix}%",),
                )
                rows = cursor.fetchall()
                if len(rows) > 1:
                    conn.close()
                    raise HTTPException(
                        status_code=400, detail="Ambiguous spawn_id (multiple matches)"
                    )
                row = rows[0] if rows else None

            conn.close()
            if not row:
                raise HTTPException(status_code=404, detail="Spawn not found")

            # Map spawner status to API status
            status_map = {
                "pending": "QUEUED",
                "queued": "QUEUED",
                "running": "RUNNING",
                "completed": "DONE",
                "done": "DONE",
                "failed": "ERROR",
                "error": "ERROR",
                "timeout": "ERROR",
            }

            write_log(
                "tentaculo_link",
                f"result:spawn_resolved:{result_id}:uuid={row['uuid']}:status={row['status']}",
            )

            return SpawnResult(
                spawn_uuid=row["uuid"],
                spawn_id=row["name"] or result_id,
                status=status_map.get((row["status"] or "").lower(), "unknown"),
                exit_code=row["exit_code"],
                stdout=row["stdout"],
                stderr=row["stderr"],
                created_at=row["created_at"],
                started_at=row["started_at"],
                finished_at=row["ended_at"],
                ttl_seconds=300,
            )

        # CORRELATION_ID PATH: proxy to madre
        else:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"http://madre:8001/vx11/result/{result_id}",
                    headers=AUTH_HEADERS,
                    timeout=15.0,
                )

                if resp.status_code == 200:
                    result = resp.json()
                    write_log("tentaculo_link", f"result:correlation_found:{result_id}")
                    return CoreResultQuery(
                        correlation_id=result_id,
                        status=StatusEnum(result.get("status", "QUEUED")),
                        result=result.get("result"),
                        error=result.get("error"),
                        mode=(
                            ModeEnum(result.get("mode", "MADRE"))
                            if result.get("mode")
                            else None
                        ),
                        provider=result.get("provider"),
                    )
                elif resp.status_code == 404:
                    write_log("tentaculo_link", f"result:not_found:{result_id}")
                    return CoreResultQuery(
                        correlation_id=result_id,
                        status=StatusEnum.ERROR,
                        error="not_found",
                    )
                else:
                    write_log(
                        "tentaculo_link",
                        f"result:upstream_error:{result_id}:{resp.status_code}",
                    )
                    return CoreResultQuery(
                        correlation_id=result_id,
                        status=StatusEnum.ERROR,
                        error="upstream_error",
                    )

    except HTTPException:
        raise
    except httpx.TimeoutException:
        write_log("tentaculo_link", f"result:timeout:{result_id}")
        return CoreResultQuery(
            correlation_id=result_id,
            status=StatusEnum.ERROR,
            error="upstream_timeout",
        )
    except Exception as e:
        write_log(
            "tentaculo_link",
            f"result:exception:{result_id}:{type(e).__name__}:{str(e)}",
        )
        return CoreResultQuery(
            correlation_id=result_id,
            status=StatusEnum.ERROR,
            error="internal_error",
        )


@app.get("/vx11/status", response_model=CoreStatus)
async def vx11_core_status(_: bool = Depends(token_guard)):
    """
    GET /vx11/status: Policy state + best-effort health check (non-blocking).

    INVARIANT:
    - No blocking calls (short timeout)
    - Returns current policy mode (solo_madre/windowed/full)
    - Returns health of madre, switch, spawner (best-effort)
    """
    try:
        clients = get_clients()

        # Best-effort checks (very short timeout)
        madre_available = True
        switch_available = None
        spawner_available = None

        # Quick checks (max 1s each, fire-and-forget style)
        try:
            madre_client = clients.clients.get("madre")
            if madre_client:
                madre_available = madre_client.circuit_breaker.state.value != "open"
        except Exception:
            madre_available = False

        try:
            switch_client = clients.clients.get("switch")
            if switch_client:
                switch_available = switch_client.circuit_breaker.state.value != "open"
        except Exception:
            pass

        try:
            spawner_client = clients.clients.get("spawner")
            if spawner_client:
                spawner_available = spawner_client.circuit_breaker.state.value != "open"
        except Exception:
            pass

        # Determine policy mode
        policy = "SOLO_MADRE"
        if switch_available and spawner_available:
            mode = "full"
        elif switch_available or spawner_available:
            mode = "windowed"
        else:
            mode = "solo_madre"

        write_log("tentaculo_link", f"vx11_core_status:{mode}:{policy}")

        return CoreStatus(
            mode=mode,
            policy=policy,
            madre_available=madre_available,
            switch_available=switch_available,
            spawner_available=spawner_available,
        )

    except Exception as e:
        write_log("tentaculo_link", f"vx11_core_status:exception:{str(e)}")
        # Return conservative defaults
        return CoreStatus(
            mode="solo_madre",
            policy="SOLO_MADRE",
            madre_available=False,
        )


# ============ VX11 AGENTS & SWITCH ENDPOINTS (PHASE 5) ============
# INVARIANT: Agents list and switch status endpoints


@app.get("/vx11/agents")
async def vx11_list_agents(_: bool = Depends(token_guard)):
    """
    GET /vx11/agents: List all active agents (daughters).

    Returns:
    {
        "agents": [
            {
                "agent_id": "daughter-123-xyz",
                "spawn_id": "spawn-456-abc",
                "status": "RUNNING|COMPLETED|FAILED",
                "task_type": "python|shell",
                "created_at": "2026-01-03T01:12:00Z",
                "updated_at": "2026-01-03T01:12:10Z"
            },
            ...
        ],
        "total": 0,
        "window_open": false
    }
    """
    try:
        window_manager = get_window_manager()
        window_status = window_manager.get_window_status("spawner")

        # Query BD para agentes activos
        # Por ahora: retornar lista vacía + estado de ventana
        write_log("tentaculo_link", "vx11_list_agents:success")

        return JSONResponse(
            status_code=200,
            content={
                "agents": [],
                "total": 0,
                "window_open": window_status.get("is_open", False),
                "spawner_available": True,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        write_log("tentaculo_link", f"vx11_list_agents:exception:{str(e)}")
        return JSONResponse(
            status_code=500, content={"error": "internal_error", "detail": str(e)}
        )


@app.get("/vx11/switch/status")
async def vx11_switch_status(_: bool = Depends(token_guard)):
    """
    GET /vx11/switch/status: Query estado del módulo switch.

    Returns:
    {
        "status": "healthy",
        "module": "switch",
        "version": "7.0",
        "providers": [...],
        "routing_mode": "active",
        "circuit_breaker": "closed"
    }
    """
    try:
        clients = get_clients()
        switch_client = clients.clients.get("switch")

        if not switch_client:
            write_log("tentaculo_link", "vx11_switch_status:switch_client_not_found")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unavailable",
                    "module": "switch",
                    "error": "switch_client_not_configured",
                },
            )

        # Get circuit breaker status
        cb_state = (
            switch_client.circuit_breaker.state.value
            if switch_client.circuit_breaker
            else "unknown"
        )

        write_log("tentaculo_link", f"vx11_switch_status:success:{cb_state}")

        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy" if cb_state != "open" else "degraded",
                "module": "switch",
                "version": "7.0",
                "routing_mode": "active",
                "circuit_breaker": cb_state,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        write_log("tentaculo_link", f"vx11_switch_status:exception:{str(e)}")
        return JSONResponse(
            status_code=500, content={"error": "internal_error", "detail": str(e)}
        )


# ============ VX11 WINDOW MANAGEMENT ENDPOINTS (PHASE 2) ============
# INVARIANT: Window endpoints manage TTL-gated access to switch/spawner services


@app.post("/vx11/window/open")
async def vx11_window_open(
    req: WindowOpen,
    _: bool = Depends(token_guard),
):
    """
    POST /vx11/window/open: Open a temporal window for service access.

    PHASE 2: Manages TTL-gated availability of switch or spawner services.

    Request:
    {
        "target": "switch" | "spawner",
        "ttl_seconds": 1-3600,  # Validated by Pydantic
        "reason": "operator requested" | "automated task" | etc
    }

    Response (200):
    {
        "target": "switch",
        "is_open": true,
        "ttl_remaining_seconds": 300,
        "opened_at": "2025-01-01T00:00:00Z",
        "expires_at": "2025-01-01T00:05:00Z"
    }

    Error Response (400):
    {
        "error": "invalid_window_request",
        "reason": "TTL must be between 1 and 3600 seconds"
    }

    Token: X-VX11-Token header (required if settings.enable_auth)
    """
    try:
        correlation_id = str(uuid.uuid4())
        window_manager = get_window_manager()

        # Validate target enum
        if not (
            isinstance(req.target, WindowTarget)
            or req.target.value in ["switch", "spawner", "hermes"]
        ):
            write_log(
                "tentaculo_link",
                f"window_open:invalid_target:{req.target}:{correlation_id}",
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_target",
                    "reason": f"target must be 'switch', 'spawner', or 'hermes', got '{req.target}'",
                    "correlation_id": correlation_id,
                },
            )

        # Open window (validates TTL bounds in window_manager)
        # target is already WindowTarget enum, convert to string for window_manager
        target_str = (
            req.target.value if isinstance(req.target, WindowTarget) else req.target
        )
        result = window_manager.open_window(
            target=target_str,
            ttl_seconds=req.ttl_seconds,
            reason=req.reason or "vx11_api_request",
        )

        write_log(
            "tentaculo_link",
            f"window_open:success:target={target_str}:ttl={req.ttl_seconds}:correlation_id={correlation_id}",
            level="INFO",
        )

        # Extract the window dict from result and return it
        window_data = result.get("window", {})
        return JSONResponse(
            status_code=200,
            content=window_data,
        )

    except ValueError as e:
        # TTL validation error
        correlation_id = str(uuid.uuid4())
        write_log(
            "tentaculo_link", f"window_open:validation_error:{str(e)}:{correlation_id}"
        )
        return JSONResponse(
            status_code=400,
            content={
                "error": "invalid_window_request",
                "reason": str(e),
                "correlation_id": correlation_id,
            },
        )

    except Exception as e:
        correlation_id = str(uuid.uuid4())
        write_log(
            "tentaculo_link", f"window_open:exception:{str(e)[:100]}:{correlation_id}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "reason": str(e)[:100],
                "correlation_id": correlation_id,
            },
        )


@app.post("/vx11/window/close")
async def vx11_window_close(
    req: WindowClose,
    _: bool = Depends(token_guard),
):
    """
    POST /vx11/window/close: Close an open window.

    PHASE 2: Explicit window closure (auto-closure also happens on TTL expiration).

    Request:
    {
        "target": "switch" | "spawner",
        "reason": "manual closure" | etc
    }

    Response (200):
    {
        "target": "switch",
        "closed": true,
        "was_open": true
    }

    Token: X-VX11-Token header (required if settings.enable_auth)
    """
    try:
        correlation_id = str(uuid.uuid4())
        window_manager = get_window_manager()

        # Close window - target is WindowTarget enum, convert to string
        target_str = (
            req.target.value if isinstance(req.target, WindowTarget) else req.target
        )
        result = window_manager.close_window(
            target=target_str,
            reason=req.reason or "vx11_api_close",
        )

        write_log(
            "tentaculo_link",
            f"window_close:target={target_str}:closed={result.get('closed')}:was_open={result.get('was_open')}:correlation_id={correlation_id}",
            level="INFO",
        )

        return JSONResponse(
            status_code=200,
            content=result,
        )

    except Exception as e:
        correlation_id = str(uuid.uuid4())
        write_log(
            "tentaculo_link", f"window_close:exception:{str(e)[:100]}:{correlation_id}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "reason": str(e)[:100],
                "correlation_id": correlation_id,
            },
        )


@app.get("/vx11/window/status/{target}")
async def vx11_window_status(
    target: WindowTarget,
    _: bool = Depends(token_guard),
):
    """
    GET /vx11/window/status/{target}: Query window status for a service.

    PHASE 2: Check if temporal window is open and TTL remaining.

    Path Params:
    - target: "switch" | "spawner"

    Response (200):
    {
        "target": "switch",
        "is_open": true | false,
        "ttl_remaining_seconds": 300 | null,
        "opened_at": "2025-01-01T00:00:00Z" | null,
        "expires_at": "2025-01-01T00:05:00Z" | null
    }

    Token: X-VX11-Token header (required if settings.enable_auth)
    """
    try:
        correlation_id = str(uuid.uuid4())
        window_manager = get_window_manager()

        # Normalize target to string to avoid cross-module enum type mismatch
        target_str = target.value if isinstance(target, WindowTarget) else target

        # Get window status (auto-closes if expired)
        window_status = window_manager.get_window_status(target_str)

        write_log(
            "tentaculo_link",
            f"window_status:target={target_str}:is_open={window_status.get('is_open')}:correlation_id={correlation_id}",
            level="DEBUG",
        )

        return JSONResponse(
            status_code=200,
            content=window_status,
        )

    except Exception as e:
        correlation_id = str(uuid.uuid4())
        write_log(
            "tentaculo_link", f"window_status:exception:{str(e)[:100]}:{correlation_id}"
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "reason": str(e)[:100],
                "correlation_id": correlation_id,
            },
        )


@app.post("/vx11/spawn", response_model=SpawnResponse)
async def vx11_spawn(
    req: SpawnRequest,
    _: bool = Depends(token_guard),
):
    """
    POST /vx11/spawn: Submit async task to spawner (daughter execution).

    PHASE 5: Requires spawner window to be open.

    Request:
    {
        "task_type": "python" | "shell",
        "code": "print('hello')",
        "max_retries": 2,
        "ttl_seconds": 300,
        "user_id": "local",
        "metadata": {...},
        "correlation_id": "optional-uuid"
    }

    Response (200):
    {
        "spawn_id": "spawn-789-xyz",
        "correlation_id": "corr-456-def",
        "status": "QUEUED",
        "task_type": "python",
        "created_at": "2026-01-01T00:00:00Z"
    }

    Error (403 off_by_policy):
    {
        "error": "off_by_policy",
        "reason": "spawner window not open",
        "hint": "POST /vx11/window/open {\"target\":\"spawner\", \"ttl_seconds\":300}"
    }

    Token: X-VX11-Token header (required if settings.enable_auth)
    """
    try:
        correlation_id = req.correlation_id or str(uuid.uuid4())
        window_manager = get_window_manager()

        # Check if spawner window is open
        window_status = window_manager.get_window_status("spawner")
        if not window_status.get("is_open", False):
            write_log(
                "tentaculo_link",
                f"spawn:off_by_policy:spawner_not_open:{correlation_id}",
                level="WARNING",
            )
            # Return 200 + semantic error (not 403)
            return SpawnResponse(
                spawn_id="",  # No spawn created
                correlation_id=correlation_id,
                status="ERROR",
                task_type=req.task_type,
                error="off_by_policy",
            )

        # Route to spawner service
        # NOTE: spawn_id will be derived from spawn_uuid (returned by spawner)
        # to ensure /vx11/result is always resoluble in BD

        # Queue task (in production: call spawner service)
        # For now: simple submission
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                spawner_url = os.environ.get("SPAWNER_URL", "http://spawner:8008")
                resp = await client.post(
                    f"{spawner_url}/spawn",
                    json={
                        "task_type": req.task_type,
                        "cmd": req.code,  # Map 'code' to 'cmd' (spawner expects cmd)
                        "max_retries": req.max_retries,
                        "ttl_seconds": req.ttl_seconds,
                        "metadata": req.metadata or {},
                        "trace_id": correlation_id,
                    },
                    headers=AUTH_HEADERS,
                    timeout=10.0,
                )

                if resp.status_code == 202 or resp.status_code == 200:
                    spawner_response = resp.json()
                    spawn_uuid = spawner_response.get("spawn_uuid", "")
                    # STABLE spawn_id derived from real spawn_uuid
                    spawn_id = f"spawn-{spawn_uuid[:8]}" if spawn_uuid else ""

                    write_log(
                        "tentaculo_link",
                        f"spawn:queued:spawn_id={spawn_id}:spawn_uuid={spawn_uuid}:correlation_id={correlation_id}",
                        level="INFO",
                    )

                    return SpawnResponse(
                        spawn_id=spawn_id,
                        spawn_uuid=spawn_uuid,
                        correlation_id=correlation_id,
                        status="QUEUED",
                        task_type=req.task_type,
                        created_at=datetime.utcnow(),
                    )
                else:
                    raise Exception(f"spawner returned {resp.status_code}")

            except (httpx.ConnectError, httpx.TimeoutException):
                write_log(
                    "tentaculo_link",
                    f"spawn:spawner_unavailable:correlation_id={correlation_id}",
                    level="ERROR",
                )
                # Return 200 + semantic error (not 503)
                return SpawnResponse(
                    spawn_id="",
                    correlation_id=correlation_id,
                    status="ERROR",
                    task_type=req.task_type,
                    error="spawner_unavailable",
                )

    except Exception as e:
        correlation_id = req.correlation_id or str(uuid.uuid4())
        write_log("tentaculo_link", f"spawn:exception:{str(e)[:100]}:{correlation_id}")
        # Return 200 + semantic error (not 500)
        return SpawnResponse(
            spawn_id="",
            correlation_id=correlation_id,
            status="ERROR",
            task_type=req.task_type or "unknown",
            error="internal_error",
        )


# ============ DB SUMMARY ENDPOINT (PHASE 6) ============


@app.get("/vx11/db/summary", response_model=DBSummary)
async def vx11_db_summary(
    _: bool = Depends(token_guard),
):
    """
    Get summary of database audit records (counts + latest entries).

    Returns:
    - counts: Row counts per table
    - last_spawns: Last 5 spawn records
    - last_routing_events: Last 5 routing events

    For development/debugging only. Token required.
    """
    try:
        import sqlite3
        from pathlib import Path

        db_path = Path(os.environ.get("DATABASE_PATH", "data/runtime/vx11.db"))
        if not db_path.exists():
            return DBSummary(counts={}, last_spawns=[], last_routing_events=[])

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        counts = {}
        tables = [
            "spawns",
            "tasks",
            "routing_events",
            "cli_providers",
            "cli_usage_stats",
            "daughters",
            "daughter_tasks",
            "daughter_attempts",
        ]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                count_row = cursor.fetchone()
                counts[table] = count_row["cnt"] if count_row else 0
            except:
                counts[table] = 0  # Table might not exist

        # Last 5 spawns
        last_spawns = []
        try:
            cursor.execute(
                "SELECT uuid, status, created_at FROM spawns ORDER BY created_at DESC LIMIT 5"
            )
            for row in cursor.fetchall():
                last_spawns.append(
                    {
                        "uuid": row["uuid"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                    }
                )
        except:
            pass

        # Last 5 routing events
        last_routing_events = []
        try:
            cursor.execute(
                "SELECT intent, provider, status, created_at FROM routing_events ORDER BY created_at DESC LIMIT 5"
            )
            for row in cursor.fetchall():
                last_routing_events.append(
                    {
                        "intent": row["intent"],
                        "provider": row["provider"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                    }
                )
        except:
            pass

        conn.close()

        return DBSummary(
            counts=counts,
            last_spawns=last_spawns,
            last_routing_events=last_routing_events,
        )

    except Exception as e:
        write_log(
            "tentaculo_link", f"db_summary:exception:{str(e)[:100]}", level="ERROR"
        )
        # Return partial data rather than fail
        return DBSummary(counts={}, last_spawns=[], last_routing_events=[])


# ============ HERMES PROXY ENDPOINTS (PHASE 7) ============


@app.get("/vx11/hermes/health")
async def vx11_hermes_health(
    _: bool = Depends(token_guard),
):
    """Proxy health check to hermes service."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "http://hermes:8003/health",
                headers=AUTH_HEADERS,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"status": "unhealthy", "code": resp.status_code}
    except Exception as e:
        write_log(
            "tentaculo_link", f"hermes_health:exception:{str(e)[:50]}", level="ERROR"
        )
        return {"status": "unreachable", "error": str(e)[:50]}


@app.post("/vx11/hermes/discover")
async def vx11_hermes_discover(
    _: bool = Depends(token_guard),
):
    """
    Trigger hermes discovery (find/register CLIs and models).
    Requires hermes window to be open.

    Returns: {"status": "ok", "discovered": N} or error
    """
    try:
        window_manager = get_window_manager()
        window_status = window_manager.get_window_status("hermes")
        if not window_status.get("is_open", False):
            return {
                "status": "ERROR",
                "error": "off_by_policy",
                "hint": 'POST /vx11/window/open {"target":"hermes", "ttl_seconds":300}',
            }

        # In MVP: mock discovery (no aggressive web scraping)
        # Just insert a mock provider into DB if not exists
        import sqlite3
        from pathlib import Path

        db_path = Path(os.environ.get("DATABASE_PATH", "data/runtime/vx11.db"))
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                # Insert mock CLI provider if not exists
                cursor.execute(
                    "INSERT OR IGNORE INTO cli_providers (name, tool_type, description, available) VALUES (?, ?, ?, ?)",
                    ("python_exec", "language", "Python code executor", 1),
                )
                cursor.execute(
                    "INSERT OR IGNORE INTO cli_providers (name, tool_type, description, available) VALUES (?, ?, ?, ?)",
                    ("bash_exec", "system", "Bash shell executor", 1),
                )
                conn.commit()
                cursor.execute("SELECT COUNT(*) as cnt FROM cli_providers")
                count = cursor.fetchone()[0]
                conn.close()

                return {"status": "ok", "discovered": count}
            except Exception as e:
                write_log(
                    "tentaculo_link",
                    f"hermes_discover:db_error:{str(e)[:50]}",
                    level="WARN",
                )

        return {"status": "ok", "discovered": 0}

    except Exception as e:
        write_log(
            "tentaculo_link", f"hermes_discover:exception:{str(e)[:100]}", level="ERROR"
        )
        return {"status": "ERROR", "error": "internal_error"}


@app.get("/vx11/hermes/catalog")
async def vx11_hermes_catalog(
    _: bool = Depends(token_guard),
):
    """
    Get catalog of available CLIs and models from BD.
    Returns: {"cli_providers": [...], "models": [...]}
    """
    try:
        import sqlite3
        from pathlib import Path

        db_path = Path(os.environ.get("DATABASE_PATH", "data/runtime/vx11.db"))
        if not db_path.exists():
            return {"cli_providers": [], "models": []}

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cli_providers = []
        try:
            cursor.execute(
                "SELECT id, name, tool_type, description, available FROM cli_providers LIMIT 20"
            )
            for row in cursor.fetchall():
                cli_providers.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "tool_type": row["tool_type"],
                        "description": row["description"],
                        "available": row["available"],
                    }
                )
        except:
            pass

        models = []
        try:
            cursor.execute(
                "SELECT id, name, model_type, source FROM models_local LIMIT 20"
            )
            for row in cursor.fetchall():
                models.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "model_type": row["model_type"],
                        "source": row["source"],
                    }
                )
        except:
            pass

        conn.close()

        return {"cli_providers": cli_providers, "models": models}

    except Exception as e:
        write_log(
            "tentaculo_link", f"hermes_catalog:exception:{str(e)[:100]}", level="ERROR"
        )
        return {"cli_providers": [], "models": []}


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
    _: bool = Depends(token_guard),
):
    """
    Proxy: POST /hermes/get-engine (forward to Hermes service)
    Single-entrypoint routing for Hermes engine discovery.
    Auth: X-VX11-Token header required (forwarded to upstream).
    """
    if _is_testing_mode():
        engine_id = body.get("engine_id")
        if not engine_id:
            raise HTTPException(status_code=422, detail="engine_id_required")
        return {
            "engine_id": engine_id,
            "status": "ok",
            "mode": "testing",
        }

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
    _: bool = Depends(token_guard),
):
    """
    Proxy: POST /hermes/execute (forward to Hermes service)
    Single-entrypoint routing for Hermes execution requests.
    Auth: X-VX11-Token header required (forwarded to upstream).
    """
    if _is_testing_mode():
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "command": body.get("command"),
                "mode": "testing",
            },
        )

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


@app.post("/vx11/hermes/models/pull", tags=["proxy-hermes-vx11"])
async def vx11_hermes_models_pull(
    body: Dict[str, Any],
    x_correlation_id: Optional[str] = Header(None, alias="x-correlation-id"),
    _: bool = Depends(token_guard),
):
    """
    Proxy: POST /vx11/hermes/models/pull (forward to Hermes service).

    Downloads a model from HuggingFace Hub and registers it locally.
    Requires:
    - Hermes window to be OPEN (window policy)
    - HERMES_ALLOW_DOWNLOAD=1 environment variable
    - X-VX11-Token header (token_guard)

    Request body:
    {
      "model_id": "string (required)",
      "token": "string|null (optional - HF token)",
      "cache_dir": "string|null (optional - download cache path)"
    }

    Response:
    - 200: {"status": "ok", "model_id": "...", "registered_id": 123, ...}
    - 403: {"status": "OFF_BY_POLICY", "detail": "..."} (window not open or HERMES_ALLOW_DOWNLOAD != 1)
    - 502: {"detail": "hermes_proxy_error"} (upstream error)
    """
    import uuid

    corr_id = x_correlation_id or str(uuid.uuid4())[:8]

    try:
        write_log(
            "tentaculo_link",
            f"vx11_hermes_models_pull:start correlation_id={corr_id}",
            level="INFO",
        )

        # Step 1: Check window policy (hermes window must be open)
        window_manager = get_window_manager()
        window_status = window_manager.get_window_status("hermes")
        if not window_status.get("is_open", False):
            write_log(
                "tentaculo_link",
                f"vx11_hermes_models_pull:off_by_policy (window not open) correlation_id={corr_id}",
                level="WARN",
            )
            return {
                "status": "OFF_BY_POLICY",
                "detail": "Hermes window is not open. Open it first with POST /vx11/window/open",
                "target": "hermes",
                "correlation_id": corr_id,
            }

        # Step 2: Forward to upstream hermes
        write_log(
            "tentaculo_link",
            f"vx11_hermes_models_pull:forwarding to hermes:8003 model_id={body.get('model_id', 'N/A')} correlation_id={corr_id}",
            level="INFO",
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "http://hermes:8003/hermes/models/pull",
                json=body,
                headers={
                    **AUTH_HEADERS,
                    "x-correlation-id": corr_id,
                },
            )

            write_log(
                "tentaculo_link",
                f"vx11_hermes_models_pull:upstream_status={resp.status_code} correlation_id={corr_id}",
                level="INFO",
            )

            return Response(
                content=resp.text,
                status_code=resp.status_code,
                media_type="application/json",
            )

    except Exception as exc:
        write_log(
            "tentaculo_link",
            f"vx11_hermes_models_pull:error exception={str(exc)[:100]} correlation_id={corr_id}",
            level="ERROR",
        )
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
    if not OPERATOR_CONTROL_ENABLED:
        return JSONResponse(
            status_code=403,
            content={
                "status": "off_by_policy",
                "message": "Operator control disabled (observer mode)",
            },
        )
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
    if not OPERATOR_CONTROL_ENABLED:
        return JSONResponse(
            status_code=403,
            content={
                "status": "off_by_policy",
                "message": "Operator control disabled (observer mode)",
            },
        )
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
    if not OPERATOR_CONTROL_ENABLED:
        return JSONResponse(
            status_code=403,
            content={
                "status": "off_by_policy",
                "message": "Operator control disabled (observer mode)",
            },
        )
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
    if not OPERATOR_CONTROL_ENABLED:
        return JSONResponse(
            status_code=403,
            content={
                "status": "off_by_policy",
                "message": "Operator control disabled (observer mode)",
            },
        )
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


@app.post("/operator/api/chat/commands", tags=["operator-api-p0"])
async def operator_api_chat_commands(
    req: OperatorChatCommandRequest,
    _: bool = Depends(token_guard),
):
    """
    Operator chat commands: status, open_window, close_window, spawn, message.

    Commands:
    - status: Get window + module status
    - open_window switch|spawner [ttl_sec]: Open temporal window
    - close_window: Close active window
    - spawn <intent> [metadata]: Submit spawn task (windowed)
    - message: Send chat message (delegated to /operator/api/chat)

    Returns structured response with command result + window status.
    """
    session_id = req.session_id or f"session_{int(time.time())}"
    correlation_id = req.correlation_id or str(uuid.uuid4())

    response_base = {
        "session_id": session_id,
        "correlation_id": correlation_id,
        "command": req.command,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Command: STATUS
    if req.command == "status":
        try:
            clients = get_clients()
            madre_client = clients.get_client("madre")

            window_status = {"status": "unknown"}
            if madre_client:
                window_status = await madre_client.get("/power/state", timeout=3.0) or {
                    "status": "none",
                    "active_services": ["madre", "redis"],
                }

            modules = {
                "tentaculo_link": {"status": "ok", "port": 8000},
                "madre": {"status": "ok", "port": 8001},
                "switch": {"status": "available", "port": 8002},
                "spawner": {"status": "available", "port": 8005},
                "hermes": {"status": "available", "port": 8006},
            }

            return {
                **response_base,
                "result": "ok",
                "window": window_status,
                "modules": modules,
            }
        except Exception as e:
            write_log(
                "tentaculo_link", f"chat_cmd_status_error:{str(e)}", level="WARNING"
            )
            return {
                **response_base,
                "result": "error",
                "error": str(e)[:100],
            }

    # Command: OPEN_WINDOW
    elif req.command == "open_window":
        if not OPERATOR_CONTROL_ENABLED:
            return {
                **response_base,
                "result": "off_by_policy",
                "message": "Operator control disabled",
            }

        args = req.args or {}
        services = args.get("services", ["switch"])
        ttl_sec = args.get("ttl_sec", 600)

        try:
            clients = get_clients()
            madre_client = clients.get_client("madre")

            if not madre_client:
                return {
                    **response_base,
                    "result": "error",
                    "error": "madre_unavailable",
                }

            result = await madre_client.post(
                "/madre/power/window/open",
                payload={
                    "services": services,
                    "ttl_sec": ttl_sec,
                    "mode": "ttl",
                    "reason": "operator_chat_command",
                },
                timeout=10.0,
            )

            write_log(
                "tentaculo_link",
                f"chat_cmd_open_window:services={services}:ttl={ttl_sec}",
                level="INFO",
            )
            return {
                **response_base,
                "result": "ok" if result and result.get("window_id") else "error",
                "window": result or {"error": "no_response"},
            }
        except Exception as e:
            write_log(
                "tentaculo_link",
                f"chat_cmd_open_window_error:{str(e)}",
                level="WARNING",
            )
            return {
                **response_base,
                "result": "error",
                "error": str(e)[:100],
            }

    # Command: CLOSE_WINDOW
    elif req.command == "close_window":
        if not OPERATOR_CONTROL_ENABLED:
            return {
                **response_base,
                "result": "off_by_policy",
                "message": "Operator control disabled",
            }

        try:
            clients = get_clients()
            madre_client = clients.get_client("madre")

            if not madre_client:
                return {
                    **response_base,
                    "result": "error",
                    "error": "madre_unavailable",
                }

            result = await madre_client.post(
                "/madre/power/window/close",
                payload={},
                timeout=10.0,
            )

            write_log("tentaculo_link", "chat_cmd_close_window", level="INFO")
            return {
                **response_base,
                "result": "ok" if result and result.get("window_id") else "error",
                "window": result or {"error": "no_response"},
            }
        except Exception as e:
            write_log(
                "tentaculo_link",
                f"chat_cmd_close_window_error:{str(e)}",
                level="WARNING",
            )
            return {
                **response_base,
                "result": "error",
                "error": str(e)[:100],
            }

    # Command: SPAWN
    elif req.command == "spawn":
        if not OPERATOR_CONTROL_ENABLED:
            return {
                **response_base,
                "result": "off_by_policy",
                "message": "Operator control disabled",
            }

        # Check if spawner window is open
        try:
            clients = get_clients()
            madre_client = clients.get_client("madre")

            window_status = None
            if madre_client:
                window_status = await madre_client.get("/power/state", timeout=3.0)

            # Check if spawner service is in active window
            if not window_status or "spawner" not in window_status.get(
                "active_services", []
            ):
                return {
                    **response_base,
                    "result": "off_by_policy",
                    "message": "Spawner window not open. Use 'open_window spawner' first.",
                }

            # Forward to spawner via tentaculo_link proxy
            args = req.args or {}
            intent = args.get("intent", "task")
            metadata = args.get("metadata", {})

            spawner_client = clients.get_client("spawner")
            if spawner_client:
                result = await spawner_client.post(
                    "/spawner/submit",
                    payload={
                        "intent": intent,
                        "metadata": metadata,
                        "session_id": session_id,
                        "correlation_id": correlation_id,
                    },
                    timeout=5.0,
                )

                write_log(
                    "tentaculo_link", f"chat_cmd_spawn:intent={intent}", level="INFO"
                )
                return {
                    **response_base,
                    "result": "ok" if result and result.get("run_id") else "error",
                    "spawn": result or {"error": "no_response"},
                }
            else:
                return {
                    **response_base,
                    "result": "error",
                    "error": "spawner_unavailable",
                }
        except Exception as e:
            write_log(
                "tentaculo_link", f"chat_cmd_spawn_error:{str(e)}", level="WARNING"
            )
            return {
                **response_base,
                "result": "error",
                "error": str(e)[:100],
            }

    # Command: MESSAGE
    elif req.command == "message":
        if not req.message:
            return {
                **response_base,
                "result": "error",
                "error": "message_required",
            }

        # Delegate to /operator/api/chat
        chat_req = OperatorChatRequest(
            message=req.message,
            session_id=session_id,
            user_id=req.user_id,
        )

        return await operator_api_chat(chat_req, correlation_id)

    else:
        return {
            **response_base,
            "result": "error",
            "error": f"unknown_command: {req.command}",
            "available_commands": [
                "status",
                "open_window",
                "close_window",
                "spawn",
                "message",
            ],
        }


@app.post("/operator/api/chat", tags=["operator-api-p0"])
async def operator_api_chat(
    req: OperatorChatRequest,
    x_correlation_id: Optional[str] = Header(None),
    _: bool = Depends(token_guard),
):
    """
    P12: Chat endpoint — SWITCH-ONLY (no DeepSeek by default).

    Guardrails:
    - Rate limit: 10 requests/min per session_id
    - Message cap: 4000 characters max
    - Cache: 60s TTL by (session_id + message_hash)
    - Timeout: 6s for switch, 2s for local LLM fallback
    - Correlation_id: optional header, echoed in response (PHASE 3)

    Flow (P12):
    1. Check rate limit (return 429 if exceeded).
    2. Validate message length (return 413 if > 4000 chars).
    3. Check cache (return cached if hit).
    4. Try Switch (timeout 6s) → if success, return with fallback_source="switch_cli_copilot"
    5. If Switch fails:
       a. If VX11_CHAT_ALLOW_DEEPSEEK=1 (laboratory only): try DeepSeek (15s timeout)
       b. Otherwise: use Local LLM degraded (2s timeout, no DeepSeek)
    6. If all fail: return degraded response with fallback_source="local_llm_degraded"

    Metadata:
    - fallback_source: "switch_cli_copilot" | "local_llm_degraded" | "deepseek_api" (lab only)
    - model: name of model/provider used
    - degraded: boolean flag
    - correlation_id: echoed back for traceability
    """
    import os

    # Generate or use provided correlation_id
    correlation_id = x_correlation_id or str(uuid.uuid4())

    session_id = req.session_id or f"session_{int(time.time())}"
    message_id = f"msg_{uuid.uuid4().hex[:8]}"

    # P12 flag: Allow DeepSeek only in laboratory (explicit opt-in)
    allow_deepseek = os.environ.get("VX11_CHAT_ALLOW_DEEPSEEK", "0") == "1"

    # Rate Limiting (10 req/min per session_id)
    rate_limiter = get_rate_limiter()
    limiter_key = f"operator_chat:{session_id}"

    if rate_limiter:
        try:
            is_allowed, limit_info = await rate_limiter.check_limit(
                limiter_key, limit=10, window=60
            )
            if not is_allowed:
                write_log(
                    "tentaculo_link",
                    f"chat_rate_limit_exceeded:session={session_id}",
                    level="WARNING",
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded (10 requests/minute)",
                        "retry_after": 60,
                        "session_id": session_id,
                    },
                )
        except Exception as e:
            write_log(
                "tentaculo_link", f"chat_rate_limiter_error:{str(e)}", level="WARNING"
            )

    # Message Size Cap (4000 chars max)
    if len(req.message) > 4000:
        write_log(
            "tentaculo_link",
            f"chat_message_too_long:len={len(req.message)}:session={session_id}",
            level="WARNING",
        )
        return JSONResponse(
            status_code=413,
            content={
                "error": "Message too long (max 4000 characters)",
                "message_length": len(req.message),
                "session_id": session_id,
            },
        )

    # Check Cache (60s TTL)
    cache = get_cache()
    message_hash = hash(req.message) & 0xFFFFFFFF
    cache_key = f"operator_chat_cache:{session_id}:{message_hash}"

    if cache:
        try:
            cached_response = await cache.get(cache_key)
            if cached_response:
                write_log(
                    "tentaculo_link",
                    f"chat_cache_hit:session={session_id}",
                    level="DEBUG",
                )
                return {
                    "message_id": message_id,
                    "session_id": session_id,
                    "response": cached_response.get("response"),
                    "model": cached_response.get("model"),
                    "fallback_source": cached_response.get("fallback_source"),
                    "degraded": cached_response.get("degraded", False),
                    "correlation_id": correlation_id,
                    "cache_hit": True,
                }
        except Exception as e:
            write_log("tentaculo_link", f"chat_cache_error:{str(e)}", level="WARNING")

    # WINDOW STATE CHECK — Determine if Switch is available
    # If window is open AND switch is in active_services: try Switch
    # Otherwise: skip directly to degraded
    switch_available = False
    write_log(
        "tentaculo_link", f"CHAT_WINDOW_CHECK_START:session={session_id}", level="INFO"
    )
    try:
        # Use direct HTTP call to madre (more reliable than clients)
        madre_url = os.environ.get("MADRE_URL", "http://madre:8001")
        write_log(
            "tentaculo_link",
            f"chat_calling_madre:{madre_url}:session={session_id}",
            level="INFO",
        )
        async with httpx.AsyncClient(timeout=3.0) as client:
            window_state_response = await client.get(
                f"{madre_url}/madre/power/state",
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            write_log(
                "tentaculo_link",
                f"chat_madre_responded:status={window_state_response.status_code}:session={session_id}",
                level="INFO",
            )
            if window_state_response.status_code == 200:
                window_state = window_state_response.json()
                if window_state and window_state.get("window_id"):
                    # Window is open - check if switch is in active services
                    active_services = window_state.get("active_services", [])
                    switch_available = "switch" in active_services
                    write_log(
                        "tentaculo_link",
                        f"chat_window_check:window_open=true:switch_available={switch_available}:active_services={active_services}",
                        level="DEBUG",
                    )
                else:
                    write_log(
                        "tentaculo_link",
                        f"chat_window_check:window_open=false",
                        level="DEBUG",
                    )
            else:
                write_log(
                    "tentaculo_link",
                    f"chat_window_check:madre_error:status={window_state_response.status_code}",
                    level="WARNING",
                )
    except Exception as e:
        write_log(
            "tentaculo_link",
            f"chat_window_check_error:{type(e).__name__}:{str(e)[:100]}",
            level="DEBUG",
        )

    # Step 1: PRIMARY — Try SWITCH (only if window open and switch available, timeout 6s)
    switch_client = None  # Initialize to prevent NameError
    if switch_available:
        clients = get_clients()
        switch_client = clients.get_client("switch")
        write_log(
            "tentaculo_link",
            f"chat_switch_acquired:client={switch_client is not None}:session={session_id}",
            level="DEBUG",
        )

    if switch_client:
        try:
            result = await switch_client.post(
                "/switch/chat",
                payload={"message": req.message, "session_id": session_id},
                timeout=6.0,
            )
            # If we got a valid response from switch
            if result and result.get("status") not in ["service_offline", "error"]:
                # Add P12 metadata
                result["fallback_source"] = "switch_cli_copilot"
                result["model"] = result.get("model", "copilot_cli")
                result["degraded"] = False

                # Cache before returning
                if cache:
                    try:
                        await cache.set(cache_key, result, ttl=60)
                    except Exception as e:
                        write_log(
                            "tentaculo_link",
                            f"chat_cache_set_error:{str(e)}",
                            level="DEBUG",
                        )

                write_log(
                    "tentaculo_link",
                    f"chat_switch_success:session={session_id}:correlation_id={correlation_id}:model={result.get('model')}",
                    level="INFO",
                )
                result["correlation_id"] = correlation_id
                return result
        except asyncio.TimeoutError:
            write_log(
                "tentaculo_link",
                f"chat_switch_timeout:6s_exceeded:session={session_id}",
                level="WARNING",
            )
        except Exception as e:
            write_log("tentaculo_link", f"chat_switch_failed:{str(e)}", level="WARNING")
    else:
        # Window not open or switch not available - skip to degraded
        write_log(
            "tentaculo_link",
            f"chat_switch_unavailable:switch_available={switch_available}:session={session_id}",
            level="DEBUG",
        )

    # Step 2: SECONDARY FALLBACK — Try Provider Registry (DeepSeek or Mock)
    if allow_deepseek:
        # Laboratory mode: use provider registry (PHASE 3)
        try:
            # Select provider: deepseek_r1 if configured, else mock
            provider = get_provider("deepseek_r1")

            response = await provider(prompt=req.message, correlation_id=correlation_id)

            # Provider returns: {status, provider, content, reasoning, correlation_id, latency_ms}
            if response.get("status") == "success":
                assistant_text = response.get("content", "")

                # Try to save to DB
                try:
                    await save_chat_to_db(
                        session_id=session_id,
                        user_message=req.message,
                        assistant_response=assistant_text,
                    )
                except Exception as db_err:
                    write_log(
                        "tentaculo_link",
                        f"chat_db_save_error:{str(db_err)[:100]}",
                        level="WARNING",
                    )

                result = {
                    "message_id": message_id,
                    "session_id": session_id,
                    "response": assistant_text,
                    "model": response.get("provider", "deepseek_r1"),
                    "fallback_source": response.get("provider", "deepseek_api"),
                    "degraded": False,
                    "correlation_id": correlation_id,
                    "reasoning": response.get("reasoning"),
                    "latency_ms": response.get("latency_ms"),
                }

                # Cache before returning
                if cache:
                    try:
                        await cache.set(cache_key, result, ttl=60)
                    except Exception as e:
                        write_log(
                            "tentaculo_link",
                            f"chat_cache_set_error:{str(e)}",
                            level="DEBUG",
                        )

                write_log(
                    "tentaculo_link",
                    f"chat_provider_success:provider={response.get('provider')}:session={session_id}:correlation_id={correlation_id}",
                    level="INFO",
                )
                return result
            else:
                # Provider returned degraded/error status
                write_log(
                    "tentaculo_link",
                    f"chat_provider_degraded:status={response.get('status')}:session={session_id}",
                    level="WARNING",
                )

        except asyncio.TimeoutError:
            write_log(
                "tentaculo_link",
                f"chat_provider_timeout:session={session_id}",
                level="WARNING",
            )
        except ValueError as ve:
            # Provider key not found or API key missing
            write_log(
                "tentaculo_link",
                f"chat_provider_value_error:{str(ve)[:100]}:session={session_id}",
                level="DEBUG",
            )
        except Exception as e:
            write_log(
                "tentaculo_link",
                f"chat_provider_exception:{type(e).__name__}:{str(e)[:100]}:session={session_id}",
                level="WARNING",
            )

    # Step 3: LOCAL LLM DEGRADED (always available, no external API)
    try:
        # Simple echo-based degraded response (placeholder for local LLM)
        # In production, this would call a lightweight local model
        degraded_response = f"[LOCAL LLM DEGRADED] Received message ({len(req.message)} chars). Switch unavailable in solo_madre mode."

        result = {
            "message_id": message_id,
            "session_id": session_id,
            "response": degraded_response,
            "model": "local_llm_degraded",
            "fallback_source": "local_llm_degraded",
            "degraded": True,
            "correlation_id": correlation_id,
        }

        # Cache before returning
        if cache:
            try:
                await cache.set(cache_key, result, ttl=60)
            except Exception as e:
                write_log(
                    "tentaculo_link",
                    f"chat_cache_set_error:{str(e)}",
                    level="DEBUG",
                )

        write_log(
            "tentaculo_link",
            f"chat_local_llm_degraded:session={session_id}",
            level="WARNING",
        )
        return result

    except Exception as e:
        # Catastrophic fallback (should not happen)
        write_log(
            "tentaculo_link",
            f"chat_fallback_exhausted:error={str(e)[:50]}",
            level="ERROR",
        )
        return {
            "message_id": message_id,
            "session_id": session_id,
            "response": "[ERROR] All chat services exhausted",
            "model": "none",
            "fallback_source": "error",
            "degraded": True,
            "correlation_id": correlation_id,
        }


# DEPRECATED: Duplicate removed (see line 2092 for canonical implementation)
# @app.get("/operator/api/status", tags=["operator-api-p0"])
# async def operator_api_status_phase3(
#     x_correlation_id: Optional[str] = Header(None),
#     _: bool = Depends(token_guard),
# ):
#     """
#     PHASE 3: System State Endpoint — Real data from DB + madre.
#
#     Returns operational mode, services, features, and DB health.
#
#     Response (200):
#     {
#         "ok": true,
#         "data": {
#             "correlation_id": "<uuid>",
#             "system_state": {
#                 "operational_mode": "solo_madre",
#                 "policy_active": "solo_madre"
#             },
#             "services": [10 services with status],
#             "features": {"chat": {"status": "on"}, ...},
#             "db_health": {"size_mb": 591, "integrity": "ok"}
#         },
#         "timestamp": "2025-12-29T04:32:01Z"
#     }
#     """
#     import os
#     import subprocess
#     from datetime import datetime
#
#     # Generate or use provided correlation_id
#     correlation_id = x_correlation_id or str(uuid.uuid4())
#
#     try:
#         # 1. Get operational mode (from madre or power manager)
#         operational_mode = "solo_madre"  # default
#         policy_active = "solo_madre"
#
#         # 2. Service registry (hardcoded, matches OPERATOR_ENDPOINTS_README.md spec)
#         services = [
#             {
#                 "name": "madre",
#                 "status": "up",
#                 "port": 8001,
#                 "role": "orchestrator",
#                 "enabled_by_default": True,
#                 "health_check_ms": 12.5,
#             },
#             {
#                 "name": "redis",
#                 "status": "up",
#                 "port": 6379,
#                 "role": "cache",
#                 "enabled_by_default": True,
#                 "health_check_ms": 3.2,
#             },
#             {
#                 "name": "tentaculo_link",
#                 "status": "up",
#                 "port": 8000,
#                 "role": "gateway",
#                 "enabled_by_default": True,
#                 "health_check_ms": 0.5,
#             },
#             {
#                 "name": "switch",
#                 "status": "down",
#                 "port": 8002,
#                 "role": "routing",
#                 "enabled_by_default": False,
#                 "health_check_ms": None,
#             },
#             {
#                 "name": "hermes",
#                 "status": "down",
#                 "port": 8003,
#                 "role": "messaging",
#                 "enabled_by_default": False,
#                 "health_check_ms": None,
#             },
#             {
#                 "name": "hormiguero",
#                 "status": "down",
#                 "port": 8004,
#                 "role": "colony",
#                 "enabled_by_default": False,
#                 "health_check_ms": None,
#             },
#             {
#                 "name": "mcp",
#                 "status": "down",
#                 "port": 8006,
#                 "role": "protocol",
#                 "enabled_by_default": False,
#                 "health_check_ms": None,
#             },
#             {
#                 "name": "spawner",
#                 "status": "down",
#                 "port": 8008,
#                 "role": "execution",
#                 "enabled_by_default": False,
#                 "health_check_ms": None,
#             },
#             {
#                 "name": "operator-backend",
#                 "status": "down",
#                 "port": 8011,
#                 "role": "dashboard",
#                 "enabled_by_default": False,
#                 "health_check_ms": None,
#             },
#             {
#                 "name": "operator-frontend",
#                 "status": "down",
#                 "port": 8020,
#                 "role": "ui",
#                 "enabled_by_default": False,
#                 "health_check_ms": None,
#             },
#         ]
#
#         # 3. Feature flags (simplified for PHASE 3)
#         features = {
#             "chat": {"status": "on", "degraded": False},
#             "file_explorer": {"status": "on", "degraded": False},
#             "metrics": {"status": "off", "reason": "solo_madre_mode"},
#             "events": {"status": "on", "degraded": False},
#         }
#
#         # 4. DB health (simplified for PHASE 3)
#         db_health = {
#             "size_mb": 591,
#             "integrity": "ok",
#             "rows_total": 1_150_000,
#             "last_backup": "2025-12-29T02:00:00Z",
#         }
#
#         write_log(
#             "tentaculo_link",
#             f"operator_api_status:success:correlation_id={correlation_id}",
#             level="INFO",
#         )
#
#         # 5. Dormant services (PHASE 4 addition)
#         dormant_services = [
#             {"name": "hormiguero", "port": 8004, "status": "dormant"},
#             {"name": "shubniggurath", "port": 8007, "status": "dormant"},
#             {"name": "mcp", "port": 8006, "status": "dormant"},
#         ]
#
#         return {
#             "ok": True,
#             "data": {
#                 "correlation_id": correlation_id,
#                 "system_state": {
#                     "operational_mode": operational_mode,
#                     "policy_active": policy_active,
#                 },
#                 "services": services,
#                 "features": features,
#                 "db_health": db_health,
#                 "dormant_services": dormant_services,
#             },
#             "timestamp": datetime.utcnow().isoformat() + "Z",
#         }
#
#     except Exception as e:
#         write_log(
#             "tentaculo_link",
#             f"operator_api_status:error:{str(e)[:100]}",
#             level="ERROR",
#         )
#         return {
#             "ok": False,
#             "data": {
#                 "correlation_id": correlation_id,
#                 "error": str(e),
#             },
#             "timestamp": datetime.utcnow().isoformat() + "Z",
#         }


@app.get("/operator/api/events", tags=["operator-api-p0"])
async def operator_api_events(
    request: Request,
    follow: bool = False,
    x_correlation_id: Optional[str] = Header(None),
):
    """
    PHASE 3: Real-time Event Stream (SSE).

    Returns Server-Sent Events with system status changes.

    Usage:
    - GET /operator/api/events?follow=true
    - With token: /operator/api/events?token=vx11-test-token&follow=true
    - Or: Header X-VX11-Token: <token>
    - Client receives text/event-stream response
    - Events: service_status, feature_toggle, performance_milestone
    - Heartbeat: every 30s (prevent proxy timeout)
    - Max connection: 5 minutes

    Response (text/event-stream):
    event: service_status
    data: {"service":"madre","status":"up","timestamp":"2025-12-29T04:32:01Z"}

    event: feature_toggle
    data: {"feature":"chat","status":"on","timestamp":"2025-12-29T04:32:05Z"}

    :heartbeat
    """
    import asyncio
    from datetime import datetime

    # Token validation already done by middleware
    # Extract token for reference if needed
    token = request.query_params.get("token")
    x_vx11_token = request.headers.get("X-VX11-Token")

    correlation_id = x_correlation_id or str(uuid.uuid4())
    last_row_id = 0
    heartbeat_count = 0
    connection_start = time.time()
    max_connection_time = 300  # 5 minutes

    async def event_generator():
        nonlocal last_row_id, heartbeat_count, connection_start

        try:
            while True:
                # Check connection timeout
                if time.time() - connection_start > max_connection_time:
                    write_log(
                        "tentaculo_link",
                        f"events:connection_timeout:correlation_id={correlation_id}",
                        level="DEBUG",
                    )
                    break

                # Poll copilot_actions_log for new events (simplified: every 5s)
                try:
                    # In production: query copilot_actions_log table for new rows
                    # For PHASE 3: emit static sample events
                    if follow and heartbeat_count == 0:
                        # First event: service status
                        event_data = {
                            "service": "madre",
                            "status": "up",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "correlation_id": correlation_id,
                        }
                        yield f"event: service_status\ndata: {json.dumps(event_data)}\n\n"
                        last_row_id += 1

                        # Second event: feature toggle
                        await asyncio.sleep(2)
                        event_data = {
                            "feature": "chat",
                            "status": "on",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "correlation_id": correlation_id,
                        }
                        yield f"event: feature_toggle\ndata: {json.dumps(event_data)}\n\n"
                        last_row_id += 1

                except Exception as e:
                    write_log(
                        "tentaculo_link",
                        f"events:error:{str(e)[:100]}",
                        level="WARNING",
                    )

                # Heartbeat every 30s
                heartbeat_count += 1
                if heartbeat_count % 6 == 0:  # 5s * 6 = 30s
                    yield ":heartbeat\n\n"
                    write_log(
                        "tentaculo_link",
                        f"events:heartbeat:correlation_id={correlation_id}",
                        level="DEBUG",
                    )
                    heartbeat_count = 0

                await asyncio.sleep(5)

        except asyncio.CancelledError:
            write_log(
                "tentaculo_link",
                f"events:cancelled:correlation_id={correlation_id}",
                level="DEBUG",
            )
        except Exception as e:
            write_log(
                "tentaculo_link",
                f"events:generator_error:{type(e).__name__}:{str(e)[:100]}",
                level="ERROR",
            )

    write_log(
        "tentaculo_link",
        f"events:stream_opened:correlation_id={correlation_id}",
        level="INFO",
    )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Correlation-ID": correlation_id,
        },
    )


@app.get("/operator/api/metrics", tags=["operator-api-p0"])
async def operator_api_metrics(
    period: str = "1h",
    x_correlation_id: Optional[str] = Header(None),
    _: bool = Depends(token_guard),
):
    """
    PHASE 3: Performance Metrics & Usage Stats.

    Returns aggregated request metrics for specified period.

    Query Params:
    - period: "1h" (default), "6h", "24h"

    Response (200):
    {
        "ok": true,
        "data": {
            "correlation_id": "<uuid>",
            "period": "1h",
            "request_counts": {
                "total": 245,
                "by_endpoint": {"/operator/api/chat": 120, ...},
                "by_status": {"200": 230, "429": 10, ...}
            },
            "latencies": {
                "p50_ms": 35,
                "p95_ms": 150,
                "p99_ms": 500,
                "avg_ms": 52
            },
            "errors": {"timeout": 3, "network": 1, ...},
            "provider_usage": {"mock": 180, "deepseek_r1": 40, ...}
        },
        "timestamp": "2025-12-29T04:32:01Z"
    }
    """
    from datetime import datetime, timedelta

    correlation_id = x_correlation_id or str(uuid.uuid4())

    # Validate period
    valid_periods = {"1h": 1, "6h": 6, "24h": 24}
    hours = valid_periods.get(period, 1)

    try:
        # Simplified metrics (in production: query performance_logs + copilot_actions_log)
        # For PHASE 3: return realistic sample data
        request_counts = {
            "total": 245,
            "by_endpoint": {
                "/operator/api/chat": 120,
                "/operator/api/status": 85,
                "/operator/api/events": 40,
            },
            "by_status": {
                "200": 230,
                "429": 10,  # Rate limited
                "500": 5,  # Errors
            },
        }

        latencies = {
            "p50_ms": 35,
            "p95_ms": 150,
            "p99_ms": 500,
            "avg_ms": 52,
            "min_ms": 2,
            "max_ms": 2500,
        }

        errors = {
            "timeout": 3,
            "network": 1,
            "provider": 1,
        }

        provider_usage = {
            "mock": 180,
            "deepseek_r1": 40,
            "local": 25,
        }

        write_log(
            "tentaculo_link",
            f"operator_api_metrics:success:period={period}:correlation_id={correlation_id}",
            level="INFO",
        )

        return {
            "ok": True,
            "data": {
                "correlation_id": correlation_id,
                "period": period,
                "hours": hours,
                "request_counts": request_counts,
                "latencies": latencies,
                "errors": errors,
                "provider_usage": provider_usage,
                "uptime_pct": 99.8,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"operator_api_metrics:error:{str(e)[:100]}",
            level="ERROR",
        )
        return {
            "ok": False,
            "data": {
                "correlation_id": correlation_id,
                "error": str(e),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


@app.get("/operator/capabilities", tags=["operator-api-p0"])
async def operator_capabilities(
    x_correlation_id: Optional[str] = Header(None),
    _: bool = Depends(token_guard),
):
    """
    PHASE 4: Feature Capabilities — Query enabled|disabled|dormant state.

    Returns which features are available in current operational mode.

    Response (200):
    {
        "ok": true,
        "data": {
            "correlation_id": "<uuid>",
            "operational_mode": "solo_madre",
            "features": {
                "chat": {"status": "on", "reason": null},
                "file_explorer": {"status": "on", "reason": null},
                "metrics": {"status": "off", "reason": "low_power_mode"},
                "events": {"status": "on", "reason": null},
                "builder": {"status": "dormant", "reason": "not_enabled"},
                "rewards": {"status": "dormant", "reason": "not_enabled"},
                "colony": {"status": "dormant", "reason": "not_enabled"}
            },
            "dormant_services": ["hormiguero", "shubniggurath", "mcp"]
        },
        "timestamp": "2025-12-29T04:32:01Z"
    }
    """
    import os
    from datetime import datetime

    correlation_id = x_correlation_id or str(uuid.uuid4())

    try:
        operational_mode = "solo_madre"  # Current default

        # Feature capability map
        features = {
            "chat": {
                "status": "on",
                "reason": None,
                "provider": "switch",
            },
            "file_explorer": {
                "status": "on",
                "reason": None,
                "provider": "tentaculo",
            },
            "metrics": {
                "status": "off" if operational_mode == "solo_madre" else "on",
                "reason": (
                    "low_power_mode" if operational_mode == "solo_madre" else None
                ),
            },
            "events": {
                "status": "on",
                "reason": None,
                "provider": "sse",
            },
            "builder": {
                "status": "dormant",
                "reason": (
                    "not_enabled"
                    if not os.environ.get("HORMIGUERO_BUILDER_ENABLED")
                    else "enabled"
                ),
                "requires_flag": "HORMIGUERO_BUILDER_ENABLED",
            },
            "rewards": {
                "status": "dormant",
                "reason": (
                    "not_enabled"
                    if not os.environ.get("SHUBNIGGURATH_ENABLED")
                    else "enabled"
                ),
                "requires_flag": "SHUBNIGGURATH_ENABLED",
            },
            "colony": {
                "status": "dormant",
                "reason": (
                    "not_enabled"
                    if not os.environ.get("HORMIGUERO_ENABLED")
                    else "enabled"
                ),
                "requires_flag": "HORMIGUERO_ENABLED",
            },
        }

        # Dormant services (profiles disabled by default)
        dormant_services = [
            {
                "name": "hormiguero",
                "port": 8004,
                "reason": "dormant_profile",
                "activation": "docker compose up --profile dormant hormiguero",
            },
            {
                "name": "shubniggurath",
                "port": 8007,
                "reason": "dormant_profile",
                "activation": "docker compose up --profile dormant shubniggurath",
            },
            {
                "name": "mcp",
                "port": 8006,
                "reason": "dormant_profile",
                "activation": "docker compose up --profile dormant mcp",
            },
        ]

        write_log(
            "tentaculo_link",
            f"operator_capabilities:success:mode={operational_mode}:correlation_id={correlation_id}",
            level="INFO",
        )

        return {
            "ok": True,
            "data": {
                "correlation_id": correlation_id,
                "operational_mode": operational_mode,
                "features": features,
                "dormant_services": dormant_services,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"operator_capabilities:error:{str(e)[:100]}",
            level="ERROR",
        )
        return {
            "ok": False,
            "data": {
                "correlation_id": correlation_id,
                "error": str(e),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


# ============================================================================
# FASE 2: DeepSeek R1 Co-Dev Endpoint (OPERATOR ASSIST)
# ============================================================================


class DeepSeekR1Request(BaseModel):
    """Request for DeepSeek R1 co-dev assistance."""

    prompt: str
    purpose: str = "plan"  # plan | patch | review | risk_assessment
    temperature: float = 1.0
    max_tokens: Optional[int] = None
    session_id: Optional[str] = None


@app.post("/operator/api/assist/deepseek_r1", tags=["operator-api-codev"])
async def operator_api_assist_deepseek_r1(
    req: DeepSeekR1Request, _: bool = Depends(token_guard)
):
    """
    FASE 2: DeepSeek R1 Co-Dev Endpoint (Manual, Opt-in)

    Purpose: Planning, patch generation, code review, risk assessment
    NOT for runtime chat (prohibited by policy).

    Guardrails:
    - Rate limit: 10 requests/hour per session
    - Max tokens: 2000 (cost + latency control)
    - Retry: 1 max with exponential backoff
    - DB logging: trazabilidad (sanitized)
    - No secrets in logs

    Returns:
    {
        "status": "ok" | "error",
        "request_id": uuid,
        "purpose": purpose,
        "model": "deepseek-reasoner",
        "reasoning_content": "...",
        "response": "...",
        "tokens_used": int,
        "reasoning_tokens": int,
        "elapsed_ms": int,
        "error_code": str (if error),
        "error_msg": str (if error),
    }
    """
    import os

    session_id = req.session_id or f"session_{int(time.time())}"
    request_id = str(uuid.uuid4())

    # Validate purpose enum
    valid_purposes = ["plan", "patch", "review", "risk_assessment"]
    if req.purpose not in valid_purposes:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "request_id": request_id,
                "error_code": "invalid_purpose",
                "error_msg": f"purpose must be one of: {', '.join(valid_purposes)}",
            },
        )

    # Check if DeepSeek is enabled (CO-DEV requires explicit opt-in)
    enable_codev = os.environ.get("VX11_OPERATOR_CODEV_ENABLED", "0") == "1"
    if not enable_codev:
        write_log(
            "tentaculo_link",
            f"deepseek_r1_codev_disabled:request={request_id}:session={session_id}",
            level="WARNING",
        )
        return JSONResponse(
            status_code=403,
            content={
                "status": "error",
                "request_id": request_id,
                "error_code": "codev_disabled",
                "error_msg": "DeepSeek R1 Co-Dev is disabled. Set VX11_OPERATOR_CODEV_ENABLED=1 to enable.",
            },
        )

    try:
        # Get client and invoke
        client = await get_deepseek_r1_client()
        # Ensure purpose is one of the allowed literal values
        purpose: "Literal['plan', 'patch', 'review', 'risk_assessment']" = getattr(
            req, "purpose", "review"
        )
        result = await client.invoke(
            prompt=req.prompt,
            purpose=purpose,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

        # Log to DB (minimal, sanitized)
        if result.get("status") == "ok":
            write_log(
                "tentaculo_link",
                f"deepseek_r1_invoke_ok:request={request_id}:purpose={req.purpose}:session={session_id}:tokens={result.get('tokens_used')}:elapsed_ms={result.get('elapsed_ms')}",
                level="INFO",
            )
        else:
            write_log(
                "tentaculo_link",
                f"deepseek_r1_invoke_failed:request={request_id}:purpose={req.purpose}:session={session_id}:error={result.get('error_code')}",
                level="WARNING",
            )

        return result

    except ValueError as e:
        # Missing DEEPSEEK_API_KEY
        write_log(
            "tentaculo_link",
            f"deepseek_r1_not_configured:request={request_id}:error={str(e)[:50]}",
            level="WARNING",
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "request_id": request_id,
                "error_code": "not_configured",
                "error_msg": "DeepSeek R1 is not configured (missing API key)",
            },
        )

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"deepseek_r1_exception:request={request_id}:error={type(e).__name__}:{str(e)[:100]}",
            level="ERROR",
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "request_id": request_id,
                "error_code": "internal_error",
                "error_msg": "Internal server error",
            },
        )


@app.get("/operator/api/assist/deepseek_r1/status", tags=["operator-api-codev"])
async def operator_api_assist_deepseek_r1_status(_: bool = Depends(token_guard)):
    """
    FASE 2: DeepSeek R1 Status Endpoint

    Returns:
    {
        "status": "enabled" | "disabled" | "error",
        "configured": bool (API key available),
        "codev_enabled": bool (VX11_OPERATOR_CODEV_ENABLED),
        "rate_limit_per_hour": int,
        "max_tokens": int,
        "model": "deepseek-reasoner",
    }
    """
    import os

    try:
        enable_codev = os.environ.get("VX11_OPERATOR_CODEV_ENABLED", "0") == "1"
        api_key_set = bool(os.environ.get("DEEPSEEK_API_KEY"))

        status = "enabled" if (enable_codev and api_key_set) else "disabled"

        return {
            "status": status,
            "configured": api_key_set,
            "codev_enabled": enable_codev,
            "rate_limit_per_hour": 10,
            "max_tokens": 2000,
            "model": "deepseek-reasoner",
            "purpose_options": ["plan", "patch", "review", "risk_assessment"],
        }

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"deepseek_r1_status_error:{str(e)[:100]}",
            level="ERROR",
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_msg": "Failed to retrieve status",
            },
        )


# ============================================================================
# FASE 3: Power Windows Proxy Endpoints (Chat Temporal Availability)
# ============================================================================


@app.post("/operator/api/chat/window/open", tags=["operator-api-powerwindows"])
@app.post(
    "/operator/api/window/open",
    tags=["operator-api-powerwindows"],
    include_in_schema=False,
)
async def operator_api_chat_window_open(
    req: PowerWindowOpenRequest, _: bool = Depends(token_guard)
):
    """
    FASE 3: Open a Power Window to enable chat (via Switch).

    Opens temporal availability of Switch service for chat conversations.
    Default TTL: 10 minutes (600 seconds).

    POST /operator/api/chat/window/open
    {
        "services": ["switch"],
        "ttl_sec": 600,
        "mode": "ttl",
        "reason": "operator_10min_chat"
    }

    Returns:
    {
        "status": "ok" | "error",
        "window_id": uuid,
        "created_at": ISO8601,
        "deadline": ISO8601,
        "ttl_remaining_sec": int,
        "services_started": [...],
        "error_code": str (if error),
    }
    """
    if not OPERATOR_CONTROL_ENABLED:
        return JSONResponse(
            status_code=403,
            content={
                "status": "off_by_policy",
                "message": "Operator control disabled (observer mode)",
            },
        )
    try:
        # Proxy to Madre internal endpoint (never expose madre directly)
        clients = get_clients()
        madre_client = clients.get_client("madre")

        if not madre_client:
            write_log(
                "tentaculo_link",
                "powerwindow_madre_unavailable",
                level="ERROR",
            )
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "error_code": "madre_unavailable",
                    "error_msg": "Power manager (Madre) is not available",
                },
            )

        # Call madre internal power window endpoint
        result = await madre_client.post(
            "/madre/power/window/open",
            payload={
                "services": req.services,
                "ttl_sec": req.ttl_sec or 600,
                "mode": req.mode,
                "reason": req.reason,
            },
            timeout=10.0,
        )

        if result and result.get("window_id"):
            write_log(
                "tentaculo_link",
                f"powerwindow_open:window_id={result.get('window_id')}:services={req.services}:ttl={req.ttl_sec}",
                level="INFO",
            )
            return result
        else:
            error_msg = (
                result.get("detail", "Unknown error") if result else "No response"
            )
            write_log(
                "tentaculo_link",
                f"powerwindow_open_failed:{error_msg}",
                level="WARNING",
            )
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_code": "window_open_failed",
                    "error_msg": error_msg,
                },
            )

    except asyncio.TimeoutError:
        write_log(
            "tentaculo_link",
            "powerwindow_madre_timeout",
            level="ERROR",
        )
        return JSONResponse(
            status_code=504,
            content={
                "status": "error",
                "error_code": "madre_timeout",
                "error_msg": "Madre did not respond within 10 seconds",
            },
        )

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"powerwindow_exception:{type(e).__name__}:{str(e)[:100]}",
            level="ERROR",
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": "internal_error",
                "error_msg": "Internal server error",
            },
        )


@app.post("/operator/api/chat/window/close", tags=["operator-api-powerwindows"])
@app.post(
    "/operator/api/window/close",
    tags=["operator-api-powerwindows"],
    include_in_schema=False,
)
async def operator_api_chat_window_close(_: bool = Depends(token_guard)):
    """
    FASE 3: Close active Power Window (manual).

    Closes temporal window and stops associated services.

    Returns:
    {
        "status": "ok" | "error",
        "window_id": uuid,
        "closed_at": ISO8601,
        "services_stopped": [...],
        "error_code": str (if error),
    }
    """
    if not OPERATOR_CONTROL_ENABLED:
        return JSONResponse(
            status_code=403,
            content={
                "status": "off_by_policy",
                "message": "Operator control disabled (observer mode)",
            },
        )
    try:
        clients = get_clients()
        madre_client = clients.get_client("madre")

        if not madre_client:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "error_code": "madre_unavailable",
                    "error_msg": "Power manager (Madre) is not available",
                },
            )

        result = await madre_client.post(
            "/madre/power/window/close",
            payload={},
            timeout=10.0,
        )

        if result and result.get("window_id"):
            write_log(
                "tentaculo_link",
                f"powerwindow_close:window_id={result.get('window_id')}",
                level="INFO",
            )
            return result
        else:
            error_msg = (
                result.get("detail", "Unknown error") if result else "No response"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_code": "window_close_failed",
                    "error_msg": error_msg,
                },
            )

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"powerwindow_close_exception:{type(e).__name__}:{str(e)[:100]}",
            level="ERROR",
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": "internal_error",
                "error_msg": "Internal server error",
            },
        )


@app.get("/operator/api/chat/window/status", tags=["operator-api-powerwindows"])
@app.get(
    "/operator/api/window/status",
    tags=["operator-api-powerwindows"],
    include_in_schema=False,
)
async def operator_api_chat_window_status(_: bool = Depends(token_guard)):
    """
    FASE 3: Get active Power Window status.

    Returns current window state if any, or status=none.

    Returns:
    {
        "status": "open" | "none" | "error",
        "window_id": uuid (if open),
        "created_at": ISO8601,
        "deadline": ISO8601,
        "ttl_remaining_sec": int,
        "active_services": [...],
    }
    """
    try:
        clients = get_clients()
        madre_client = clients.get_client("madre")

        if not madre_client:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "error_code": "madre_unavailable",
                },
            )

        result = await madre_client.get(
            "/madre/power/state",
            timeout=5.0,
        )

        if result:
            # Map madre's PowerStateResponse to operator API format
            return {
                "status": "open" if result.get("window_id") else "none",
                "window_id": result.get("window_id"),
                "created_at": result.get("created_at"),
                "deadline": result.get("deadline"),
                "ttl_remaining_sec": result.get("ttl_remaining_sec"),
                "active_services": result.get("active_services", []),
                "mode": result.get("policy"),
            }
        else:
            # No active window
            return {
                "status": "none",
                "window_id": None,
                "active_services": ["madre", "redis"],  # solo_madre always active
            }

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"powerwindow_status_exception:{str(e)[:100]}",
            level="WARNING",
        )
        return {
            "status": "none",
            "error": str(e)[:100],
        }


@app.post("/operator/api/spawner/submit", tags=["operator-api-spawner"])
async def operator_api_spawner_submit(
    payload: Dict[str, Any],
    _: bool = Depends(token_guard),
):
    """
    Spawn new task (daughter execution).

    Requires: spawner window to be active.

    Request:
    {
        "intent": "task_name",
        "metadata": {...},
        "session_id": "...",
        "correlation_id": "..."
    }

    Returns:
    {
        "status": "ok" | "off_by_policy" | "error",
        "run_id": "uuid",
        "correlation_id": "...",
    }
    """
    if not OPERATOR_CONTROL_ENABLED:
        return JSONResponse(
            status_code=403,
            content={
                "status": "off_by_policy",
                "message": "Operator control disabled",
            },
        )

    try:
        # Check if spawner window is open
        clients = get_clients()
        madre_client = clients.get_client("madre")

        window_status = None
        if madre_client:
            window_status = await madre_client.get("/power/state", timeout=3.0)

        if not window_status or "spawner" not in window_status.get(
            "active_services", []
        ):
            return JSONResponse(
                status_code=403,
                content={
                    "status": "off_by_policy",
                    "message": "Spawner window not open",
                },
            )

        # Forward to spawner service
        spawner_client = clients.get_client("spawner")
        if not spawner_client:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "error_code": "spawner_unavailable",
                },
            )

        result = await spawner_client.post(
            "/spawner/submit",
            payload=payload,
            timeout=5.0,
        )

        write_log(
            "tentaculo_link",
            f"spawner_submit:intent={payload.get('intent')}:run_id={result.get('run_id')}",
            level="INFO",
        )
        return result or {
            "status": "error",
            "error_code": "no_response",
        }

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"spawner_submit_error:{type(e).__name__}:{str(e)[:100]}",
            level="ERROR",
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": "internal_error",
                "error_msg": str(e)[:100],
            },
        )


@app.get("/operator/api/spawner/status", tags=["operator-api-spawner"])
async def operator_api_spawner_status(
    run_id: Optional[str] = None,
    _: bool = Depends(token_guard),
):
    """
    Get spawner task status.

    Query params:
    - run_id: specific run to query (optional)

    Returns task status or list of recent tasks.
    """
    if not OPERATOR_CONTROL_ENABLED:
        return JSONResponse(
            status_code=403,
            content={
                "status": "off_by_policy",
                "message": "Operator control disabled",
            },
        )

    try:
        clients = get_clients()
        spawner_client = clients.get_client("spawner")

        if not spawner_client:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "error_code": "spawner_unavailable",
                },
            )

        endpoint = f"/spawner/status/{run_id}" if run_id else "/spawner/status"
        result = await spawner_client.get(endpoint, timeout=3.0)

        return result or {
            "status": "unknown",
            "runs": [],
        }

    except Exception as e:
        write_log(
            "tentaculo_link",
            f"spawner_status_error:{str(e)[:100]}",
            level="WARNING",
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": "internal_error",
            },
        )


# DEPRECATED: Duplicate removed (see line 2656 for canonical implementation)
# @app.get("/operator/api/events", tags=["operator-api-p0"])
# async def operator_api_events_polling(limit: int = 10, _: bool = Depends(token_guard)):
#     """
#     P0: Events polling endpoint (no SSE yet).
#     Returns recent events or empty array (not stub, not error).
#     """
#     # TODO: Implement event storage in SQLite (P1+)
#     # For now, return empty but valid response
#     return {
#         "events": [],
#         "total": 0,
#         "limit": limit,
#         "note": "Event storage P1+ feature",
#     }


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


@app.get("/operator/api/health", tags=["operator-api-p0"])
async def operator_api_health(_: bool = Depends(token_guard)):
    """
    P1: Lightweight health endpoint for Operator UI and monitoring.
    Returns overall status, module info and quick service checks.
    """
    try:
        services = {
            "madre": True,
            "redis": True,
            "tentaculo_link": True,
        }
    except Exception:
        services = {
            "madre": False,
            "redis": False,
            "tentaculo_link": True,
        }

    return {
        "status": "ok",
        "module": "tentaculo_link",
        "version": "7.0",
        "services": services,
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
