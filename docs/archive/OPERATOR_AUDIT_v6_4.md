# AUDITORÍA VISUAL Y LÓGICA: OPERATOR VX11 v6.4

**Fecha**: 4 de diciembre de 2025  
**Estado**: Auditoría Completa (sin modificaciones)  
**Objetivo**: Validar estructura, wiring, componentes visuales y endpoints de Operator backend + frontend conforme a arquitectura v6.4 de VX11.

---

## 📊 RESUMEN EJECUTIVO

### Estado Actual
- ✅ **Backend**: FastAPI funcional con bridge a Tentáculo Link
- ✅ **Frontend**: React/Vite con 4 componentes básicos
- ⚠️ **Wiring**: Parcialmente alineado con v6.4; faltan representaciones visuales clave
- ❌ **Visualización**: Deficiente; no muestra planes, hijas, cola prioritaria, auditoría MCP, etc.
- ❌ **UX**: Minimalista; falta logging en vivo, collapsibles, visualizadores de flujos

### Hallazgos Críticos
1. **Falta de representación de planes Madre** → No hay panel para visualizar planes, feedback, delegaciones
2. **Sin panel de hijas activas/muertas** → Spawner crea procesos, pero Operator no los muestra
3. **Cola prioritaria de Switch oculta** → Switch mantiene `task_queue` persistente; Operator no accede
4. **Hermes modelo registry invisible** → Modelos locales/registrados no aparecen en UI
5. **MCP auditoría no mapeada** → Sandbox ejecutable pero sin visualización de logs/auditoría
6. **Hormiguero/Reina no representados** → Tareas clasificadas por Reina no aparecen
7. **WebSocket una dirección** → Solo recibe eventos; no hay canales específicos por tipo

### Puntuación Visual
- **Cobertura de módulos**: 40% (solo health básico)
- **Fidelidad arquitectónica**: 35% (visualiza status, ignora planes/procesos/colas)
- **UX operacional**: 25% (no hay logs streaming, sin collapsibles, sin minimapa)

---

## 🏗️ ESTRUCTURA ACTUAL

### Backend (`/operator/backend/`)

```
operator/
├── main.py                           # FastAPI app, 316 líneas
├── Dockerfile
├── services/
│   ├── __init__.py
│   ├── clients.py                    # ShubClient, ManifestatorClient, SwitchClient, HermesClient
│   ├── operator_brain.py             # Lightweight intent handler (detecta chat|task|audio)
│   ├── model_rotator.py              # Selector simple ["auto", "balanced", "eco"]
│   ├── intent_parser.py              # AudioIntentParser (minimal)
│   ├── job_queue.py                  # In-memory JobQueue (no persistencia en BD)
│   └── health_aggregator.py          # HealthAggregator (12 módulos vía HTTP /health)
```

### Frontend (`/operator/frontend/`)

```
frontend/
├── src/
│   ├── App.tsx                       # Render principal, 3 panels
│   ├── main.tsx
│   ├── services/
│   │   └── api.ts                    # fetchSystemStatus, validateManifest, wsConnect
│   ├── components/
│   │   ├── Dashboard.tsx             # Grid de módulos + evento reciente
│   │   ├── ChatPanel.tsx             # Chat simple (Switch)
│   │   ├── ShubPanel.tsx             # Placeholder "Shub sessions coming soon"
│   │   └── StatusBar.tsx             # Estado conexión + contador health
│   └── styles.css
├── Dockerfile, vite.config.ts, tsconfig.json
└── package.json
```

### Legacy (`/operator/disabled/`)
- Versión anterior conservada para compatibilidad
- Endpoints similares, con `queue_size` en respuestas

---

## 🔌 WIRING ACTUAL vs ARQUITECTURA v6.4

### ✅ Conexiones Correctas

