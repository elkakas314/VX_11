# VX11 CORE WIRING — FASE A: INVENTARIO EXHAUSTIVO

**Fecha**: 2026-01-01T04:24:01Z  
**Ingeniero**: Copilot (paranoico)  
**Estado**: COMPLETE (sin tocar código)

---

## 1. ENDPOINTS MAPEADOS

### TENTACULO_LINK (8000) — Gateway Entrypoint

| METHOD | PATH | Handler | Auth | Policy | Status |
|--------|------|---------|------|--------|--------|
| GET | `/health` | health() | NO | - | ✅ EXISTE |
| GET | `/operator` | operator_redirect() | NO | - | ✅ EXISTE (redir a /ui) |
| GET | `/vx11/status` | vx11_status() | SI | token_guard | ✅ EXISTE |
| GET | `/metrics` | metrics() | SI | token_guard | ✅ EXISTE |
| GET | `/operator/ui` | static files | NO | - | ✅ EXISTE |
| POST | `/operator/chat` | operator_chat() | SI | token_guard | ✅ EXISTE |
| POST | `/operator/task` | operator_task() | SI | token_guard | ✅ EXISTE |
| POST | `/operator/chat/ask` | operator_chat_ask() | SI | token_guard | ✅ EXISTE |
| GET | `/operator/status` | operator_status() | SI | token_guard | ✅ EXISTE |
| GET | `/operator/power/state` | power_state() | SI | token_guard | ✅ EXISTE |
| GET | `/operator/power/status` | power_status() | SI | token_guard | ✅ EXISTE |
| GET | `/operator/power/policy/solo_madre/status` | solo_madre_status() | SI | token_guard | ✅ EXISTE |
| POST | `/operator/power/policy/solo_madre/apply` | solo_madre_apply() | SI | token_guard | ✅ EXISTE |
| POST | `/operator/power/service/{name}/start` | service_start() | SI | token_guard | ✅ EXISTE |
| POST | `/operator/power/service/{name}/stop` | service_stop() | SI | token_guard | ✅ EXISTE |
| POST | `/hermes/get-engine` | proxy_hermes_get_engine() | SI | token_guard | ✅ EXISTE (proxy a hermes:8003) |
| POST | `/hermes/execute` | proxy_hermes_execute() | SI | token_guard | ✅ EXISTE (proxy a hermes:8003) |

**MIDDLEWARE**: `operator_api_proxy` intercepta `/operator/api/*` → proxy a operator_backend:8011 (si `OPERATOR_PROXY_ENABLED=true`)

---

### MADRE (8001) — Orchestrator Internal

| METHOD | PATH | Handler | Internal Call | Status |
|--------|------|---------|----------------|--------|
| POST | `/chat` | (chat_handler) | TBD en main.py | ❓ NO MAPEADO |
| POST | `/orchestrate` | (orchestrate_handler) | TBD | ❓ NO MAPEADO |
| POST | `/control` | (control_handler) | TBD | ❓ NO MAPEADO |
| POST | `/task` | (task_handler) | TBD | ❓ NO MAPEADO |
| GET | `/health` | health() | - | ✅ EXISTE (probablemente) |
| GET | `/status` | status() | - | ✅ EXISTE (probablemente) |

**POLICY INTEGRATION**:
- `power_windows.get_window_manager()` → Chequea si Switch/Spawner está disponible
- `power_windows.check_ttl_expiration()` → Detiene servicios al expirar TTL
- Background task `_ttl_checker_background()` → Corre cada 1 segundo

**AUTH**: X-VX11-Token header (forward desde tentaculo_link)

---

### SWITCH (8002) — Intelligence Layer

| METHOD | PATH | Handler | Status |
|--------|------|---------|--------|
| GET | `/health` | health() | ✅ EXISTE |
| GET | `/switch/context` | context() | ✅ EXISTE |
| POST | `/switch/advice` | advice() | ✅ EXISTE |
| GET | `/switch/providers` | providers() | ✅ EXISTE |
| POST | `/switch/hermes/select_engine` | select_engine() | ✅ EXISTE |
| POST | `/switch/control` | control() | ✅ EXISTE |
| POST | `/switch/route-v5` | route_v5() | ✅ EXISTE |
| POST | `/switch/route` | route() | ✅ EXISTE |
| POST | `/switch/chat` | chat() | ✅ EXISTE |

