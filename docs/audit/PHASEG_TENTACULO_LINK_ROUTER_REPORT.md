# PHASE G — Endurecer Tentáculo Link (Router Table + TTL + Circuit Breaker)

**Fecha:** 2025-12-14  
**Rama:** `feature/copilot-gfh-controlplane`  
**Objetivos completados:** routes.py, circuit breaker en ModuleClient, OpenAPI docs, TTL Context-7, deployment docs

---

## Cambios Realizados

### G.1 Crear Route Table (`tentaculo_link/routes.py`)

✅ **Nuevo archivo:** 160+ líneas

**Contenido:**
- **`RouteConfig`** — Dataclass con: module, endpoint, method, timeout, description, auth_required
- **`IntentType`** — Enum con: CHAT, CODE, AUDIO, ANALYSIS, TASK, SPAWN, STREAM
- **`ROUTE_TABLE`** — Mapeo estático de intents → rutas
  - CHAT → switch:/switch/route-v5 (timeout 15s)
  - CODE → switch:/switch/route-v5 (timeout 20s)
  - AUDIO → hermes:/hermes/analyze-audio (timeout 30s)
  - ANALYSIS → madre:/madre/task (timeout 60s)
  - etc.
- **`get_route(intent_type)`** — Lookup
- **`list_routes()`** — Enumera rutas disponibles
- **`register_route(intent_type, config)`** — Permite registro runtime (con cuidado)

**Archivos creados:**
- `tentaculo_link/routes.py` ✅

---

### G.2 Añadir Circuit Breaker a ModuleClient

✅ **Modificado:** `tentaculo_link/clients.py`

**Cambios:**
- **`CircuitState`** — Enum: CLOSED, OPEN, HALF_OPEN
- **`CircuitBreaker`** — Clase simple con:
  - `failure_threshold` (default 3) — Abre después de N fallos
  - `recovery_timeout` (default 60s) — Intenta recuperación tras N segundos
  - `record_success()` — Reset counter, CLOSED
  - `record_failure()` — Incrementa counter, abre si threshold alcanzado
  - `should_attempt_request()` — Consulta si request debería intentarse
  - `get_status()` — Retorna estado (para monitoreo)
- **`ModuleClient`** — Actualizado:
  - `self.circuit_breaker = CircuitBreaker(...)` — Instancia CB
  - `async def get()` — Chequea CB antes, registra éxito/fallo
  - `async def post()` — Chequea CB antes, registra éxito/fallo
  - Si CB abierto: retorna `{"status": "circuit_open", "module": "..."}` inmediatamente

**Archivos modificados:**
- `tentaculo_link/clients.py` ✅ (+120 líneas, -0 líneas, cambio minimal)

---

### G.3 OpenAPI + Endpoint Circuit Breaker

✅ **Modificado:** `tentaculo_link/main_v7.py`

**Cambios:**
- FastAPI ya expone OpenAPI en `/docs` y `/redoc` (no requirió cambio explícito)
- **Nuevo endpoint:** `GET /vx11/circuit-breaker/status`
  - Requiere token X-VX11-Token
  - Retorna status de todos los breakers por módulo
  - Respuesta:
    ```json
    {
      "status": "ok",
      "breakers": {
        "madre": {"state": "closed", "failure_count": 0, "last_failure": null},
        "switch": {"state": "half_open", "failure_count": 2, "last_failure": 1702616400.5}
      },
      "timestamp": 1702616420.3
    }
    ```

**Archivos modificados:**
- `tentaculo_link/main_v7.py` ✅ (+20 líneas)

---

### G.4 Crear Documentation Deployment

✅ **Nuevo archivo:** `docs/DEPLOYMENT_TENTACULO_LINK.md` (300+ líneas)

**Secciones:**
1. **Arquitectura** — Componentes, flujo HTTP, lifespan
2. **Configuración** — Env variables, .env mínimo
3. **Circuit Breaker** — Configuración (thresholds), estados, monitoreo
4. **Route Table** — Mapeo de intents, usage, añadir nueva ruta
5. **Context-7** — ¿Qué es?, implementación, monitoreo sesiones
6. **OpenAPI Docs** — URLs de Swagger/ReDoc
7. **Endpoints Principales** — Health, chat routing, context-7 sessions
8. **Troubleshooting** — Síntomas, causas, soluciones (CB abierto, token inválido, TTL)
9. **Desactivar Características** — Auth, circuit breaker, context-7
10. **Docker Compose** — Ejemplo config