| Componente | Endpoint | Destino | Estado |
|-----------|----------|---------|--------|
| Operator→Tentáculo | WebSocket `/ws` | Tentáculo Link | ✅ Bridge bidireccional |
| Operator→Switch | `/intent/chat` → SwitchClient | Switch `:8002` | ✅ Usa `/switch/route-v5` |
| Operator→Hermes | `HermesClient` | Hermes `:8003` | ✅ Endpoint `/hermes/waveform` |
| Operator→Shub | `ShubClient` | Shub `:8007` | ✅ Endpoint `/shub/run_mode_c` |
| Operator→Manifestator | `ManifestatorClient` | Manifestator `:8005` | ✅ `/api/manifest/validate` |
| Health Aggregate | HealthAggregator loop | 12 módulos | ✅ Colecta `/health` cada módulo |

### ⚠️ Wiring Parcial

| Componente | Requerido v6.4 | Actual | Brecha |
|-----------|----------------|--------|---------|
| Operator→Madre | `/orchestrate` (planes + feedback) | ❌ No implementado | Falta integración |
| Operator→Spawner | `/spawn/list`, `/spawn/status/{id}` | ❌ No hay cliente | Falta panel hijas |
| Operator→Hormiguero | `/hormiguero/task`, `/hormiguero/tasks` | ❌ No hay cliente | Falta vista tareas |
| Operator→MCP | `/mcp/execute`, `/mcp/sandbox/check` | ❌ No hay cliente | Falta auditoría |
| Tentáculo→Operator | Eventos broadcast | ✅ Recibe | ⚠️ Sin canales específicos |

### ❌ Endpoints Faltantes en Operator Backend

Según v6.4, Operator **debería exponer**:
```
GET /plans                        # Planes creados por Madre
GET /plans/{plan_id}              # Detalle de plan + feedback
GET /spawns                       # Hijas activas/muertas
GET /spawns/{spawn_id}            # Detalle de hija
GET /switch/queue                 # Cola prioritaria (tarea siguiente)
GET /switch/queue/status          # Tamaño cola, modelo activo
GET /hermes/models                # Modelos disponibles (local + registro)
GET /mcp/audit                    # Logs de sandbox
GET /hormiguero/tasks             # Tareas clasificadas por Reina
GET /hormiguero/tasks/pending     # Solo pendientes
POST /execute-plan/{plan_id}      # Gatillar ejecución de plan
POST /kill-spawn/{spawn_id}       # Terminar hija
```

**Status**: ❌ TODOS no implementados

---

## 🎨 AUDITORÍA VISUAL (FRONTEND)

### Componentes Presentes

#### 1. **StatusBar** (5 líneas)
```tsx
Operator ▸ Tentáculo Link 🟢
Health: 5/9
```
✅ **Función**: Indica conexión + contador módulos ok/total  
❌ **Limitación**: Sin detalles, sin indicadores de carga, sin drill-down

#### 2. **Dashboard** (30 líneas)
```tsx
System Dashboard
[chip] madre: ok [chip] switch: ok [chip] hermes: ok ...
Recent Events (últimos 5)
- channel: event, type: status, source: madre
```
✅ **Función**: Overview de módulos + eventos recientes  
❌ **Limitación**:
- Solo muestra chips "ok/fail", no detalles
- Eventos muy genéricos, sin contexto
- Sin filtrado por canal

#### 3. **ChatPanel** (25 líneas)
```tsx
Chat (Switch)
[filter por canal="chat"]
[input] Send
```
✅ **Función**: Interface de chat básica  
❌ **Limitación**:
- Solo conecta con Switch, sin contexto de Madre
- Sin historial persistente
- Sin indicador de modelo activo

#### 4. **ShubPanel** (10 líneas)
```tsx
Shub Dashboard
"Monitor Shub sessions and audio analysis"
"Recommendations: coming soon"
```
❌ **Función**: Solo placeholder  
❌ **Limitación**: Completamente no funcional

#### 5. **API Service** (25 líneas)
```ts
fetchSystemStatus()       → GET /system/status
validateManifest()        → POST /manifest/validate
fetchJSON()               → Generic fetch wrapper
wsConnect()               → WebSocket bridge
```
✅ **Función**: Abstracción básica  
❌ **Limitación**: 
- Sin métodos para planes, hijas, cola, auditoría
- Sin manejo de errores específicos
- Sin retry logic