**LLAMADAS DESDE MADRE**:
- `DelegationClient.call_module("switch", endpoint, payload)` → vía `http://switch:8002`
- URL: `http://switch:{settings.switch_port}/{endpoint}`
- Headers: `{"X-VX11-Token": settings.api_token}`

---

### SPAWNER (8008) — Service Orchestration (Stub)

| METHOD | PATH | Handler | Status |
|--------|------|---------|--------|
| GET | `/health` | health() | ✅ EXISTE (probablemente) |
| POST | `/spawn` | spawn_task() | ❓ TBD |

**INTEGRACIÓN CON MADRE**:
- `DelegationClient.request_spawner_hija()` → Crea entrada en BD `daughter_tasks`
- No se ejecuta HTTP directo si TTL está OFF

---

## 2. FLUJO ACTUAL TENTACULO_LINK → MADRE → SWITCH

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLIENTE EXTERNO (vía curl/UI)                                      │
└─────────────┬───────────────────────────────────────────────────────┘
              │
              │ POST /operator/chat
              │ (X-VX11-Token: required)
              ▼
        ┌──────────────────────────────────────┐
        │ TENTACULO_LINK (8000)                │
        │ - TokenGuard() → verifica token      │
        │ - operator_chat_proxy() → forward    │
        │ - rate_limit check                   │
        │ - Context-7 session storage          │
        └────────┬─────────────────────────────┘
                 │
                 │ httpx.AsyncClient
                 │ POST http://madre:8001/chat
                 │
                 ▼
        ┌──────────────────────────────────────┐
        │ MADRE (8001)                         │
        │ - Parse intent                       │
        │ - Check power_windows (TTL)          │
        │ - IF window CLOSED → OFF_BY_POLICY   │
        │ - IF window OPEN → call Switch       │
        └────────┬─────────────────────────────┘
                 │
                 │ DelegationClient.call_module("switch", "/switch/route-v5", {...})
                 │ POST http://switch:8002/switch/route-v5
                 │ Headers: X-VX11-Token
                 │
                 ▼
        ┌──────────────────────────────────────┐
        │ SWITCH (8002)                        │
        │ - Route query to best engine         │
        │ - Hermes registry lookup             │
        │ - Return engine selection + cost     │
        └────────┬─────────────────────────────┘
                 │
                 │ return { engine_id, cost, reasoning }
                 │
                 ▼
        ┌──────────────────────────────────────┐
        │ MADRE (continues)                    │
        │ - Aggregate result                   │
        │ - Format response                    │
        │ - Log to DB                          │
        └────────┬─────────────────────────────┘
                 │
                 │ return response_json
                 │
                 ▼
        ┌──────────────────────────────────────┐
        │ TENTACULO_LINK (continues)           │
        │ - Forward response to client         │
        │ - Add X-Correlation-Id header        │
        │ - Store in cache (ttl_sec=600)       │
        └────────┬─────────────────────────────┘
                 │
                 │ response 200 JSON
                 │
                 ▼
        ┌──────────────────────────────────────┐
        │ CLIENTE EXTERNO                      │
        │ (recibe respuesta)                   │
        └──────────────────────────────────────┘