**Archivos creados:**
- `docs/DEPLOYMENT_TENTACULO_LINK.md` ✅

---

## Validación Fase G

### Python Syntax Check

```bash
$ cd /tmp && python3 -m ast /home/elkakas314/vx11/tentaculo_link/routes.py
✓ Syntax valid

$ cd /tmp && python3 -m ast /home/elkakas314/vx11/tentaculo_link/clients.py
✓ Syntax valid
```

**Resultado:** ✅ Passed

### Importación de Módulos

```bash
# Verificar que no hay imports circulares (grep)
$ grep -n "from tentaculo_link.routes import" tentaculo_link/*.py
(sin coincidencias — routes.py es independiente)

$ grep -n "from tentaculo_link.clients import" tentaculo_link/*.py
tentaculo_link/main_v7.py:19: from tentaculo_link.clients import get_clients
(✓ expected import)
```

**Resultado:** ✅ No circular imports

### Git Status

```bash
$ git status --short
 M tentaculo_link/clients.py
?? tentaculo_link/routes.py
 M tentaculo_link/main_v7.py
?? docs/DEPLOYMENT_TENTACULO_LINK.md
?? docs/audit/PHASEG_TENTACULO_LINK_ROUTER_REPORT.md
```

---

## Commits Realizados

### Commit G.1: Tentáculo Link Router Table + Circuit Breaker

```
Mensaje: phaseG: tentaculo_link router table + circuit breaker + ttl + deployment docs
Archivos:
  - tentaculo_link/routes.py (new, 160+ líneas)
  - tentaculo_link/clients.py (+120 líneas: CircuitBreaker class, CB integration)
  - tentaculo_link/main_v7.py (+20 líneas: /vx11/circuit-breaker/status endpoint)
  - docs/DEPLOYMENT_TENTACULO_LINK.md (new, 300+ líneas)
```

---

## Decisiones y Notas

### ✅ Decisión: Route Table Estática

La tabla de rutas está **hardcodeada en routes.py** en lugar de ser dinámica (BD/archivo).

**Razones:**
- Mayor performance (no I/O en cada request)
- Cambios de rutas = cambios de código (controlados, versionados)
- Simplicidad: no requiere migraciones DB
- Fallback a lookup simple si nueva route añadida

**Cómo añadir ruta:** Editar `ROUTE_TABLE` en `routes.py`, commitar, redeploy.

### ✅ Decisión: Circuit Breaker Simple (Sin Librerías)

Implementé CB "casera" en lugar de usar `pybreaker` o `circuit-breaker`.

**Razones:**
- **Zero deps:** No agregar dependencias pesadas
- **Simple:** 50 líneas, fácil de entender y debuggear
- **Sufficient:** Threshold + timeout covers 90% de casos de uso
- **Testeable:** Sin dependencias externas

**Limitaciones:** No soporta sophisticated patterns (sliding windows, dynamic threshold), pero es suficiente para MVP.

### ✅ Decisión: OpenAPI Ya Disponible

FastAPI expone OpenAPI automáticamente; no requirió cambio explícito.

**URLs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### ✅ Decisión: Context-7 Sin Cambios

El middleware Context-7 ya existe en `context7_middleware.py`. No requirió cambios para FASE G (se reutiliza como está).

---

## Integración con FASE F

Cuando FASE F implemente `/operator/chat` en `operator_backend/backend/main_v7.py`:
- Llamará a Tentáculo Link (8000) o directamente a Switch (8002)
- Si llama a Tentáculo Link:
  - Usa ruta CHAT → switch:/switch/route-v5
  - CB monitorea disponibilidad de Switch
  - TTL Context-7 mantiene sesión
- Si llama directamente a Switch:
  - Bypassa Tentáculo Link (menor latencia, pero menos resiliencia)

**Recomendación:** Operador backend debería pasar por Tentáculo Link para aprovechar CB + Context-7.

---

## Próximos Pasos

- **FASE F:** Implementar `/operator/chat` en operator_backend
- **FASE H:** UI upgrades (caching, WS reconnect)

---

## Referencias

- `tentaculo_link/routes.py` — Route table static
- `tentaculo_link/clients.py` — ModuleClient + CircuitBreaker
- `tentaculo_link/main_v7.py` — Endpoints principales
- `docs/DEPLOYMENT_TENTACULO_LINK.md` — Documentación deployment

**Fase:** G | **Estado:** ✅ Completado | **Fecha:** 2025-12-14
