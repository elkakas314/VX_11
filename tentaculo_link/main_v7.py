"""
Tentáculo Link v7.0 - Gateway Refactored






























































































































































































































































































































































































**Versión:** 7.0 | **Fase:** G | **Actualizado:** 2025-12-14---- `config/settings.py` — Configuración centralizada- `tentaculo_link/context7_middleware.py` — Context-7 sessions TTL- `tentaculo_link/routes.py` — Route table static- `tentaculo_link/clients.py` — ModuleClient + CircuitBreaker- `tentaculo_link/main_v7.py` — Endpoints principales## Referencias---```    - hermes    - switch    - madre  depends_on:    - vx11  networks:    # ... etc    - SWITCH_PORT=8002    - MADRE_PORT=8001    - ENABLE_AUTH=true    - VX11_TENTACULO_LINK_TOKEN=vx11-local-token    - TENTACULO_LINK_PORT=8000  environment:    - "8000:8000"  ports:  image: vx11/tentaculo_link:latesttentaculo_link:# docker-compose.yml```yaml## Docker Compose---```# context7.add_message(...)# context7 = get_context7_manager()```pythonComentar middleware en `main_v7.py`:### Deshabilitar Context-7```self.circuit_breaker = None  # o usar un mock que siempre retorna should_attempt=True# En ModuleClient.__init__()```pythonModificar `clients.py`:### Deshabilitar Circuit Breaker```ENABLE_AUTH=false# .env```bash### Deshabilitar Autenticación (Solo Dev Local)## Desactivar Características (Opcionales)---3. Si es manual: enviar POST `/vx11/context-7/cleanup` (si existe endpoint)2. Verificar logs de cleanup: `grep "cleanup_expired" logs/`1. Chequear que `CONTEXT7_CLEANUP_INTERVAL` está configurado**Solución:****Causa:** Context-7 no limpian sesiones expiradas o cleanup parado**Síntoma:** Memoria crece constantemente### TTL Sessions Acumuladas```curl -H "X-VX11-Token: vx11-local-token" ...# Incluir en requestsexport VX11_TENTACULO_LINK_TOKEN="vx11-local-token"# Asegurar token en env var```bash**Solución:****Causa:** Header `X-VX11-Token` faltante o incorrecto**Síntoma:** `401 Unauthorized`### Token Inválido4. Si necesita forzar reset: reiniciar Tentáculo Link3. Circuit breaker se auto-recuperará tras `recovery_timeout` (default 60s)2. Ver logs del módulo1. Chequear módulo target: `curl http://127.0.0.1:{puerto}/health`**Solución:**- Errores persistentes en el módulo- Módulo respondiendo lentamente (timeouts)- Módulo no disponible (proceso muerto, puerto cerrado)**Causas:****Síntoma:** Responses con `"status": "circuit_open"`### Circuit Breaker Abierto## Troubleshooting---```  http://127.0.0.1:8000/vx11/context-7/sessionscurl -H "X-VX11-Token: vx11-local-token" \# Ver sesiones activas```bash### Context-7 Sessions```  }'    "metadata": {"source": "ui"}    "session_id": "session-001",    "message": "Hola, ¿cómo estás?",  -d '{  -H "Content-Type: application/json" \  -H "X-VX11-Token: vx11-local-token" \curl -X POST http://127.0.0.1:8000/operator/chat \# Route chat to Switch (via Tentáculo Link)```bash### Chat Routing```  http://127.0.0.1:8000/vx11/circuit-breaker/statuscurl -H "X-VX11-Token: vx11-local-token" \# Circuit breaker status# { "ok": true, "modules": {...}, "summary": {...} }curl http://127.0.0.1:8000/vx11/status# Aggregated status (all modules)# { "status": "ok", "module": "tentaculo_link", "version": "7.0" }curl http://127.0.0.1:8000/health# Simple health```bash### Health Checks## Endpoints Principales---```http://127.0.0.1:8000/openapi.json# OpenAPI JSONhttp://127.0.0.1:8000/redoc# ReDochttp://127.0.0.1:8000/docs# Swagger UI```bashTentáculo Link expone documentación automática:## OpenAPI Docs---```# }#   "total": 1#   ],#     }#       "message_count": 5#       "expires_at": "2025-12-14T11:30:00Z",#       "created_at": "2025-12-14T10:30:00Z",#       "session_id": "session-001",#     {#   "sessions": [# {# Respuesta:  http://127.0.0.1:8000/vx11/context-7/sessions | jq .curl -H "X-VX11-Token: vx11-local-token" \# Ver sesiones activas```bash### Monitorear Sesiones```        # Borra sesiones expiradas (tarea background)    def cleanup_expired(self):            # Retorna resumen de contexto para enviar al LLM    def get_hint_for_llm(self, session_id):            # Agrega mensaje a contexto de sesión    def add_message(self, session_id, role, content):            self.ttl_seconds = ttl_seconds        self.sessions = {}  # session_id → context    def __init__(self, ttl_seconds=3600):class Context7Manager:# Ver context7_middleware.py para detalles```python### ImplementaciónContext-7 es un middleware que mantiene estado de sesión en memoria con TTL auto-cleanup.### ¿Qué es?## Context-7 (TTL Sessions)---```)    timeout=25.0,    method="POST",    endpoint="/my_module/process",    module="my_module",ROUTE_TABLE[IntentType.MY_CUSTOM] = RouteConfig(# En routes.py (recomendado)```python### Agregar Nueva Ruta```print(all_routes.keys())  # dict_keys(['chat', 'code', 'audio', ...])all_routes = list_routes()# Listar todas las rutasprint(route.module, route.endpoint, route.timeout)  # switch, /switch/route-v5, 15.0route = get_route("chat")# Obtener ruta específicafrom tentaculo_link.routes import get_route, list_routes```python### Usoing Route Lookup```}    ...    IntentType.ANALYSIS: RouteConfig(module="madre", endpoint="/madre/task", ...),    IntentType.AUDIO:   RouteConfig(module="hermes", endpoint="/hermes/analyze-audio", ...),    IntentType.CODE:    RouteConfig(module="switch", endpoint="/switch/route-v5", ...),    IntentType.CHAT:    RouteConfig(module="switch", endpoint="/switch/route-v5", ...),ROUTE_TABLE = {# Ejemplos:```pythonEl archivo `routes.py` define mapeo estático `IntentType → RouteConfig`:### Mapeo de Intents## Route Table---```# }#   "timestamp": 1702616420.3#   },#     "switch": { "state": "half_open", "failure_count": 2, "last_failure": 1702616400.5 }#     "madre": { "state": "closed", "failure_count": 0, "last_failure": null },#   "breakers": {#   "status": "ok",# {# Respuesta:  http://127.0.0.1:8000/vx11/circuit-breaker/status | jq .curl -H "X-VX11-Token: vx11-local-token" \# Ver status de todos los circuit breakers```bash### Monitoreo| **HALF_OPEN** | Esperando recuperación | Intenta 1 request de prueba; si éxito → CLOSED; si fallo → OPEN || **OPEN** | Módulo no disponible | Rechaza requests, retorna `circuit_open` || **CLOSED** | Normal | Procesa requests ||--------|-------------|--------|| Estado | Descripción | Acción |### Estados```)    recovery_timeout=60.0,    # Intenta recuperación tras 60s    failure_threshold=3,      # Abre después de 3 fallosself.circuit_breaker = CircuitBreaker(# En clients.py: ModuleClient.__init__()```python### Configuración## Circuit Breaker---```CONTEXT7_TTL_SECONDS=3600OPERATOR_PORT=8011HERMES_PORT=8003SWITCH_PORT=8002MADRE_PORT=8001ENABLE_AUTH=falseVX11_TENTACULO_LINK_TOKEN=vx11-local-tokenTENTACULO_LINK_PORT=8000```bash### `.env` Mínimo (Desarrollo Local)```CONTEXT7_CLEANUP_INTERVAL=300  # limpieza cada 5 minCONTEXT7_TTL_SECONDS=3600  # sesiones expiran en 1 hora# Context-7 TTL# ... etcOPERATOR_URL="http://operator-backend:8011"HERMES_URL="http://hermes:8003"SWITCH_URL="http://switch:8002"MADRE_URL="http://madre:8001"# Módulos (URLs)ENABLE_AUTH=true  # false para dev localVX11_GATEWAY_TOKEN="vx11-local-token"  # fallbackVX11_TENTACULO_LINK_TOKEN="vx11-local-token"# AutenticaciónTENTACULO_LINK_PORT=8000# Puerto```bash### Env Variables## Configuración---```8. Si fallo: registra en circuit breaker, retorna error   ↓7. Si éxito: graba en contexto, retorna respuesta   ↓   - Si HALF_OPEN: intenta recovery   - Si OPEN: retorna circuit_open + fallback   - Si CLOSED: intenta request6. ModuleClient verifica circuit breaker (¿módulo disponible?)   ↓5. Obtiene ModuleClient para módulo target   ↓4. Tentáculo Link consulta route table (routes.py)   ↓3. Context-7 middleware: agrega sesión si es nueva   ↓2. Token validation (X-VX11-Token header)   ↓1. Request entra a Tentáculo Link (:8000)```### Flujo| **Context-7** | `context7_middleware.py` | Gestor de sesiones con TTL auto-cleanup || **Route table** | `routes.py` | Mapeo intento_type → endpoint + módulo || **Module clients** | `clients.py` | HTTP clients para cada módulo con circuit breaker || **Main app** | `main_v7.py` | FastAPI app, endpoints principales ||-----------|---------|---------|| Componente | Archivo | Función |### Componentes## Arquitectura---**Puerto:** 8000 | **Objetivo:** HTTP gateway con autenticación, router inteligente, circuit breaker y TTL Context-7.**Versión:** 7.0 | **Módulo:** `tentaculo_link`  Pure proxy + auth + context-7 middleware + modular clients
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set

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
from fastapi.responses import JSONResponse, StreamingResponse, Response
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
)
async def proxy_shub(
    request: Request,
    path: str,
    x_correlation_id: str = Header(None),
) -> StreamingResponse:
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
        limit_type = "protected" if is_protected else "default"
        allowed, limit_info = await limiter.check_limit(identifier, limit_type)

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


# ============ GENERIC API PROXY (forward all /operator/api/* to operator-backend) ============


@app.api_route("/operator/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def operator_api_proxy(path: str, request: Request):
    """
    Generic proxy for /operator/api/* endpoints.
    Forwards to operator-backend:8011/api/{path} with all method types.
    Respects headers, body, query params. Passes Authorization header if present.
    Auth is optional (backend handles auth_mode policy).
    """
    clients = get_clients()
    operator = clients.get_client("operator-backend")
    if not operator:
        raise HTTPException(status_code=503, detail="operator_backend_unavailable")

    # Build backend path
    backend_path = f"/api/{path}"
    if request.query_params:
        query_string = "&".join(f"{k}={v}" for k, v in request.query_params.items())
        backend_path = f"{backend_path}?{query_string}"

    # Extract Authorization header from request (optional, pass-through)
    auth_header = request.headers.get("authorization")
    extra_headers = {}
    if auth_header:
        extra_headers["authorization"] = auth_header

    try:
        method = request.method.lower()

        if method == "get":
            result = await operator.get(backend_path, extra_headers=extra_headers)
        elif method in ["post", "put"]:
            body = await request.json()
            result = await operator.post(
                backend_path, payload=body, extra_headers=extra_headers
            )
        elif method == "delete":
            result = await operator.post(
                f"{backend_path}", payload={}, extra_headers=extra_headers
            )
        else:
            raise HTTPException(status_code=405, detail="method_not_allowed")

        write_log("tentaculo_link", f"operator_api_proxy:{method}:{path}")
        return result
    except Exception as exc:
        write_log("tentaculo_link", f"operator_api_proxy_error:{exc}", level="WARNING")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
