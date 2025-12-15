# VX11 API Discovery — Endpoints Reales (v7.1)

**Generado:** 2025-12-15  
**Fuente:** `curl /openapi.json` desde servicios 7/10 OK  
**Propósito:** Template de intents para agent VX11

---

## TentáculoLink (8000) — Gateway Principal

**Rol**: HTTP gateway + router table + entrypoint único

### Endpoints Clave

| Endpoint | Método | Propósito | Ejemplo de Intent |
|----------|--------|----------|-------------------|
| `/vx11/status` | GET | Estado global del sistema | `@vx11 status` |
| `/vx11/intent` | POST | Inyectar intent directo | `@vx11 task:enqueue "desc"` |
| `/vx11/overview` | GET | Resumen visual | `@vx11 audit structure` |
| `/operator/chat` | POST | Chat persistido con sesión | `@vx11 chat: msg` |
| `/vx11/dsl` | POST | Ejecutar DSL directo | Internal |
| `/health` | GET | Health check | Monitoring |

### Curl Template (Inyectar Intent)

```bash
curl -X POST http://localhost:8000/vx11/intent \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "copilot-agent",
    "intent_type": "task",
    "description": "Reparar módulo hermes",
    "priority": 5
  }'
```

---

## Madre (8001) — Orquestador Autónomo

**Rol**: Tareas, P&P (off/standby/active), decisiones autónomas

### Endpoints Clave

| Endpoint | Método | Propósito | Intent |
|----------|--------|----------|--------|
| `/madre/hijas` | GET | Listar hijas activas | `@vx11 watch hijas` |
| `/madre/daughter/spawn` | POST | Spawn hija ejecutora | `@vx11 task:enqueue` |
| `/madre/daughters` | GET | Estado hijas | Monitoring |
| `/madre/dsl` | POST | Ejecutar DSL de Madre | Internal |
| `/health` | GET | Health check | Monitoring |

### Curl Template (Spawn Hija)

```bash
curl -X POST http://localhost:8001/madre/daughter/spawn \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "purpose": "diagnosticar y reparar hermes",
    "tools": ["hermes_diagnose", "manifestator_patch"],
    "ttl_seconds": 300
  }'
```

---

## Switch (8002) — Router IA Adaptativo

**Rol**: Seleccionar modelo/CLI, scoring, learning

### Endpoints Clave

| Endpoint | Método | Propósito | Intent |
|----------|--------|----------|--------|
| `/switch/route-v5` | POST | Enrutar prompt con scoring | `@vx11 task:enqueue` |
| `/switch/chat` | POST | Chat + selección modelo | Chat |
| `/switch/models/available` | GET | Modelos disponibles | `@vx11 audit` |
| `/switch/hermes/select_engine` | POST | Seleccionar engine | Internal |
| `/health` | GET | Health | Monitoring |

### Curl Template (Enrutar Intent)

```bash
curl -X POST http://localhost:8002/switch/route-v5 \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "diagnosticar hermes",
    "task_type": "diagnosis",
    "metadata": {"module": "hermes"}
  }'
```

---

## Manifestator (8005) — Auditoría + Parches

**Rol**: Detectar drift, generar patches, aplicar

### Endpoints Clave

| Endpoint | Método | Propósito | Intent |
|----------|--------|----------|--------|
| `/manifestator/scan-drift` | POST | Scan drift vs canon | `@vx11 audit structure` |
| `/manifestator/dsl/plan` | POST | Generar plan de parcheo | `@vx11 fix service:X` |
| `/manifestator/dsl/apply/{plan_id}` | POST | Aplicar patch | Internal |
| `/health` | GET | Health | Monitoring |

### Curl Template (Scan Drift)

```bash
curl -X POST http://localhost:8005/manifestator/scan-drift \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "modules": ["tentaculo_link", "madre", "switch"],
    "depth": "full"
  }'
```

---

## MCP (8006) — Conversacional

**Rol**: Ejecutar comandos, sandbox safe

### Endpoints Clave

| Endpoint | Método | Propósito | Intent |
|----------|--------|----------|--------|
| `/mcp/copilot-bridge` | POST | Bridge Copilot → VX11 | Internal |
| `/mcp/sandbox/exec_cmd` | POST | Ejecutar cmd safe | Internal |
| `/health` | GET | Health | Monitoring |

---

## Spawner (8008) — Hijas Efímeras

**Rol**: Spawn, track, kill procesos hijas

### Endpoints Clave

| Endpoint | Método | Propósito | Intent |
|----------|--------|----------|--------|
| `/spawner/spawn` | POST | Spawn proceso efímero | `@vx11 task:enqueue` |
| `/spawn/status/{spawn_id}` | GET | Status hija | `@vx11 watch <id>` |
| `/spawn/output/{spawn_id}` | GET | Obtener output | Internal |
| `/spawn/kill/{spawn_id}` | POST | Matar hija | Internal |
| `/health` | GET | Health | Monitoring |

### Curl Template (Spawn Hija Efímera)

```bash
curl -X POST http://localhost:8008/spawner/spawn \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "diagnostico-hermes",
    "cmd": "python3 scripts/diagnose_module.py hermes",
    "ttl_seconds": 120
  }'
```

---

## Operator Backend (8011) — Chat Persistido

**Rol**: `/operator/chat` con sesión + BD, browser tasks, recursos

### Endpoints Clave

| Endpoint | Método | Propósito | Intent |
|----------|--------|----------|--------|
| `/operator/chat` | POST | Chat con persistencia | `@vx11 chat: msg` |
| `/operator/session/{session_id}` | GET | Recuperar sesión | Internal |
| `/operator/browser/task` | POST | Navegar + capturar | Internal |
| `/operator/resources` | GET | Recursos disponibles | `@vx11 status` |
| `/health` | GET | Health | Monitoring |

### Curl Template (Chat Persistido)

```bash
curl -X POST http://localhost:8011/operator/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "vx11-agent-session",
    "user_id": "copilot",
    "message": "¿Cuál es el estado de hermes?",
    "context_summary": "Diagnosticando módulos"
  }'
```

---

## Intent Routing Examples

### Intent: Diagnosticar Módulo BROKEN

```
Usuario: @vx11 fix service:hermes

Agent Action:
1. TentáculoLink (8000) /vx11/intent → describe intent
2. Madre (8001) /madre/daughter/spawn → spawn hija diagnosticadora
3. Spawner (8008) /spawner/spawn → ejecutar diagnóstico
4. Manifestator (8005) /manifestator/dsl/plan → generar patch
5. Manifestator /manifestator/dsl/apply → aplicar fix
6. Report → Operator Backend (8011) /operator/chat → persistir resultado
```

### Intent: Chat + Seguimiento

```
Usuario: @vx11 chat: ¿Qué módulos están roto?

Agent Action:
1. TentáculoLink (8000) /vx11/status → obtener estado actual
2. Operator Backend (8011) /operator/chat → sesión persistida
3. Switch (8002) /switch/chat → enrutar respuesta
4. Report → Tabla servicios OK/BROKEN
```

---

## Notas de Implementación

- **Header requerido**: `X-VX11-Token: vx11-local-token`
- **Content-Type**: `application/json` (POST)
- **Timeout**: 15-30s por request
- **Fallback**: Si servicio cae, agent intenta siguiente en router
- **Logging**: Todos los intents registrados en `/data/runtime/vx11.db` tabla `copilot_actions_log`

---

**Generado por FASE 3: VX11 Agent Bootstrap**