---

## 📋 COMPONENTES FALTANTES PARA v6.4 COMPLETO

### Panel 1: PLANES Y ORQUESTACIÓN (MadrePanel)
**Propósito**: Visualizar planes creados, feedback inicial, delegaciones  
**Datos necesarios**:
```json
{
  "plans": [
    {
      "plan_id": "uuid-123",
      "prompt": "Validar sistema",
      "created_at": "2025-12-04T10:00:00Z",
      "feedback": {
        "model": "deepseek",
        "reply": "Plan sugerido: validar switch→hermes→spawner"
      },
      "delegations": [
        {"target": "switch", "action": "route", "status": "pending"},
        {"target": "hermes", "action": "search_models", "status": "running"}
      ],
      "status": "executing"
    }
  ]
}
```
**Componentes UI**:
- Timeline de planes
- Detalle de feedback por plan
- Árbol de delegaciones (collapsible)
- Status badge (pending|running|done|failed)

---

### Panel 2: HIJAS Y PROCESOS (SpawnerPanel)
**Propósito**: Monitorear procesos efímeros creados por Madre→Spawner  
**Datos necesarios**:
```json
{
  "spawns": [
    {
      "spawn_id": "uuid-456",
      "cmd": "python3 scripts/validate.py",
      "status": "running",
      "pid": 12345,
      "memory_mb": 128,
      "cpu_percent": 45.2,
      "started_at": "2025-12-04T10:05:00Z",
      "ttl_seconds": 300,
      "parent_task_id": "uuid-123",
      "stdout": "[running...stream]",
      "stderr": ""
    }
  ]
}
```
**Componentes UI**:
- Tabla de procesos (vivos/muertos)
- Gráfico mini de CPU/Memoria
- Logs streaming (tail 50 líneas)
- Botón "Kill spawn" + "View full output"
- Indicador TTL (barra de cuenta regresiva)

---

### Panel 3: COLA PRIORITARIA (SwitchQueuePanel)
**Propósito**: Visualizar cola persistente, modelo activo, próximas tareas  
**Datos necesarios**:
```json
{
  "queue": {
    "size": 12,
    "active_model": "deepseek-r1",
    "model_memory_mb": 4096,
    "mode": "BALANCED",
    "next": [
      {
        "task_id": "uuid-001",
        "priority": 1,
        "source": "shub",
        "prompt_preview": "Análisis audio track-03...",
        "estimated_wait_s": 2
      },
      {
        "task_id": "uuid-002",
        "priority": 2,
        "source": "operator",
        "prompt_preview": "Validar manifest...",
        "estimated_wait_s": 5
      }
    ]
  }
}
```
**Componentes UI**:
- Indicador modelo activo + memoria
- Tamaño cola con barra visual
- Lista próximas 5 tareas con prioridad
- Modo operacional (ECO|BALANCED|HIGH-PERF|CRITICAL)
- Botón "Preload next model"

---

### Panel 4: MODELOS Y REGISTRY (HermesPanel)
**Propósito**: Visualizar modelos locales, registro remoto, estado descarga  
**Datos necesarios**:
```json
{
  "models": {
    "local": [
      {
        "name": "mistral-7b-instruct",
        "size_gb": 4.2,
        "location": "/app/models/hermes/mistral-7b-instruct",
        "loaded": true,
        "memory_usage_mb": 2048,
        "last_used": "2025-12-04T10:10:00Z"
      }
    ],
    "registry": [
      {
        "name": "deepseek-r1",
        "source": "huggingface",
        "size_gb": 7.0,
        "downloaded": false,
        "available": true
      }
    ],
    "cli_commands": [
      {
        "cmd": "analyze_audio",
        "provider": "hermes",
        "registered": true,
        "last_execution": "2025-12-04T09:50:00Z"
      }
    ]
  }
}
```
**Componentes UI**:
- Tabs: Local | Registry | CLI Commands
- Tabla modelos cargados (con toggle carga/descarga)
- Barra descarga para modelos no locales
- Inspector de uso memoria
- Registro CLI con timestamps

