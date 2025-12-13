"""
Tentáculo Link v7.0 - Gateway Refactored
Pure proxy + auth + context-7 middleware + modular clients
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config.forensics import write_log
from config.settings import settings
from config.tokens import get_token, load_tokens
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    clients = get_clients()
    context7 = get_context7_manager()
    await clients.startup()
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    write_log("tentaculo_link", "startup:v7_initialized")
    try:
        yield
    finally:
        await clients.shutdown()
        write_log("tentaculo_link", "shutdown:v7_closed")


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


# ============ HEALTH & STATUS ============

@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "ok", "module": "tentaculo_link", "version": "7.0"}


@app.get("/vx11/status")
async def vx11_status():
    """Aggregate health check for all modules (async parallel)."""
    import datetime
    clients = get_clients()
    health_results = await clients.health_check_all()
    
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
        }
    }


# ============ OPERATOR CHAT (CONTEXT-7 INTEGRATED) ============

@app.post("/operator/chat")
async def operator_chat(
    req: OperatorChatRequest,
    _: bool = Depends(token_guard),
):
    """Route chat to Operator backend with CONTEXT-7 integration."""
    session_id = req.session_id or str(uuid.uuid4())
    user_id = req.user_id or "local"
    
    # Track in CONTEXT-7
    context7 = get_context7_manager()
    context7.add_message(session_id, "user", req.message, req.metadata)
    context_hint = context7.get_hint_for_llm(session_id)
    
    # Route to Operator backend
    clients = get_clients()
    payload = {
        "session_id": session_id,
        "user_id": user_id,
        "message": req.message,
        "context_summary": context_hint,
        "metadata": req.metadata or {},
    }
    result = await clients.route_to_operator("/operator/chat", payload)
    
    # Track response in CONTEXT-7
    assistant_msg = result.get("response") or result.get("message") or json.dumps(result)
    context7.add_message(session_id, "assistant", str(assistant_msg))
    
    write_log("tentaculo_link", f"operator_chat:{session_id}")
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
            "healthy": sum(1 for h in health_results.values() if h.get("status") == "ok"),
            "unhealthy": sum(1 for h in health_results.values() if h.get("status") != "ok"),
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
    write_log("tentaculo_link", f"http_error:{exc.status_code}:{exc.detail}", level="WARNING")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


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

    async def broadcast(self, message_type: str, data: dict):
        """Broadcast event to all connected clients (v8.1 stub for Operator updates)."""
        for client_id, conn in list(self.connections.items()):
            try:
                await conn.send_json({"type": message_type, "data": data})
            except Exception:
                # Client disconnected or error; silently skip
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = "anonymous"):
    """WebSocket endpoint for real-time updates (stub)."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo for now
            await websocket.send_json({"type": "echo", "data": data})
    except WebSocketDisconnect:
        await manager.disconnect(client_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
