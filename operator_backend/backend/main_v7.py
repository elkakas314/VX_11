"""
Operator Backend v7.0 - FastAPI
Clean, modular, integrates with new BD schema + CONTEXT7 + Switch
Endpoints: chat, session, shub/dashboard, vx11/overview, resources, browser/task
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Depends,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config.settings import settings
from config.tokens import get_token, load_tokens
from config.forensics import write_log
from config.db_schema import (
    get_session,
    OperatorSession,
    OperatorMessage,
    OperatorToolCall,
    OperatorSwitchAdjustment,
    OperatorBrowserTask,
)
from .browser import BrowserClient
from .switch_integration import SwitchClient, TentaculoLinkClient

# Load tokens
load_tokens()
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


# ============ REQUEST/RESPONSE MODELS ============


class ChatRequest(BaseModel):
    """Chat message request."""

    session_id: Optional[str] = None
    user_id: Optional[str] = "local"
    message: str
    context_summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat message response."""

    session_id: str
    response: str
    tool_calls: Optional[List[Dict[str, Any]]] = None


class SessionInfo(BaseModel):
    """Session history."""

    session_id: str
    user_id: str
    created_at: str
    message_count: int
    messages: List[Dict[str, Any]]


class ShubDashboard(BaseModel):
    """Shub status dashboard."""

    status: str
    modules: Dict[str, Any]


class VX11Overview(BaseModel):
    """VX11 system overview."""

    status: str
    healthy_modules: int
    total_modules: int
    modules: Dict[str, Any]


# ============ DEPENDENCIES ============


class TokenGuard:
    """Token validation."""

    def __call__(self, x_vx11_token: str = Header(None)) -> bool:
        if settings.enable_auth:
            if not x_vx11_token:
                raise HTTPException(status_code=401, detail="auth_required")
            if x_vx11_token != VX11_TOKEN:
                raise HTTPException(status_code=403, detail="forbidden")
        return True


token_guard = TokenGuard()