---

### Panel 5: AUDITORÍA Y SANDBOX (MCPPanel)
**Propósito**: Visualizar ejecuciones de sandbox, auditoría, logs de seguridad  
**Datos necesarios**:
```json
{
  "sandbox": {
    "executions": [
      {
        "exec_id": "uuid-789",
        "code_hash": "sha256-abc...",
        "timestamp": "2025-12-04T10:15:00Z",
        "status": "success",
        "duration_ms": 234,
        "imports": ["os", "sys"],
        "forbidden_detected": false,
        "output": "result: valid",
        "audit_log": "exec_allowed|import_check_ok|timeout_ok"
      }
    ],
    "audit_stats": {
      "total_executions": 1024,
      "security_violations": 3,
      "avg_execution_time_ms": 156
    }
  }
}
```
**Componentes UI**:
- Tabla auditoría (timestamp, status, duración)
- Inspector de código (read-only syntax highlight)
- Logs de seguridad (forbidden imports, timeouts)
- Stats resumen (total, violaciones, avg tiempo)
- Export audit log button

---

### Panel 6: TAREAS Y REINA (HormigueroPanel)
**Propósito**: Visualizar tareas clasificadas por Reina, estado progreso  
**Datos necesarios**:
```json
{
  "tasks": {
    "pending": [
      {
        "task_id": "uuid-001",
        "description": "Validar manifests",
        "classification": "validation",
        "priority": "high",
        "created_at": "2025-12-04T09:00:00Z",
        "estimated_duration_s": 30
      }
    ],
    "in_progress": [
      {
        "task_id": "uuid-002",
        "description": "Procesar audio",
        "progress_percent": 65,
        "queen_assigned_at": "2025-12-04T10:00:00Z"
      }
    ],
    "completed": [
      {
        "task_id": "uuid-003",
        "description": "Análisis drift",
        "result": "ok",
        "completed_at": "2025-12-04T10:10:00Z"
      }
    ]
  }
}
```
**Componentes UI**:
- Tabs: Pending | In Progress | Completed
- Tabla tareas con clasificación color-coded
- Barra progreso para tareas en ejecución
- Timeline histórico (últimas 24h)
- Métricas (total completadas, tiempo promedio)

---

### Panel 7: MINIMAPA DEL SISTEMA
**Propósito**: Visualización rápida de flujo completo, estado cada módulo  
**Componentes UI**:
```
┌─────────────────────────────────────────────┐
│  VX11 v6.4 System Overview                  │
├─────────────────────────────────────────────┤
│                                             │
│   [User Input] ──→ [Tentáculo Link] ──→ ... │
│                           ↓                 │
│                    [Madre Planner]          │
│                    ├→ feedback              │
│                    └→ delegates             │
│                                             │
│   ┌─ [Switch] ─ Queue: 12, Model: active   │
│   │  ├─ [Hermes] - Models: 3 local         │
│   │  ├─ [Spawner] - Hijas: 5 running      │
│   │  └─ [MCP] - Audit: 1024 exec          │
│   │                                         │
│   └─ [Hormiguero] - Reina Tasks: 24        │
│                                             │
│   Status: 🟢 All ok                        │
│   Memory: 2.3/8.0 GB  CPU: 35%            │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔧 VALIDACIÓN DE ENDPOINTS BACKEND

### Endpoints Existentes

| Endpoint | Método | Auth | Status | Implementación |
|----------|--------|------|--------|-----------------|
| `/health` | GET | ❌ | ✅ | HealthResponse |
| `/system/status` | GET | ✅ | ✅ | Aggregated via Tentáculo |
| `/intent` | POST | ✅ | ✅ | Proxy a Tentáculo Link |
| `/intent/chat` | POST | ✅ | ✅ | SwitchClient.chat() |
| `/shub/upload` | POST | ✅ | ✅ | Via Tentáculo + Shub |
| `/shub/run` | POST | ✅ | ✅ | ShubClient.run_mode_c() |
| `/manifest/validate` | POST | ✅ | ✅ | ManifestatorClient |
| `/jobs/{job_id}` | GET | ✅ | ✅ | JobQueue.get() |
| `/jobs/{job_id}/cancel` | POST | ✅ | ✅ | JobQueue.cancel() |
| `/health/aggregate` | GET | ✅ | ✅ | HealthAggregator.collect() |
| `/ws` | WEBSOCKET | ⚠️ | ✅ | Bridge a Tentáculo |
| `/api/process` | POST | ✅ | ✅ | OperatorBrain.process_input() |
| `/api/analyze-intent` | POST | ✅ | ✅ | OperatorBrain._detect_intent() |
| `/api/system-status` | GET | ✅ | ✅ | Alias `/system/status` |
| `/api/switch-model` | POST | ✅ | ✅ | ModelRotator.default |
| `/api/manifest/validate` | POST | ✅ | ✅ | Alias de `/manifest/validate` |
| `/api/shub/run_mode_c` | POST | ✅ | ✅ | Alias de `/shub/run` |

### Endpoints Faltantes (Críticos para v6.4)

```python
# PLANES Y ORQUESTACIÓN
GET /plans                       # Todos los planes
GET /plans/{plan_id}             # Detalle + feedback
POST /plans/{plan_id}/execute    # Gatillar ejecución

