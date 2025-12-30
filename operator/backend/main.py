import asyncio
import json
import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from config.forensics import write_log
from config.settings import settings
from config.tokens import get_token

APP_VERSION = "7.0"

VX11_TOKEN = (
    get_token("VX11_OPERATOR_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
TOKEN_HEADER = settings.token_header

RATE_LIMIT_WINDOW_SEC = int(os.environ.get("VX11_OPERATOR_RATE_WINDOW_SEC", "60"))
RATE_LIMIT_MAX = int(os.environ.get("VX11_OPERATOR_RATE_LIMIT", "60"))
RATE_STATE: Dict[str, list[float]] = {}

AUDIT_LOG_PATH = os.environ.get(
    "VX11_OPERATOR_AUDIT_LOG",
    "/app/logs/operator_backend_audit.jsonl",
)
SCORECARD_PATH = os.environ.get(
    "VX11_SCORECARD_PATH", "/app/docs/audit/SCORECARD.json"
)
PERCENTAGES_PATH = os.environ.get(
    "VX11_PERCENTAGES_PATH", "/app/docs/audit/PERCENTAGES.json"
)

TENTACULO_BASE = settings.tentaculo_link_url.rstrip("/")


class OperatorChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "local"
    metadata: Optional[Dict[str, Any]] = None


class ExplorerQueryRequest(BaseModel):
    preset_id: str = Field(..., description="Preset identifier")
    params: Dict[str, Any] = Field(default_factory=dict)


class PowerWindowRequest(BaseModel):
    services: list[str]
    ttl_sec: Optional[int] = 600
    mode: str = "ttl"
    reason: str = "operator_manual"


class TokenGuard:
    def __call__(self, x_vx11_token: Optional[str] = Header(None)) -> bool:
        if settings.enable_auth:
            if not x_vx11_token:
                raise HTTPException(status_code=401, detail="auth_required")
            if x_vx11_token != VX11_TOKEN:
                raise HTTPException(status_code=403, detail="forbidden")
        return True


token_guard = TokenGuard()

app = FastAPI(title="VX11 Operator Backend", version=APP_VERSION)


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type and not isinstance(response, StreamingResponse):
        try:
            body = response.body
            if body:
                payload = json.loads(body)
                if isinstance(payload, dict) and "correlation_id" not in payload:
                    payload["correlation_id"] = correlation_id
                    headers = dict(response.headers)
                    headers.pop("content-length", None)
                    return JSONResponse(
                        status_code=response.status_code,
                        content=payload,
                        headers=headers,
                    )
        except Exception:
            return response
    return response


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _correlation_id(request: Request, x_correlation_id: Optional[str]) -> str:
    return getattr(request.state, "correlation_id", None) or x_correlation_id or str(
        uuid.uuid4()
    )


def _off_by_policy(
    correlation_id: str, service: str = "operator_backend"
) -> JSONResponse:
    payload = {
        "status": "OFF_BY_POLICY",
        "service": service,
        "message": "Disabled by SOLO_MADRE policy",
        "correlation_id": correlation_id,
        "recommended_action": "Ask Madre to open operator window",
    }
    return JSONResponse(status_code=403, content=payload)


def _off_by_policy_with_runbook(
    correlation_id: str, service: str, runbook: str
) -> JSONResponse:
    payload = {
        "status": "OFF_BY_POLICY",
        "service": service,
        "message": "Disabled by SOLO_MADRE policy",
        "correlation_id": correlation_id,
        "recommended_action": "Ask Madre to open operator window",
        "runbook": runbook,
    }
    return JSONResponse(status_code=403, content=payload)


async def get_correlation_id(
    request: Request, x_correlation_id: Optional[str] = Header(None)
) -> str:
    return _correlation_id(request, x_correlation_id)


def _rate_limit_key(request: Request) -> str:
    token = request.headers.get(TOKEN_HEADER, "")
    ip = request.client.host if request.client else "unknown"
    return f"{token}:{ip}"


def _rate_limit_ok(identifier: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SEC
    recent = [t for t in RATE_STATE.get(identifier, []) if t >= window_start]
    if len(recent) >= RATE_LIMIT_MAX:
        RATE_STATE[identifier] = recent
        return False
    recent.append(now)
    RATE_STATE[identifier] = recent
    return True


def _write_audit(event: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as exc:
        write_log("operator_backend", f"audit_log_error:{exc}", level="WARNING")


def _load_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except Exception as exc:
        write_log("operator_backend", f"json_read_error:{path}:{exc}", level="WARNING")
    return None


def _tail_lines(path: str, limit: int = 200) -> list[str]:
    if limit <= 0:
        return []
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return list(deque(handle, maxlen=limit))
    except Exception as exc:
        write_log("operator_backend", f"log_tail_error:{path}:{exc}", level="WARNING")
        return []


def _intent_response(
    action: str, correlation_id: str, payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    intent_id = f"{action}_{uuid.uuid4()}"
    _write_audit(
        {
            "event": action,
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
            "payload": payload or {},
            "intent_id": intent_id,
        }
    )
    return {
        "status": "INTENT_QUEUED",
        "intent_id": intent_id,
        "action": action,
        "message": "Intent queued for Madre review",
    }


OPERATOR_SETTINGS: Dict[str, Any] = {
    "appearance": {"theme": "dark", "language": "en"},
    "chat": {"model": "deepseek-r1", "temperature": 0.7},
    "security": {"enable_api_logs": False, "enable_debug_mode": False},
    "notifications": {"enable_events": True, "events_level": "info"},
}


async def _call_tentaculo(
    method: str,
    path: str,
    correlation_id: str,
    payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = 8.0,
) -> httpx.Response:
    headers = {TOKEN_HEADER: VX11_TOKEN, "X-Correlation-Id": correlation_id}
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.request(
            method,
            f"{TENTACULO_BASE}{path}",
            headers=headers,
            json=payload,
            params=params,
        )


async def _get_window_status(correlation_id: str) -> Dict[str, Any]:
    response = await _call_tentaculo(
        "GET", "/api/window/status", correlation_id, timeout=5.0
    )
    if response.status_code >= 400:
        return {
            "mode": "solo_madre",
            "services": ["madre", "redis"],
            "degraded": True,
            "reason": "window_status_unavailable",
        }
    payload = response.json()
    services = set(payload.get("services", []))
    services.update({"tentaculo_link"})
    payload["services"] = list(services)
    return payload


async def _get_core_health(correlation_id: str) -> Dict[str, Any]:
    response = await _call_tentaculo(
        "GET", "/api/internal/core-health", correlation_id, timeout=5.0
    )
    if response.status_code >= 400:
        return {"status": "degraded", "services": {}}
    return response.json()


@app.get("/operator/api/health")
async def health(correlation_id: str = Depends(get_correlation_id)):
    return {
        "status": "ok",
        "service": "operator_backend",
        "version": APP_VERSION,
        "timestamp": _now_iso(),
    }


@app.get("/operator/api/env")
async def env_status(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    return {
        "service": "operator_backend",
        "version": APP_VERSION,
        "policy": window.get("mode", "solo_madre"),
        "window": window,
        "timestamp": _now_iso(),
    }


@app.get("/operator/api/status")
async def operator_status(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    core = await _get_core_health(correlation_id)
    window = await _get_window_status(correlation_id)
    degraded = core.get("status") != "ok"
    return {
        "status": "ok",
        "policy": window.get("mode", "solo_madre"),
        "core_services": core.get("services", {}),
        "degraded": degraded,
        "window": window,
    }


@app.get("/operator/api/modules")
async def modules(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    core = await _get_core_health(correlation_id)
    window = await _get_window_status(correlation_id)
    allowed = set(window.get("services", []))
    modules: Dict[str, Any] = {}

    for name, info in core.get("services", {}).items():
        modules[name] = {
            "status": info.get("status", "unknown"),
            "reason": info.get("reason"),
            "category": "core",
        }

    optional = ["switch", "hermes", "hormiguero", "manifestator", "spawner"]
    for name in optional:
        modules[name] = {
            "status": "UP" if name in allowed else "OFF_BY_POLICY",
            "reason": "window_active" if name in allowed else "solo_madre",
            "category": "optional",
        }

    modules["operator_backend"] = {
        "status": "UP",
        "reason": "operator_profile",
        "category": "operator",
    }

    return {"modules": modules}


@app.get("/operator/api/topology")
async def topology(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    core = await _get_core_health(correlation_id)
    window = await _get_window_status(correlation_id)
    allowed = set(window.get("services", []))

    def status_for(name: str) -> str:
        if name in allowed:
            return core.get("services", {}).get(name, {}).get("status", "UP")
        return "OFF_BY_POLICY"

    services = {
        "tentaculo_link": core.get("services", {}).get("tentaculo_link", {}),
        "madre": core.get("services", {}).get("madre", {}),
        "redis": core.get("services", {}).get("redis", {}),
        "switch": {"status": status_for("switch")},
        "hermes": {"status": status_for("hermes")},
        "hormiguero": {"status": status_for("hormiguero")},
        "manifestator": {"status": status_for("manifestator")},
        "spawner": {"status": status_for("spawner")},
    }

    return {
        "status": "ok",
        "services": services,
        "policy": window.get("mode", "solo_madre"),
    }


@app.get("/operator/api/windows")
async def windows(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    status = await _get_window_status(correlation_id)
    return status


@app.post("/operator/api/chat/window/open")
async def open_window(
    req: PowerWindowRequest,
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    response = await _call_tentaculo(
        "POST", "/api/window/open", correlation_id, payload=req.dict()
    )
    _write_audit(
        {
            "event": "window_open",
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
            "payload": req.dict(),
        }
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.post("/operator/api/chat/window/close")
async def close_window(
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    response = await _call_tentaculo("POST", "/api/window/close", correlation_id)
    _write_audit(
        {
            "event": "window_close",
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
        }
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/chat/window/status")
async def window_status(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    status = await _get_window_status(correlation_id)
    return status


@app.post("/operator/api/chat")
async def chat(
    req: OperatorChatRequest,
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")

    window = await _get_window_status(correlation_id)
    if window.get("mode") != "window_active":
        return _off_by_policy(correlation_id)

    payload = req.dict()
    response = await _call_tentaculo(
        "POST", "/operator/chat/ask", correlation_id, payload=payload, timeout=10.0
    )
    _write_audit(
        {
            "event": "chat",
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
            "payload": {"session_id": req.session_id, "message": req.message},
        }
    )
    data = response.json()
    return JSONResponse(status_code=response.status_code, content=data)


@app.get("/operator/api/events")
async def events(
    limit: int = 10,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo(
        "GET", "/api/events", correlation_id, params={"limit": limit}
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/events/stream")
async def events_stream(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    heartbeat_sec = int(os.environ.get("VX11_OPERATOR_SSE_HEARTBEAT", "15"))
    poll_interval_sec = int(os.environ.get("VX11_OPERATOR_SSE_POLL", "60"))

    async def stream() -> Any:
        last_poll = 0.0
        retry_ms = 10000
        yield f"retry: {retry_ms}\n\n"
        while True:
            try:
                now = time.time()
                if now - last_poll >= poll_interval_sec:
                    last_poll = now
                    window = await _get_window_status(correlation_id)
                    events_resp = await _call_tentaculo(
                        "GET",
                        "/api/events",
                        correlation_id,
                        params={"limit": 5},
                        timeout=5.0,
                    )
                    payload = {
                        "type": "snapshot",
                        "window": window,
                        "events": events_resp.json().get("events", []),
                        "timestamp": _now_iso(),
                        "correlation_id": correlation_id,
                    }
                    yield f"event: snapshot\n"
                    yield f"data: {json.dumps(payload)}\n\n"
                heartbeat = {
                    "type": "heartbeat",
                    "timestamp": _now_iso(),
                    "correlation_id": correlation_id,
                }
                yield f"event: heartbeat\n"
                yield f"data: {json.dumps(heartbeat)}\n\n"
                await asyncio.sleep(heartbeat_sec)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                error_payload = {
                    "type": "error",
                    "message": str(exc),
                    "timestamp": _now_iso(),
                    "correlation_id": correlation_id,
                }
                yield f"event: error\n"
                yield f"data: {json.dumps(error_payload)}\n\n"
                await asyncio.sleep(heartbeat_sec)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/operator/api/logs/tail")
async def logs_tail(
    limit: int = 200,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    lines = [line.rstrip("\n") for line in _tail_lines(AUDIT_LOG_PATH, limit=limit)]
    return {
        "status": "ok",
        "source": AUDIT_LOG_PATH,
        "lines": lines,
    }


@app.get("/operator/api/audit/runs")
async def audit_runs(
    limit: int = 20,
    offset: int = 0,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo(
        "GET",
        "/api/audit/runs",
        correlation_id,
        params={"limit": limit, "offset": offset},
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/audit/runs/{run_id}")
async def audit_run_detail(
    run_id: str,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo(
        "GET", f"/api/audit/{run_id}", correlation_id
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/explorer/presets")
async def explorer_presets(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    presets = [
        {
            "id": "events_recent",
            "label": "Recent Events",
            "description": "Last 50 events (24h)",
            "params": {"limit": 50, "hours_back": 24},
        },
        {
            "id": "audit_runs",
            "label": "Audit Runs",
            "description": "Latest audit runs",
            "params": {"limit": 20},
        },
    ]
    return {"presets": presets}


@app.post("/operator/api/explorer/query")
async def explorer_query(
    req: ExplorerQueryRequest,
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")

    if req.preset_id == "events_recent":
        params = {
            "limit": req.params.get("limit", 50),
            "hours_back": req.params.get("hours_back", 24),
        }
        response = await _call_tentaculo(
            "GET", "/api/events", correlation_id, params=params
        )
        return JSONResponse(status_code=response.status_code, content=response.json())

    if req.preset_id == "audit_runs":
        params = {"limit": req.params.get("limit", 20)}
        response = await _call_tentaculo(
            "GET", "/api/audit/runs", correlation_id, params=params
        )
        return JSONResponse(status_code=response.status_code, content=response.json())

    raise HTTPException(status_code=400, detail="invalid_preset")


@app.post("/operator/api/madre/plan")
async def madre_plan(
    payload: Dict[str, Any],
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if window.get("mode") != "window_active":
        return _off_by_policy(correlation_id, service="madre")
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    intent = _intent_response("madre_plan", correlation_id, payload)
    return {
        "status": intent["status"],
        "intent_id": intent["intent_id"],
        "action": intent["action"],
        "message": "Madre plan request queued",
    }


@app.post("/operator/api/madre/execute")
async def madre_execute(
    payload: Dict[str, Any],
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if window.get("mode") != "window_active":
        return _off_by_policy(correlation_id, service="madre")
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    intent = _intent_response("madre_execute", correlation_id, payload)
    return {
        "status": intent["status"],
        "intent_id": intent["intent_id"],
        "action": intent["action"],
        "message": "Madre execute request queued",
    }


@app.post("/operator/api/madre/cancel")
async def madre_cancel(
    payload: Dict[str, Any],
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if window.get("mode") != "window_active":
        return _off_by_policy(correlation_id, service="madre")
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    intent = _intent_response("madre_cancel", correlation_id, payload)
    return {
        "status": intent["status"],
        "intent_id": intent["intent_id"],
        "action": intent["action"],
        "message": "Madre cancel request queued",
    }


@app.get("/operator/api/madre/status/{intent_id}")
async def madre_status(
    intent_id: str,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if window.get("mode") != "window_active":
        return _off_by_policy(correlation_id, service="madre")
    return {
        "status": "unknown",
        "intent_id": intent_id,
        "message": "Intent tracking not configured; consult Madre logs",
    }


@app.get("/operator/api/hormiguero/status")
async def hormiguero_status(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if "hormiguero" not in window.get("services", []):
        return _off_by_policy(correlation_id, service="hormiguero")
    response = await _call_tentaculo(
        "GET", "/hormiguero/queen/status", correlation_id, timeout=5.0
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.post("/operator/api/hormiguero/scan/once")
async def hormiguero_scan_once(
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if "hormiguero" not in window.get("services", []):
        return _off_by_policy(correlation_id, service="hormiguero")
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    response = await _call_tentaculo(
        "POST", "/api/hormiguero/scan/once", correlation_id
    )
    _write_audit(
        {
            "event": "hormiguero_scan_once",
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
        }
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/spawner/status")
async def spawner_status(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo(
        "GET", "/api/spawner/status", correlation_id, timeout=5.0
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/spawner/runs")
async def spawner_runs(
    limit: int = 20,
    offset: int = 0,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo(
        "GET",
        "/api/spawner/runs",
        correlation_id,
        params={"limit": limit, "offset": offset},
        timeout=8.0,
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.post("/operator/api/spawner/submit")
async def spawner_submit(
    payload: Dict[str, Any],
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    response = await _call_tentaculo(
        "POST", "/api/spawner/submit", correlation_id, payload=payload, timeout=12.0
    )
    _write_audit(
        {
            "event": "spawner_submit",
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
            "payload": payload,
        }
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


async def _manifestator_plan(correlation_id: str) -> Dict[str, Any]:
    lanes_resp = await _call_tentaculo(
        "GET", "/api/rails/lanes", correlation_id, timeout=5.0
    )
    rails_resp = await _call_tentaculo(
        "GET", "/api/rails", correlation_id, timeout=5.0
    )
    return {
        "summary": "Manifestator compare plan generated",
        "lanes": lanes_resp.json().get("lanes", []),
        "rails": rails_resp.json().get("rails", []),
        "apply": "prohibited",
    }


@app.get("/operator/api/manifestator/status")
async def manifestator_status(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if "manifestator" not in window.get("services", []):
        return _off_by_policy(correlation_id, service="manifestator")

    response = await _call_tentaculo(
        "GET", "/api/rails/lanes", correlation_id, timeout=5.0
    )
    payload = {
        "status": "ok",
        "lanes": response.json().get("lanes", []),
    }
    return payload


@app.post("/operator/api/manifestator/patchplan")
async def manifestator_patchplan(
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if "manifestator" not in window.get("services", []):
        return _off_by_policy(correlation_id, service="manifestator")
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    plan = await _manifestator_plan(correlation_id)
    _write_audit(
        {
            "event": "manifestator_patchplan",
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
        }
    )
    return {"status": "ok", "plan": plan}


@app.post("/operator/api/manifestator/compare")
async def manifestator_compare(
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if "manifestator" not in window.get("services", []):
        return _off_by_policy(correlation_id, service="manifestator")
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")

    plan = await _manifestator_plan(correlation_id)

    _write_audit(
        {
            "event": "manifestator_compare",
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
        }
    )

    return {"status": "ok", "plan": plan}


@app.post("/operator/api/manifestator/apply")
async def manifestator_apply(
    payload: Dict[str, Any],
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    window = await _get_window_status(correlation_id)
    if "manifestator" not in window.get("services", []):
        return _off_by_policy(correlation_id, service="manifestator")
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    intent = _intent_response("manifestator_apply", correlation_id, payload)
    return {
        "status": intent["status"],
        "intent_id": intent["intent_id"],
        "action": intent["action"],
        "message": "Manifestator apply request queued; requires Madre approval",
    }


@app.get("/operator/api/shub/status")
async def shub_status(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    return _off_by_policy_with_runbook(
        correlation_id,
        service="shub",
        runbook="Enable shub via Madre power window and configure SHUB_URL in operator_backend.",
    )


@app.get("/operator/api/shub/jobs")
async def shub_jobs(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    return _off_by_policy_with_runbook(
        correlation_id,
        service="shub",
        runbook="Enable shub via Madre power window and configure SHUB_URL in operator_backend.",
    )


@app.post("/operator/api/shub/jobs/submit")
async def shub_jobs_submit(
    payload: Dict[str, Any],
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    _ = payload
    return _off_by_policy_with_runbook(
        correlation_id,
        service="shub",
        runbook="Enable shub via Madre power window and configure SHUB_URL in operator_backend.",
    )


@app.post("/operator/api/assist/deepseek_r1")
async def assist_deepseek(
    payload: Dict[str, Any],
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    _ = payload
    return _off_by_policy_with_runbook(
        correlation_id,
        service="assist",
        runbook="CoDev assist disabled; enable deepseek_r1 in switch and open an operator window.",
    )


@app.get("/operator/api/assist/deepseek_r1/status")
async def assist_deepseek_status(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    return _off_by_policy_with_runbook(
        correlation_id,
        service="assist",
        runbook="CoDev assist disabled; enable deepseek_r1 in switch and open an operator window.",
    )


@app.get("/operator/api/metrics")
async def metrics(
    window_seconds: int = 3600,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo(
        "GET",
        "/api/metrics",
        correlation_id,
        params={"window_seconds": window_seconds},
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/scorecard")
async def scorecard(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    scorecard_data = _load_json(SCORECARD_PATH)
    percentages_data = _load_json(PERCENTAGES_PATH)
    payload = {
        "scorecard": scorecard_data,
        "percentages": percentages_data,
        "availability": {
            "scorecard": scorecard_data is not None,
            "percentages": percentages_data is not None,
        },
    }
    return payload


@app.get("/operator/api/audit")
async def audit_summary(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo(
        "GET", "/api/audit/runs", correlation_id, params={"limit": 20}
    )
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/settings")
async def get_settings(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    return {**OPERATOR_SETTINGS}


@app.post("/operator/api/settings")
async def update_settings(
    payload: Dict[str, Any],
    request: Request,
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    if not _rate_limit_ok(_rate_limit_key(request)):
        raise HTTPException(status_code=429, detail="rate_limited")
    OPERATOR_SETTINGS.update(payload)
    _write_audit(
        {
            "event": "settings_update",
            "correlation_id": correlation_id,
            "timestamp": _now_iso(),
            "payload": payload,
        }
    )
    return {
        "status": "ok",
        "message": "Settings updated",
        "settings": OPERATOR_SETTINGS,
    }


@app.get("/operator/api/rails/lanes")
async def rails_lanes(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo("GET", "/api/rails/lanes", correlation_id)
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/rails")
async def rails(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
):
    response = await _call_tentaculo("GET", "/api/rails", correlation_id)
    return JSONResponse(status_code=response.status_code, content=response.json())


@app.get("/operator/api/healthz")
async def healthz():
    return {"status": "ok"}


ALIAS_ROUTES = [
    ("/health", ["GET"], health),
    ("/env", ["GET"], env_status),
    ("/status", ["GET"], operator_status),
    ("/modules", ["GET"], modules),
    ("/topology", ["GET"], topology),
    ("/windows", ["GET"], windows),
    ("/chat/window/open", ["POST"], open_window),
    ("/chat/window/close", ["POST"], close_window),
    ("/chat/window/status", ["GET"], window_status),
    ("/chat", ["POST"], chat),
    ("/events", ["GET"], events),
    ("/events/stream", ["GET"], events_stream),
    ("/logs/tail", ["GET"], logs_tail),
    ("/audit/runs", ["GET"], audit_runs),
    ("/audit/runs/{run_id}", ["GET"], audit_run_detail),
    ("/audit", ["GET"], audit_summary),
    ("/explorer/presets", ["GET"], explorer_presets),
    ("/explorer/query", ["POST"], explorer_query),
    ("/madre/plan", ["POST"], madre_plan),
    ("/madre/execute", ["POST"], madre_execute),
    ("/madre/cancel", ["POST"], madre_cancel),
    ("/madre/status/{intent_id}", ["GET"], madre_status),
    ("/manifestator/status", ["GET"], manifestator_status),
    ("/manifestator/patchplan", ["POST"], manifestator_patchplan),
    ("/manifestator/compare", ["POST"], manifestator_compare),
    ("/manifestator/apply", ["POST"], manifestator_apply),
    ("/hormiguero/status", ["GET"], hormiguero_status),
    ("/hormiguero/scan_once", ["POST"], hormiguero_scan_once),
    ("/spawner/status", ["GET"], spawner_status),
    ("/spawner/runs", ["GET"], spawner_runs),
    ("/spawner/submit", ["POST"], spawner_submit),
    ("/metrics", ["GET"], metrics),
    ("/scorecard", ["GET"], scorecard),
    ("/settings", ["GET"], get_settings),
    ("/settings", ["POST"], update_settings),
    ("/rails/lanes", ["GET"], rails_lanes),
    ("/rails", ["GET"], rails),
    ("/shub/status", ["GET"], shub_status),
    ("/shub/jobs", ["GET"], shub_jobs),
    ("/shub/jobs/submit", ["POST"], shub_jobs_submit),
    ("/assist/deepseek_r1", ["POST"], assist_deepseek),
    ("/assist/deepseek_r1/status", ["GET"], assist_deepseek_status),
]


def _register_aliases(prefix: str, include_in_schema: bool) -> None:
    for path, methods, handler in ALIAS_ROUTES:
        app.add_api_route(
            f"{prefix}{path}",
            handler,
            methods=methods,
            include_in_schema=include_in_schema,
        )


_register_aliases("/api/v1", include_in_schema=True)
_register_aliases("/api", include_in_schema=False)