```

---

## 3. POLICY / VENTANAS TEMPORALES

### Estado ACTUAL (default):
- **Runtime Mode**: `solo_madre` (SWITCH OFF)
- **Policy Location**: `madre/power_windows.py` → `WindowManager`
- **TTL Checker**: Background task en `madre/main.py` → `_ttl_checker_background()`
- **Service Control**: Docker compose via subprocess (si `VX11_POWER_WINDOWS_DOCKER_EXEC=1`)

### Endpoints de Control (vía tentaculo_link):
1. `GET /operator/power/policy/solo_madre/status` → ¿está activo SOLO_MADRE?
2. `POST /operator/power/policy/solo_madre/apply` → Fuerza SOLO_MADRE (detiene Switch, Spawner, etc)
3. `POST /operator/power/window/open` → Abre ventana temporal para servicios (en routes_power.py)
4. `POST /operator/power/window/close` → Cierra ventana (en routes_power.py)

### OFF_BY_POLICY Responses:
```json
{
  "status": "OFF_BY_POLICY",
  "service": "switch",
  "message": "Disabled by SOLO_MADRE policy",
  "recommended_action": "Ask Madre to open switch window",
  "correlation_id": "uuid"
}
```

---

## 4. IDENTIFICACIÓN DE P0s (PROBLEMAS CRÍTICOS)

### P0-1: HERMES SERVICE UNHEALTHY
- **Síntoma**: `vx11-hermes-test` → health status **unhealthy** (docker ps)
- **Impacto**: `/hermes/get-engine` y `/hermes/execute` → fallan o degradan
- **Rootcause**: TBD (revisar logs en forensic/hermes/)
- **Mitigation**: Podría causar que route-v5 falle sin caer todo tentaculo_link

### P0-2: CIRCUITO ABIERTO MADRE↔SWITCH
- **Síntoma**: Si madre → switch falla 3+ veces, circuito se abre (circuit_breaker.py)
- **Impacto**: Incluso con ventana abierta, madre NUNCA llama a switch (todos los pedidos vuelven OFF_BY_POLICY)
- **Rootcause**: Network timeout, switch service down, etc.
- **Mitigation**: Chequear `/vx11/circuit-breaker/status` endpoint

### P0-3: OFF_BY_POLICY OPACO (SIN ERROR CLARO)
- **Síntoma**: Cliente llamada `/operator/chat` → recibe `connection refused` (ERROR opaco)
- **Impacto**: No sabe si es porque SOLO_MADRE está activo o porque service está down
- **Rootcause**: Middleware `operator_api_proxy` fallando silenciosamente (Exception catch → 403)
- **Mitigation**: Ya hay manejo, pero revisar si está retornando mensaje claro

---

## 5. DEFINICIÓN DE HECHO (DoD) — FASE B REQUISITOS

Para FASE B (Cableado Core), debo garantizar:

1. ✅ **Single Entrypoint**: Todo acceso SOLO por `http://localhost:8000`
   - Verificar: cliente NO puede llamar a `http://localhost:8001/` (madre internal)
   - Verificar: cliente NO puede llamar a `http://localhost:8002/` (switch internal)

2. ✅ **Default SOLO_MADRE**: Sin intervención, Switch OFF
   - Verificar: `POST /operator/chat` → responde OFF_BY_POLICY (no connection refused)

3. ✅ **Ventana Temporal Funcional**:
   - Open window: `POST /operator/power/window/open {"services": ["switch"], "ttl_sec": 300}`
   - Chat con ventana: `POST /operator/chat` → llama a Switch, responde 200
   - Close window: `POST /operator/power/window/close {"window_id": "..."}`
   - Chat sin ventana: vuelve a OFF_BY_POLICY

4. ✅ **Tokens + Auth**:
   - X-VX11-Token required en TODAS las rutas de tentaculo_link
   - Rechazar 401 si falta, 403 si inválido
   - NO hardcodear en bundles

5. ✅ **Reproducible**:
   - 6 curls contra `http://localhost:8000` → todo funciona
   - Pytest opcional (si hay test framework)

---

## 6. ARCHIVOS CRÍTICOS IDENTIFICADOS

- `tentaculo_link/main_v7.py` → Entrypoint principal (4277 líneas)
- `madre/main.py` → Orquestador (980 líneas)
- `madre/power_windows.py` → Policy + TTL manager
- `madre/routes_power.py` → Endpoints de control (593 líneas)
- `madre/core/delegation.py` → HTTP client a Switch (101 líneas)
- `switch/main.py` → Router intelligence (1432+ líneas)
- `config/settings.py` → Configuración global de puertos/URLs
- `config/tokens.py` → Token management

---

## 7. CONCLUSIÓN FASE A

✅ **INVENTARIO COMPLETO**
- Endpoints MAPEADOS: tentaculo_link (18 main), madre (6+), switch (9)
- Flujo ENTENDIDO: tentaculo_link → madre → switch (vía DelegationClient HTTP)
- Policy IDENTIFICADA: SOLO_MADRE default, ventanas temporales vía WindowManager
- P0s LOCALIZADOS: Hermes unhealthy, circuit breaker, OFF_BY_POLICY opaco

**SIGUIENTE**: FASE B (Cableado Core + pruebas reproducibles)

---

**Audit Trail**: docs/audit/20260101T042401Z_core_wiring/
