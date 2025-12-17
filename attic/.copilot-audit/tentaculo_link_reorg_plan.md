# Tentáculo Link v7.0 → v7.1 Reorganization Plan

## Objetivo
Centralizar routing logic, unificar prefijos de endpoint, mejorar observabilidad y seguridad sin breaking changes en frontend.

## Cambios Minimalistas (No Breaking)

### 1. Unificar Prefijo de Rutas (Opcional, Backward-Compatible)
**Actualmente:**
- `/vx11/status` (modules)
- `/operator/chat` (legacy)
- `/shub/dashboard` (inconsistent)
- `/resources` (orphan)

**Propuesto:**
- Mantener `/vx11/*` como canonical (módulo interno)
- Mantener `/operator/*` para retrocompatibilidad (legacy alias)
- Nuevo: `/api/v1/*` como forward-compatible (opcional futuro)

**Acción:** Solo añadir, no eliminar. Router puede servir ambos prefijos.

### 2. Router Table Centralizado (tentaculo_link/routes.py)
Consolidar mapping `intent_type → endpoint` en archivo separado:

```python
# tentaculo_link/routes.py
ROUTE_MAP = {
    "vx11:dsl": {"endpoint": "/madre/dsl", "module": "madre"},
    "vx11:intent": {"endpoint": "/madre/intent", "module": "madre"},
    "vx11:chat": {"endpoint": "/madre/chat", "module": "madre"},
    "shub:analyze": {"endpoint": "/shub/analyze", "module": "shub"},
    "resources:list": {"endpoint": "/hermes/resources", "module": "hermes"},
}
```

**Beneficio:** Cambios de routing se hacen en un lugar, no scattered por main_v7.py.

### 3. Circuit Breaker en ModuleClient (tentaculo_link/clients.py)
Detectar fallos de módulos y retornar fallback automático:

```python
class ModuleClient:
    async def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # ... existing
        except (ConnectionError, Timeout) as exc:
            if self.failure_count >= 3:
                write_log("tentaculo_link", f"circuit_open:{self.module_name}", level="ERROR")
                return {"status": "unavailable", "module": self.module_name, "error": "circuit_open"}
            self.failure_count += 1
            # retry or fallback
```

**Beneficio:** Evita cascada de fallos si madre/switch se cuelga.

### 4. Rate Limiter → Redis (Opcional, Backward-Compatible)
Migrar de memoria a Redis si hay múltiples instancias:

```python
# tentaculo_link/rate_limiter.py
class RedisRateLimiter:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
    
    async def allow(self, key: str) -> bool:
        count = await self.redis.incr(f"ratelimit:{key}")
        if count == 1:
            await self.redis.expire(f"ratelimit:{key}", 60)
        return count <= 60
```

**Nota:** Requiere Docker Redis. Marcar como "future work" si no se implementa ahora.

### 5. Session TTL para CONTEXT-7 (tentaculo_link/context7_middleware.py)
Evitar memory leak de sesiones antiguas:

```python
def is_session_expired(self, session_id: str, ttl_hours: int = 24) -> bool:
    session = self.get_session(session_id)
    if not session:
        return True
    age = (datetime.utcnow() - session.created_at).total_seconds() / 3600
    return age > ttl_hours
```

**Beneficio:** Limpiar sesiones viejas automáticamente.

### 6. OpenAPI/Swagger Docs (main_v7.py)
Generar documentación automática:

```python
app = FastAPI(
    title="VX11 Tentáculo Link",
    version="7.1",
    description="Central gateway for VX11 microservices",
    docs_url="/docs",  # Swagger UI
    openapi_url="/openapi.json",
)
```

**Beneficio:** Frontend puede descubrir endpoints dinámicamente. `/docs` disponible en http://localhost:8000/docs.

### 7. Prometheus Metrics (tentaculo_link/metrics.py)
Instrumentar para observabilidad:

```python
from prometheus_client import Counter, Histogram

request_count = Counter(
    "tentaculo_link_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)
request_latency = Histogram(
    "tentaculo_link_request_duration_seconds",
    "Request latency",
    ["endpoint"],
)

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    latency = time.time() - start
    request_latency.labels(endpoint=request.url.path).observe(latency)
    request_count.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    return response
```

**Beneficio:** Métricas disponibles en `/metrics` para Prometheus scraping.

## Implementation Order (Phases)

### Phase 1: Router Table + Docs (1-2 commits)
- [ ] Create `tentaculo_link/routes.py` with ROUTE_MAP
- [ ] Enable OpenAPI docs in FastAPI
- [ ] Update README with `/docs` link

### Phase 2: Circuit Breaker (1 commit)
- [ ] Add failure counter to ModuleClient
- [ ] Implement exponential backoff
- [ ] Test with manual module restart

### Phase 3: Session TTL (1 commit)
- [ ] Add timestamp + expiry logic to Context7Session
- [ ] Cleanup job (optional: async task every 1h)

### Phase 4: Prometheus (1 commit, optional)
- [ ] Add prometheus_client to requirements_tentaculo.txt
- [ ] Instrument HTTP middleware
- [ ] Expose `/metrics` endpoint

### Phase 5: Redis RateLimiter (optional, future)
- [ ] Add Redis service to docker-compose.yml
- [ ] Replace RateLimiter with RedisRateLimiter
- [ ] Configure REDIS_URL in settings

## Files to Modify

| File | Change | Type |
|------|--------|------|
| `tentaculo_link/main_v7.py` | Enable OpenAPI docs | Minor |
| `tentaculo_link/routes.py` | **New** - Router table | New |
| `tentaculo_link/clients.py` | Add circuit breaker logic | Minor |
| `tentaculo_link/context7_middleware.py` | Add session TTL | Minor |
| `tentaculo_link/metrics.py` | **New** - Prometheus instrumentation | New (optional) |
| `requirements_tentaculo.txt` | Add prometheus_client (optional) | Minor |
| `.github/workflows/ci.yml` | Scrape /metrics (optional) | New (optional) |

## Frontend Impact
✅ **ZERO** — All changes are internal to tentaculo_link. Routes remain backward-compatible.

## Testing Checklist
- [ ] `pytest tests/test_tentaculo_link.py` passes
- [ ] `/docs` Swagger UI loads
- [ ] `/metrics` returns valid Prometheus format
- [ ] Circuit breaker triggers when module offline
- [ ] Rate limit works (60 req/min per IP)
- [ ] Old sessions expire after 24h
- [ ] Frontend still connects via OPERATOR_BASE_URL:8011 (unaffected)

## Backward Compatibility
✅ All existing endpoints remain functional. New features are opt-in.

## Next: Operator UI Refactoring
Once tentaculo_link is stabilized, proceed with:
1. React Query hooks for chat streaming
2. Monaco editor with lint markers
3. Shub panel finalization
4. Health gating for dashboard

See `.copilot-audit/plan_operator_upgrade.md` for UI phases.
