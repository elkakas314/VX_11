"""
Tentáculo Link v7.0 - Gateway Refactored
Pure proxy + auth + context-7 middleware + modular clients
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set

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


# ============ EVENT VALIDATION & CANONICALIZATION ============

CANONICAL_EVENT_WHITELIST = {
    "system.alert",
    "system.correlation.updated",
    "system.state.summary",
    "forensic.snapshot.created",
    "madre.decision.explained",
    "switch.system.tension",
    "shub.action.narrated",
}

def validate_event_type(event_type: str) -> bool:
    """Check if event type is in canonical whitelist."""
    return event_type in CANONICAL_EVENT_WHITELIST

def log_event_rejection(event_type: str, reason: str):
    """Log rejected events as DEBUG (not error)."""
    write_log("tentaculo_link", f"event_rejected:type={event_type}:reason={reason}", level="DEBUG")

# ============ CANONICAL EVENT SCHEMAS (PHASE V1-V2) ============

CANONICAL_EVENT_SCHEMAS = {
    "system.alert": {
        "required": ["alert_id", "severity", "message", "timestamp"],
        "types": {"alert_id": str, "severity": str, "message": str, "timestamp": int},
        "nature": "incident",
        "max_payload": 2048,
    },
    "system.correlation.updated": {
        "required": ["correlation_id", "related_events", "strength", "timestamp"],
        "types": {"correlation_id": str, "related_events": list, "strength": (int, float), "timestamp": int},
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
        "types": {"decision_id": str, "summary": str, "confidence": (int, float), "timestamp": int},
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
    write_log("tentaculo_link", f"event_rejected:type={event_type}:reason={reason}", level="DEBUG")


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
                    log_event_rejection(event_type, f"invalid type for {field}: expected {expected_type}, got {type(value).__name__}")
                    return None
            else:
                if not isinstance(value, expected_type):
                    log_event_rejection(event_type, f"invalid type for {field}: expected {expected_type.__name__}, got {type(value).__name__}")
                    return None
    
    # Check payload size
    payload_json = json.dumps(event)
    if len(payload_json.encode('utf-8')) > schema["max_payload"]:
        log_event_rejection(event_type, f"payload exceeds max size: {len(payload_json)} > {schema['max_payload']}")
        return None
    
    return event


def normalize_event(event: dict) -> dict:
    """
    PHASE V2: Normalize and tag event internally.
    - Ensure timestamp (milliseconds)
    - Add schema_version (internal only, not sent to Operator UI)
    """
    if "timestamp" not in event:
        event["timestamp"] = int(time.time() * 1000)
    
    # Tag with schema version for internal tracking
    event["_schema_version"] = "v1.0"
    
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
    write_log("tentaculo_link", f"event_validated_and_normalized:type={event_type}", level="DEBUG")
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
        - Log errors as DEBUG only
        """
        event_type = event.get("type", "unknown")
        
        # Final validation (redundant but safe)
        if not validate_event_type(event_type):
            log_event_rejection(event_type, "broadcast attempted with non-canonical type")
            return
        
        # Remove internal tags before sending to Operator
        event_clean = {k: v for k, v in event.items() if not k.startswith("_")}
        
        for client_id, conn in list(self.connections.items()):
            try:
                await conn.send_json(event_clean)
                write_log("tentaculo_link", f"broadcast_sent:type={event_type}:client={client_id}", level="DEBUG")
            except Exception as e:
                # Client disconnected or error; silently skip
                write_log("tentaculo_link", f"broadcast_failed:client={client_id}:error={str(e)}", level="DEBUG")


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = "anonymous"):
    """
    WebSocket endpoint for Operator clients.
    Receives and validates canonical events only.
    Non-canonical events are rejected silently.
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
                # Validate event against canonical whitelist
                validated = await validate_and_filter_event(event)
                if validated:
                    # Event is canonical; broadcast to all clients
                    await manager.broadcast(validated)
                # else: event rejected; no broadcast, no echo
            except json.JSONDecodeError:
                log_event_rejection("malformed", "invalid JSON")
                # Don't echo; connection stays open for next valid event
    except WebSocketDisconnect:
        await manager.disconnect(client_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