# ============ LIFESPAN ============


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown."""
    write_log("operator_backend", "startup:v7_initialized")
    try:
        yield
    finally:
        write_log("operator_backend", "shutdown:v7_closed")


# ============ APP SETUP ============

app = FastAPI(
    title="VX11 Operator Backend",
    version="7.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ HEALTH ============


@app.get("/health")
async def health():
    """Simple health check."""
    return {
        "status": "ok",
        "module": "operator",
        "version": "7.0",
    }


# ============ INTENT ENDPOINT (for legacy test compat) ============


class IntentRequest(BaseModel):
    """Intent routing request."""

    intent_type: str
    data: Dict[str, Any]
    target: str
    metadata: Optional[Dict[str, Any]] = None


@app.post("/intent")
async def intent_handler(req: IntentRequest, _: bool = Depends(token_guard)):
    """Route intents to target module (legacy endpoint)."""
    # Canonical proxy: if target is "switch", delegate via Tentáculo Link
    if req.target == "switch":
        msg = (req.data.get("message", "") or "").strip()
        metadata = req.metadata or {}

        # Derive mode-specific metadata if needed
        # Detect mixing/mezcla intent (Spanish: "mezcla", English: "mix", "mixing", "blend")
        if any(word in msg.lower() for word in ["mix", "mezcla", "mixing", "blend"]):
            metadata["mode"] = "mix"
            metadata["mix_ops"] = ["normalize", "eq", "limiter"]

        tentaculo_client = TentaculoLinkClient()
        response = await tentaculo_client.query_task(
            task_type=req.intent_type or "chat",
            payload={"message": msg, "metadata": metadata},
            metadata=metadata,
            intent_type=req.intent_type or "task",
        )

        write_log("operator_backend", f"intent:{req.intent_type}:routed_to_tentaculo")
        return {
            "status": "ok",
            "intent_type": req.intent_type,
            "target": "switch",
            "response": response,
        }

    write_log(
        "operator_backend", f"intent:{req.intent_type}:unknown_target:{req.target}"
    )
    raise HTTPException(status_code=400, detail=f"unknown target: {req.target}")


# ============ CHAT ENDPOINT ============


@app.post("/operator/chat")
async def operator_chat(
    req: ChatRequest,
    _: bool = Depends(token_guard),
):
    """Chat endpoint with BD persistence + Tentáculo Link integration."""
    session_id = req.session_id or str(uuid.uuid4())
    user_id = req.user_id or "local"

    db = None
    try:
        db = get_session("vx11")

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
            content=req.message,
            message_metadata=json.dumps(req.metadata or {}),
        )
        db.add(user_msg)
        db.commit()

        # Query Tentáculo Link for canonical routing to Switch
        tentaculo_client = TentaculoLinkClient()
        metadata = dict(req.metadata or {})
        if req.context_summary:
            metadata["context_summary"] = req.context_summary

        switch_result = await tentaculo_client.query_chat(
            message=req.message,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata,
        )

        response_text = (
            switch_result.get("response")
            or switch_result.get("message")
            or f"Received: {req.message}"
        )

        # Store assistant response
        assistant_msg = OperatorMessage(
            session_id=session_id,
            role="assistant",
            content=response_text,
        )
        db.add(assistant_msg)
        db.commit()

        write_log("operator_backend", f"chat:{session_id}:success")

        return ChatResponse(
            session_id=session_id,
            response=response_text,
        )

    except Exception as exc:
        write_log("operator_backend", f"chat_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if db:
            db.close()


# ============ SESSION ENDPOINT ============


@app.get("/operator/session/{session_id}")
async def operator_session(
    session_id: str,
    _: bool = Depends(token_guard),
):
    """Get session history."""
    try:
        db = get_session("vx11")

        session = db.query(OperatorSession).filter_by(session_id=session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="session_not_found")

        messages = db.query(OperatorMessage).filter_by(session_id=session_id).all()

        result = SessionInfo(
            session_id=session.session_id,
            user_id=session.user_id,
            created_at=session.created_at.isoformat(),
            message_count=len(messages),
            messages=[
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
        )

        write_log("operator_backend", f"session_retrieved:{session_id}")
        return result

    except HTTPException:
        raise
    except Exception as exc:
        write_log("operator_backend", f"session_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


# ============ VX11 OVERVIEW ============


@app.get("/operator/vx11/overview")
async def vx11_overview(_: bool = Depends(token_guard)):
    """Get VX11 system overview (stub for now)."""
    # Query Tentáculo Link /health to build real overview
    overview = {
        "status": "partial",
        "healthy_modules": 0,
        "total_modules": 10,
        "modules": {},
    }
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://localhost:8000/health")
            r.raise_for_status()
            tentaculo = r.json()
    except Exception:
        tentaculo = {"status": "offline"}

    modules = {
        "tentaculo_link": tentaculo,
        "madre": {"status": "ok"},
        "switch": {"status": "ok"},
        "hermes": {"status": "ok"},
        "hormiguero": {"status": "ok"},
        "spawner": {"status": "ok"},
        "manifestator": {"status": "ok"},
        "mcp": {"status": "ok"},
        "shub": {"status": "ok"},
        "operator": {"status": "ok", "version": "7.0"},
    }

    healthy = sum(1 for v in modules.values() if v.get("status") == "ok")
    overview.update(
        {
            "status": "ok" if healthy >= 1 else "degraded",
            "healthy_modules": healthy,
            "modules": modules,
        }
    )
    write_log("operator_backend", "vx11_overview:requested")
    return overview


# ============ SHUB DASHBOARD ============


@app.get("/operator/shub/dashboard")
async def shub_dashboard(_: bool = Depends(token_guard)):
    """Get Shub dashboard (stub for now)."""
    # Query Shubniggurath for health and metrics
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            h = await client.get("http://localhost:8007/health")
            h.raise_for_status()
            health = h.json()
            m = await client.post(
                "http://localhost:8007/metrics",
                json={"include": ["sessions", "resources", "queue"]},
            )
            m.raise_for_status()
            metrics = m.json()
    except Exception:
        health = {"status": "offline"}
        metrics = {
            "active_sessions": 0,
            "projects": [],
            "resources": {"cpu_percent": 0.0, "memory_mb": 0},
        }

    dashboard = {
        "status": health.get("status", "offline"),
        "shub_health": health.get("status", "offline"),
        "active_sessions": metrics.get("active_sessions", 0),
        "projects": metrics.get("projects", []),
        "resources": metrics.get("resources", {}),
    }
    write_log("operator_backend", "shub_dashboard:requested")
    return dashboard


# ============ RESOURCES (HERMES) ============


@app.get("/operator/resources")
async def resources(_: bool = Depends(token_guard)):
    """Get available resources (CLI tools + models)."""
    # Query Hermes for tools/resources
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            h = await client.get("http://localhost:8003/health")
            h.raise_for_status()
            health = h.json()
            t = await client.get("http://localhost:8003/tools")
            t.raise_for_status()
            tools = t.json()
    except Exception:
        health = {"status": "offline"}
        tools = {"cli_tools": [], "local_models": []}

    resources_info = {
        "status": health.get("status", "offline"),
        "cli_tools": tools.get(
            "cli_tools", [{"name": "deepseek_r1", "available": False, "version": "1.0"}]
        ),
        "local_models": tools.get("local_models", []),
        "max_tokens": 1000,
        "available_tokens": 950,
    }
    write_log("operator_backend", "resources:requested")
    return resources_info


# ============ BROWSER TASK (PLACEHOLDER) ============


class BrowserTaskRequest(BaseModel):
    """Browser task request."""

    url: str
    session_id: Optional[str] = None


@app.post("/operator/browser/task")
async def browser_task(
    req: BrowserTaskRequest,
    _: bool = Depends(token_guard),
):
    """Create browser task (Playwright real implementation)."""
    session_id = req.session_id or str(uuid.uuid4())
    task_id = str(uuid.uuid4())
    db = None

    try:
        db = get_session("vx11")

        # Create task in DB
        browser_task = OperatorBrowserTask(
            id=task_id,
            session_id=session_id,
            url=req.url,
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(browser_task)
        db.commit()

        # Execute browser task asynchronously
        client = BrowserClient(impl="playwright", headless=True, timeout_ms=30000)
        result = await client.navigate(req.url)

        # Update task with result
        browser_task.status = result.get("status", "error")
        browser_task.screenshot_path = result.get("screenshot_path")
        browser_task.text_snippet = result.get("text_snippet")
        browser_task.error_message = result.get("error")
        browser_task.completed_at = datetime.utcnow()
        db.commit()

        write_log(
            "operator_backend",
            f"browser_task:completed:{task_id}:{result.get('status')}",
        )

        return {
            "task_id": task_id,
            "status": "completed",
            "url": req.url,
            "session_id": session_id,
            "result": result,
        }

    except Exception as exc:
        write_log(
            "operator_backend", f"browser_task_error:{task_id}:{exc}", level="ERROR"
        )
        if db and "browser_task" in locals():
            browser_task.status = "error"
            browser_task.error_message = str(exc)
            browser_task.completed_at = datetime.utcnow()
            try:
                db.commit()
            except:
                pass
        raise HTTPException(status_code=500, detail="browser_task_failed")
    finally:
        if db:
            db.close()


@app.get("/operator/browser/task/{task_id}")
async def browser_task_status(
    task_id: str,
    _: bool = Depends(token_guard),
):
    """Get browser task status and result."""
    db = None
    try:
        db = get_session("vx11")

        # Query task from DB
        task = db.query(OperatorBrowserTask).filter_by(id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="task_not_found")

        return {
            "task_id": task.id,
            "status": task.status,
            "url": task.url,
            "screenshot_path": task.screenshot_path,
            "text_snippet": task.text_snippet,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat(),
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
        }

    except HTTPException:
        raise
    except Exception as exc:
        write_log(
            "operator_backend",
            f"browser_task_status_error:{task_id}:{exc}",
            level="ERROR",
        )
        raise HTTPException(status_code=500, detail="task_status_error")
    finally:
        if db:
            db.close()


# ============ TOOL CALLS TRACKING ============


@app.post("/operator/tool/call")
async def tool_call_track(
    message_id: int,
    tool_name: str,
    status: str,
    duration_ms: Optional[int] = None,
    result: Optional[Dict[str, Any]] = None,
    _: bool = Depends(token_guard),
):
    """Track tool call execution."""
    try:
        db = get_session("vx11")

        tool_call = OperatorToolCall(
            message_id=message_id,
            tool_name=tool_name,
            status=status,
            duration_ms=duration_ms,
            result=json.dumps(result) if result else None,
        )
        db.add(tool_call)
        db.commit()

        write_log("operator_backend", f"tool_call:tracked:{tool_name}:{status}")
        return {"status": "ok"}

    except Exception as exc:
        write_log("operator_backend", f"tool_call_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


# ============ SWITCH ADJUSTMENT TRACKING ============


@app.post("/operator/switch/adjustment")
async def switch_adjustment_track(
    session_id: str,
    before_config: Dict[str, Any],
    after_config: Dict[str, Any],
    reason: str,
    _: bool = Depends(token_guard),
):
    """Track Switch parameter adjustments."""
    try:
        db = get_session("vx11")

        adjustment = OperatorSwitchAdjustment(
            session_id=session_id,
            before_config=json.dumps(before_config),
            after_config=json.dumps(after_config),
            reason=reason,
            applied=False,
        )
        db.add(adjustment)
        db.commit()

        write_log("operator_backend", f"switch_adjustment:recorded:{session_id}")
        return {"status": "ok", "adjustment_id": adjustment.id}

    except Exception as exc:
        write_log("operator_backend", f"switch_adjustment_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


# ============ ERROR HANDLERS ============


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler with logging."""
    write_log(
        "operator_backend",
        f"http_error:{exc.status_code}:{exc.detail}",
        level="WARNING",
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


# ============ SWITCH FEEDBACK LOOP ============


@app.post("/operator/switch/feedback")
async def record_switch_feedback(
    _: bool = Depends(token_guard),
    engine: str = "default",
    success: bool = True,
    latency_ms: int = 0,
    tokens_used: int = 0,
    error_msg: Optional[str] = None,
) -> Dict[str, Any]:
    """Record Switch performance feedback for adaptive learning."""
    db = None
    try:
        db = get_session("vx11")

        # Create adjustment record
        adjustment = OperatorSwitchAdjustment(
            session_id=str(uuid.uuid4()),
            engine_used=engine,
            success=success,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            error_message=error_msg or "",
            feedback_timestamp=datetime.utcnow(),
        )
        db.add(adjustment)
        db.commit()

        write_log(
            "operator_backend",
            f"switch_feedback:{engine}:success={success}:latency={latency_ms}ms",
        )

        return {"status": "recorded", "adjustment_id": adjustment.id}

    except Exception as e:
        write_log("operator_backend", f"switch_feedback_error:{str(e)}", level="ERROR")
        raise HTTPException(status_code=500, detail="feedback_error")

    finally:
        if db:
            db.close()


# ============ WEBSOCKET (STUB) ============


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for canonical VX11 events.

    Expected incoming message: JSON with keys {"event_type": "...", "data": {...}}
    Supported event types: message_received, tool_call_requested, tool_result_received,
    plan_updated, status_changed, error_reported
    """
    try:
        await websocket.accept()
        write_log("operator_backend", f"ws_connect:{session_id}")

        async def format_canonical_event(event_type: str, data: dict) -> dict:
            from datetime import datetime

            valid = {
                "message_received",
                "tool_call_requested",
                "tool_result_received",
                "plan_updated",
                "status_changed",
                "error_reported",
            }
            if event_type not in valid:
                event_type = "status_changed"
                data["note"] = f"unknown_event_type:{event_type}"
            return {
                "type": event_type,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }

        # Event loop
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                write_log("operator_backend", f"ws_disconnect:{session_id}")
                break

            try:
                import json

                payload = json.loads(raw) if raw and raw.strip().startswith("{") else {"event_type": "message_received", "data": {"message": raw}}
                event_type = payload.get("event_type", "message_received")
                data = payload.get("data", {})
                canonical = await format_canonical_event(event_type, data)
                await websocket.send_json(canonical)
                write_log("operator_backend", f"ws_event:{session_id}:{event_type}")
            except json.JSONDecodeError:
                err = {"error": "invalid_json", "raw": raw}
                canonical = await format_canonical_event("error_reported", err)
                await websocket.send_json(canonical)
                write_log("operator_backend", f"ws_json_error:{session_id}")
            except Exception as exc:
                err = {"error": str(exc)}
                canonical = await format_canonical_event("error_reported", err)
                await websocket.send_json(canonical)
                write_log("operator_backend", f"ws_processing_error:{session_id}:{exc}",)

    except Exception:
        write_log("operator_backend", f"ws_error:{session_id}")
    finally:
        write_log("operator_backend", f"ws_disconnect:{session_id}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8011)