# PROCESOS EFÍMEROS (Spawner)
GET /spawns                      # Hijas activas
GET /spawns/{spawn_id}           # Detalle hija
GET /spawns/{spawn_id}/logs      # Stream logs
POST /spawns/{spawn_id}/kill     # Terminar hija
GET /spawns/{spawn_id}/metrics   # CPU/Memory

# COLA PRIORITARIA (Switch)
GET /queue                       # Estado cola
GET /queue/next                  # Próxima tarea
GET /queue/status                # Tamaño + modelo activo
POST /queue/preload-model        # Precalentar modelo

# HERMES (Modelos)
GET /models                      # Local + registry
GET /models/local                # Solo locales
GET /models/registry             # Solo remoto
POST /models/download/{name}     # Descargar modelo
POST /models/unload/{name}       # Descargar RAM

# MCP (Auditoría)
GET /audit/executions            # Todos los ejecutados
GET /audit/executions/{exec_id}  # Detalle
GET /audit/violations            # Solo violaciones
POST /audit/export               # Export completo

# HORMIGUERO (Tareas + Reina)
GET /tasks                       # Todas tareas
GET /tasks/pending               # Solo pendientes
GET /tasks/in-progress           # Solo en progreso
GET /tasks/{task_id}             # Detalle tarea
```

**Status**: ❌ CERO implementados

---

## 🎯 MEJORAS UX RECOMENDADAS

### 1. Logs en Streaming
**Actuales**: Eventos encolados, max 50  
**Recomendado**:
- WebSocket `/logs/stream?channel=operador|switch|hermes|spawner|all`
- Tail en vivo de logs de módulos
- Filtrado por nivel (INFO|WARN|ERROR|DEBUG)
- Auto-scroll con pausable

### 2. Collapsible Panels
**Actual**: Layout fijo 3 columnas  
**Recomendado**:
- Tabs collapsibles por módulo
- Drag-n-drop reordenable
- Preset layouts (compact|full|focus-switch|focus-hermes)
- Remember user preference

### 3. Visualizador de Flujos Tentaculares
**Actual**: Nada  
**Recomendado**:
- Diagrama mermaid/cytoscape en tiempo real
- Nodos: Tentáculo, Madre, Switch, Hermes, Spawner, MCP, Hormiguero
- Aristas: Requests activos (pulsantes si en progreso)
- Hover: Tooltip con endpoint + latencia

### 4. Minimapa del Sistema
**Actual**: Status bar líneal  
**Recomendado**:
- Grid 3x3 de módulos
- Color: 🟢=ok, 🟡=slow (>500ms), 🔴=down
- Size del cuadro = CPU/Memory usage
- Click → drill-down a ese módulo

### 5. Indicadores de Carga por Módulo
**Actual**: Chip "ok" simple  
**Recomendado**:
- Gráfico mini sparkline (CPU %)
- Barra memoria (0-100%)
- Latencia median (ms)
- Última actualización (ago)

### 6. Vista Real de Tareas Multi-paso
**Actual**: Chat plano + intent parseado  
**Recomendado**:
- Gantt chart de planes
- Hijas como nodos expandibles
- Timeline de eventos
- Rastreo de contexto (context7)

### 7. Export/Import de Configuración
**Actual**: Ninguno  
**Recomendado**:
- Export estado actual (JSON)
- Import preset (dev|staging|prod)
- Guardar favoritos de búsquedas/filtros

### 8. Dark Mode + Temas
**Actual**: Uno solo  
**Recomendado**:
- Toggle dark/light
- Personalizable (colors, fonts)
- Preset: github, nord, dracula, solarized

---

## 📐 ARQUITECTURA VISUAL SUGERIDA

### Layout Propuesto (Full v6.4)

```
┌──────────────────────────────────────────────────────────────┐
│ StatusBar: Tentáculo 🟢 | Health 9/9 | CPU 35% | Mem 2.3GB  │
├──────────────────────────────────────────────────────────────┤
│ [▼] Planes  [▼] Hijas  [▼] Cola  [▼] Modelos  [▼] Auditoría │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─ PLANES (Madre)          ┌─ HIJAS (Spawner)              │
│  │ ├─ Plan #1               │ ├─ [running] pid=1234         │
│  │ │  ├─ feedback: deepseek │ │  CPU:45% Mem:128MB          │
│  │ │  ├─ [→] switch         │ │  [logs] [kill]              │
│  │ │  └─ [→] hermes         │ ├─ [idle] pid=5678           │
│  │ └─ Plan #2               │ └─ [dead] pid=9999           │
│  │                          │                               │
│  ├─ COLA (Switch)           ├─ MODELOS (Hermes)            │
│  │ Active: deepseek-r1      │ Local:                       │
│  │ Memory: 4GB/8GB          │  ├─ mistral-7b [4.2GB] ✓    │
│  │ Queue: ▓▓▓░░░░░░  12     │  ├─ llama-13b [6.0GB] ✓     │
│  │ Next: [shub] audio...    │ Registry:                    │
│  │ Mode: BALANCED           │  ├─ deepseek-r1 [7.0GB]     │
│  │                          │  └─ mixtral-8x7b [26GB]      │
│  │ ┌─ AUDITORÍA (MCP)       │                              │
│  │ │ Exec: 1024 total       ├─ TAREAS (Hormiguero)        │
│  │ │ Violations: 3          │ Pending: 5                   │
│  │ │ Avg time: 156ms        │ In Progress: 3               │
│  │ │ Last: sha256-abc...    │ Completed (24h): 127         │
│  │ └─                       │                              │
│  │                          │                              │
│  └─ LOGS (Streaming)        ├─ CHAT (Switch)              │
│    [INFO] madre: plan_created_uuid-1  │ You: Validar...   │
│    [WARN] switch: model_loading...    │ Bot: Plan...      │
│    [INFO] hermes: download_ok model   │ [Send]            │
│    [DEBUG] spawner: hija_ttl=300s...  │                  │
│    [ERROR] mcp: forbidden_import...   │                  │
│                                       │                  │
└───────────────────────────────────────┴───────────────────┘
```

---

## 🚨 FALLOS DETECTADOS Y RIESGOS

### Críticos (Bloquean v6.4)

1. **❌ Sin acceso a Planes de Madre**
   - Riesgo: Operador ciego a decisiones orquestación
   - Impacto: No puede auditar o re-ejecutar planes
   - Fix: Implementar cliente Madre + `/plans` endpoint

2. **❌ Sin visibilidad de Spawner**
   - Riesgo: Hijas fantasma sin monitoreo
   - Impacto: Memory leak, procesos zombies
   - Fix: Implementar cliente Spawner + `/spawns` endpoint

3. **❌ Cola Switch oculta**
   - Riesgo: Desconoce estado queue, modelo activo
   - Impacto: No puede optimizar orden tareas
   - Fix: Exponer `/queue/status` + `/queue/next`

### Mayores (Degradan operabilidad)

4. **⚠️ WebSocket sin canales específicos**
   - Riesgo: Ruido, difícil filtrar eventos
   - Impacto: Dashboard pesado con 100+ eventos/min
   - Fix: Implementar canales: `operador|madre|switch|hermes|etc`

5. **⚠️ Job Queue en memoria**
   - Riesgo: Pérdida de estado si restart
   - Impacto: No persiste intenciones
   - Fix: Mover JobQueue → BD (`job_queue` table)

6. **⚠️ HealthAggregator timeout fijo 3s**
   - Riesgo: Módulos lentos mostrados como "fail"
   - Impacto: False positives en dashboard
   - Fix: Implementar circuit breaker con degradado

### Menores (UX/Polish)

7. **⚠️ Sin logs streaming en vivo**
   - Riesgo: Debugging difícil durante operación
   - Impacto: Operador debe SSH a contenedor
   - Fix: Implementar `/logs/stream?module=X` WebSocket

8. **⚠️ Componentes UI demasiado simples**
   - Riesgo: Imposible operar sistema complejo
   - Impacto: Overload cognitivo, errores operador
   - Fix: Agregar paneles modulares, collapsibles, drill-down

---

## 📝 LISTA DE IMPLEMENTACIÓN MÍNIMA PARA v6.4

### Backend Endpoints (Prioridad)

**Tier 1 - Críticos**:
```
POST /clients/madre.py              # MadreClient para planes
POST /clients/spawner.py            # SpawnerClient para hijas
GET  /plans                         # Retrieve all planes
GET  /plans/{plan_id}               # Retrieve plan detail
GET  /spawns                        # Retrieve all hijas
GET  /spawns/{spawn_id}             # Retrieve hija detail
GET  /queue/status                  # Switch queue state
```

**Tier 2 - Importantes**:
```
GET  /spawns/{spawn_id}/logs        # Stream hija logs
POST /spawns/{spawn_id}/kill        # Terminar hija
GET  /models                        # Hermes models
GET  /audit/executions              # MCP auditoría
GET  /tasks                         # Hormiguero tareas
```

**Tier 3 - Mejoras UX**:
```
POST /jobs → save in BD             # JobQueue persistence
GET  /logs/stream WebSocket         # Logs en vivo
POST /preset/save                   # Save layout
POST /preset/load                   # Load layout
```

### Frontend Components (Prioridad)

**Tier 1 - Critical Panels**:
- [ ] `MadrePanel.tsx` - Plans + feedback + delegations
- [ ] `SpawnerPanel.tsx` - Hijas vivas + logs + metrics
- [ ] `SwitchQueuePanel.tsx` - Cola + modelo + próximas tareas
- [ ] Update `api.ts` con nuevos fetch functions

**Tier 2 - Information Panels**:
- [ ] `HermesPanel.tsx` - Modelos local/registry
- [ ] `MCPPanel.tsx` - Auditoría sandbox
- [ ] `HormigueroPanel.tsx` - Tareas + Reina
- [ ] `MiniMapPanel.tsx` - Overview sistema

**Tier 3 - UX Enhancements**:
- [ ] Collapsible tabs
- [ ] Drag-n-drop reordenable
- [ ] Dark mode toggle
- [ ] Export/import layouts
- [ ] Logs streaming panel

---

## 🔄 MATRIZ DE CAMBIOS PROPUESTOS

| Área | Cambio | Líneas | Prioridad | Sprint |
|------|--------|--------|-----------|--------|
| Backend | Agregar MadreClient | +50 | Crítico | 1 |
| Backend | Agregar SpawnerClient | +50 | Crítico | 1 |
| Backend | Endpoints `/plans/*` | +100 | Crítico | 1 |
| Backend | Endpoints `/spawns/*` | +120 | Crítico | 1 |
| Backend | Endpoints `/queue/*` | +60 | Crítico | 1 |
| Backend | Endpoints `/models/*` | +80 | Mayor | 2 |
| Backend | Endpoints `/audit/*` | +70 | Mayor | 2 |
| Backend | Endpoints `/tasks/*` | +70 | Mayor | 2 |
| Backend | JobQueue→BD | +40 | Mayor | 2 |
| Backend | WebSocket canales | +60 | Mayor | 2 |
| Frontend | MadrePanel | +200 | Crítico | 1 |
| Frontend | SpawnerPanel | +250 | Crítico | 1 |
| Frontend | SwitchQueuePanel | +180 | Crítico | 1 |
| Frontend | Update api.ts | +150 | Crítico | 1 |
| Frontend | HermesPanel | +200 | Mayor | 2 |
| Frontend | MCPPanel | +180 | Mayor | 2 |
| Frontend | HormigueroPanel | +180 | Mayor | 2 |
| Frontend | MiniMapPanel | +250 | Mayor | 2 |
| Frontend | Collapsibles + layout | +300 | Mejora | 3 |

**Total LOC estimado**:
- Tier 1 (Crítico): ~1,800 líneas
- Tier 2 (Mayor): ~1,200 líneas
- Tier 3 (Mejora): ~300 líneas
- **Total**: ~3,300 líneas nuevas

---

## 🎬 RECOMENDACIONES FINALES

### Corto Plazo (Semana 1)
1. ✅ Implementar clientes Madre + Spawner en backend
2. ✅ Exponer endpoints críticos (`/plans/*`, `/spawns/*`)
3. ✅ Crear `MadrePanel.tsx` + `SpawnerPanel.tsx`
4. ✅ Actualizar `api.ts` con nuevos métodos
5. ✅ Testar endpoints con Tentáculo vivo

### Mediano Plazo (Semana 2)
6. ⏳ Agregar endpoints cola, modelos, auditoría
7. ⏳ Crear `HermesPanel`, `MCPPanel`, `HormigueroPanel`
8. ⏳ Persistencia JobQueue en BD
9. ⏳ WebSocket canales específicos

### Largo Plazo (Semana 3+)
10. 🔮 Collapsibles, layouts, dark mode
11. 🔮 Minimapa del sistema
12. 🔮 Logs streaming en vivo
13. 🔮 Export/import configuración
14. 🔮 Performance: virtualization, memoization

### Validación Post-Implementación
- [ ] Todos los endpoints nuevos responden <200ms
- [ ] Frontend carga <2s
- [ ] WebSocket no pierde eventos
- [ ] Health aggregator 100% cobertura módulos
- [ ] Tests E2E: crear plan → ejecutar → ver hijas → completar
- [ ] Documentación OpenAPI completa
- [ ] Audit trail: todas operaciones logged

---

## 📊 CONCLUSIÓN

**VX11 Operator v6.4 está en estado FUNCTIONAL PERO INCOMPLETO:**

- ✅ **Backend**: Conecta con Tentáculo Link, clientes básicos funcionales
- ✅ **Frontend**: React/Vite renderiza, WebSocket vivo
- ⚠️ **Arquitectura**: Parcialmente alineada, faltan capas críticas
- ❌ **Visualización**: Minimalista; no representa planes, hijas, colas, auditoría
- ❌ **UX**: 25/100; falta logging, collapsibles, visualizadores, mini-map

**Para v6.4 COMPLETO** se requieren ~3,300 LOC nuevas distribuidas en:
1. **Tier 1 (Crítico)**: ~1,800 LOC → MadrePanel, SpawnerPanel, endpoints planes/hijas
2. **Tier 2 (Mayor)**: ~1,200 LOC → Hermes/MCP/Hormiguero panels + canales WS
3. **Tier 3 (Mejora)**: ~300 LOC → Collapsibles, layouts, dark mode

**Recomendación**: Implementar Tier 1 primero (~5-7 días dev), luego Tier 2 (~3-5 días), finalmente Tier 3 (polish, ~2-3 días).

---

**Auditoría completada sin modificaciones.**  
*Listo para pasar a fase de implementación.*
