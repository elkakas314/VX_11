# VX11 v7.1 — Instrucciones Canónicas para Agentes de Código IA

**Versión:** 7.1 | **Actualizado:** 2025-12-14  
**Audiencia:** GitHub Copilot, Claude, y agentes IA trabajando en VX11.  
**Objetivo:** Máxima productividad inmediata sin hacer preguntas, respetando arquitectura, seguridad y convenciones.

---

## 🎯 TL;DR — Lo Esencial

**Stack:** FastAPI (9 módulos Python) + React 18 (Vite) + SQLite + Docker Compose  
**Puertos:** 8000–8008 (módulos), 8011 (Operator API), 8020 (Operator UI)  
**DB:** `/data/runtime/vx11.db` (single-writer, todas las tablas unificadas)  
**Token:** Header `X-VX11-Token: vx11-local-token` en todas las solicitudes HTTP  
**Frontend:** TanStack Query (caching) + WebSocket (reconnection automática) + React 18  
**Flujo típico:** Intent → Tentáculo Link → Switch (IA routing) → Executor (Hermes/Madre/Shub) → BD

---

## 🏗️ ARQUITECTURA CANÓNICA: 9 Módulos HTTP-Only

### Topología Física

### Servicios Distribuidos (HTTP-Only, Zero Coupling)

```
┌─────────────────────────────────────────────────────────────┐
│             TENTÁCULO LINK (8000, alias "gateway")          │
│  Gateway + Router Table + Circuit Breaker + Context-7 TTL   │
│                                                               │
│  ├─ Madre (8001)          ← Orquestación autónoma + P&P     │
│  ├─ Switch (8002)         ← Router IA (selección modelos)   │
│  ├─ Hermes (8003)         ← CLI + autodescubrimiento HF     │
│  ├─ Hormiguero (8004)     ← Paralelización (Queen + Ants)   │
│  ├─ Manifestator (8005)   ← Auditoría + parches automáticos │
│  ├─ MCP (8006)            ← Conversacional                   │
│  ├─ Shubniggurath (8007)  ← Procesamiento IA avanzado       │
│  └─ Spawner (8008)        ← Hijas efímeras                   │
│                                                               │
│  ├─ Operator Backend (8011)    ← Chat persistido, BD         │
│  └─ Operator Frontend (8020)   ← React 18 + WebSocket       │
└─────────────────────────────────────────────────────────────┘
```

| Módulo | Puerto | Responsabilidad Clave |
|--------|--------|---|
| **Tentáculo Link** | 8000 | HTTP gateway auth + route table + circuit breaker |
| **Madre** | 8001 | Tareas autónomas, P&P (off/standby/active), toma decisiones |
| **Switch** | 8002 | Router IA adaptativo: local/CLI/remote/DeepSeek selección |
| **Hermes** | 8003 | CLI execution + HuggingFace autodiscovery + modelos locales |
| **Hormiguero** | 8004 | Paralelización: Queen + Ant workers, escalado automático |
| **Manifestator** | 8005 | Drift detection + patch generation/application |
| **MCP** | 8006 | Conversational interface, intent parsing |
| **Shubniggurath** | 8007 | Audio/video processing, IA pipelines |
| **Spawner** | 8008 | Spawn/manage ephemeral child processes |
| **Operator Backend** | 8011 | `/operator/chat` + session persistence (OperatorSession DB) |
| **Operator Frontend** | 8020 | React 18 + TanStack Query caching + WebSocket reconnection |

### Routing & Discovery

- **Route Table:** `tentaculo_link/routes.py` (intent type → module endpoint mapping)
  - IntentType: CHAT, CODE, AUDIO, ANALYSIS, TASK, SPAWN, STREAM
  - Static configuration, versionable, performante
- **Circuit Breaker:** `tentaculo_link/clients.py` (resiliente failover)
  - Estados: CLOSED (normal) → OPEN (falla) → HALF_OPEN (recovery)
  - Threshold: 3 fallos, recovery timeout: 60s
- **Context-7 Sessions:** `tentaculo_link/context7_middleware.py` (TTL sessions con topic clustering)
  - Persistencia en `data/runtime/context7_sessions.json` (append-only)

### Layout de Código (Producción vs Dev)

- **`tentaculo_link/`** — Gateway (8000), route table, circuit breaker, context-7
- **`operator_backend/backend/`** — Backend API (8011): `/operator/chat`, session persistence
- **`operator_backend/frontend/`** — React 18 (8020): TanStack Query + WebSocket + Monaco editor
- **`config/`** — Shared: module_template, db_schema, settings, tokens, forensics
- **`data/runtime/`** — BD unificada `vx11.db` (SQLite single-writer pattern)

### No Duplicados: Estructura Rígida

- NO crear `operator_v2/` o `operator_backup/` — todo en `operator_backend/` o archiva en `operator_backend/legacy/`.
- NO cambiar puertos en `docker-compose.yml` — son puntos de rigidez arquitectónica.
- NO mover módulos raíz sin autorización — afecta toda la topología HTTP.

---

## 🧹 Reglas de Limpieza Perpetua

**Nunca tracked:**
- `node_modules/`, `dist/`, `build/`, `.venv/`, `*.egg-info/`, `__pycache__/`, `.pytest_cache/`
- `logs/*.txt` (reponable), `data/runtime/` excepto schema
- Secretos: `tokens.env`, `.env.local`, cualquier API key

**Docs canónicas (versionadas en git):**
- `docs/` — APIs, arquitectura, deployment
- `docs/audit/` — Reportes de fases ejecutadas, decisiones de diseño
- `.copilot-audit/` — Auditorías exhaustivas (Operator FASE1–4)

**Legacies:**
- Si deprecas código, archiva en `src/legacy/` con nombre + fecha, no borres.
- Actualiza imports en docs y code para no referenciar accidentalmente.

---

## 🚀 Cómo Ejecutar Flujos VX11 a Bajo Coste

### Principios

1. **Preferir HTTP local** — Usa curl a endpoints locales en lugar de spawning de procesos pesados.
2. **DeepSeek R1 solo para razonamiento pesado** — Para tareas ligeras (chat corto, chequeos), usar modelo local o Copilot mismo.
3. **Intent → Madre → Spawner → Hija → BD → Muere** — Flujo operativo: envía intent a madre, ella planifica y spawnea hijas efímeras, reportan resultados a BD, se terminan automáticamente.

### Flujo Operativo Típico (HTTP-Only, Sin Imports Cruzados)

```
1. INTENT (desde operator, webhook, o sistema)
   ↓
2. Tentáculo Link (gateway, valida token, circuit breaker)
   ↓
3. Madre (router table → módulo target)
   ↓
4. Switch (elige modelo: local, CLI, remote)
   ↓
5. Hermes/Local/CLI (ejecuta, responde)
   ↓
6. Response → BD (via tentaculo_link o directo)
   ↓
7. Hija efímera muere (auto-cleanup)
```

### Comandos Listos (HTTP-Only)

```bash
# Health checks
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8001/madre/health
curl -s http://127.0.0.1:8002/switch/health
curl -s http://127.0.0.1:8011/operator/health

# Status del gateway
curl -s http://127.0.0.1:8000/vx11/status

# Consultar Switch (route-v5)
curl -X POST http://127.0.0.1:8002/switch/route-v5 \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","task_type":"chat"}'

# Chat Operator (esperado en fase F)
curl -X POST http://127.0.0.1:8011/operator/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"hola","session_id":"test-session"}'

# Context-7 (sesiones TTL, si existe)
curl -s http://127.0.0.1:8000/vx11/context-7/sessions \
  -H "X-VX11-Token: vx11-local-token"
```

### Tarea Larga (Polling)

```bash
# 1. Crear tarea (via Madre o Spawner)
TASK_ID=$(curl -X POST http://127.0.0.1:8001/madre/task \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"intent":"analyze_code","priority":5}' | jq -r .task_id)

# 2. Polling (cada 2s hasta completed|failed)
while true; do
  STATUS=$(curl -s http://127.0.0.1:8001/madre/task/$TASK_ID \
    -H "X-VX11-Token: vx11-local-token" | jq -r .status)
  case $STATUS in
    completed|failed) break ;;
    *) sleep 2 ;;
  esac
done

# 3. Obtener resultado
curl -s http://127.0.0.1:8001/madre/task/$TASK_ID \
  -H "X-VX11-Token: vx11-local-token" | jq .
```

---

## 🎓 Patrones Esenciales de Código

### 1. Estructura de FastAPI Modules

Todos los módulos siguen el mismo patrón. Usar [config/module_template.py](../../config/module_template.py):

```python
from config.module_template import create_module_app

app = create_module_app("mi_modulo")

@app.post("/mi_modulo/mi-endpoint")
async def mi_endpoint(req: dict):
    return {"resultado": "ok"}
```

**Reglas:**
- Endpoint namespaced: `/{modulo}/{versión}/{recurso}`
- Siempre async
- Validar header `X-VX11-Token` via config.tokens

### 2. Llamar Otro Módulo (HTTP, Zero Coupling)

```python
import httpx
from config.settings import settings
from config.tokens import get_token

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

async def call_switch(prompt: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.switch_url}/switch/route-v5",
            json={"prompt": prompt, "task_type": "chat"},
            headers=AUTH_HEADERS
        )
        resp.raise_for_status()
        return resp.json()
```

**Reglas:**
- NO imports entre módulos
- Siempre usar `settings.{module}_url` (DNS-aware)
- Timeout explícito
- Header `X-VX11-Token` obligatorio
- Maneja 401/404/timeout con fallback

### 3. Base de Datos (Single-Writer Pattern)

```python
from config.db_schema import get_session, Task, Context

db = get_session("mi_modulo")
try:
    task = Task(uuid="...", name="test", module="mi_modulo", status="pending")
    db.add(task)
    db.commit()
    
    # Leer
    ctx = db.query(Context).filter_by(task_id=task.uuid).first()
finally:
    db.close()  # ✅ OBLIGATORIO en finally
```

**Reglas:**
- Siempre `db.close()` en finally
- No dejar sesiones abiertas (memory leak)
- Tablas: ver [config/db_schema.py](../config/db_schema.py) (Task, Context, OperatorSession, OperatorMessage, etc.)

### 4. Autenticación y Tokens

```python
from config.tokens import get_token

# ✅ Siempre así:
TOKEN = get_token("ENV_VAR_NAME")  # lee de env, no hardcodea
HEADERS = {"X-VX11-Token": TOKEN}
```

**Reglas:**
- NUNCA hardcodear tokens
- Siempre desde `config/tokens.py` o `config/settings.py`
- Header exacto: `X-VX11-Token`

### 5. Logging y Forensics

```python
import logging
from config.forensics import write_log

log = logging.getLogger(__name__)

log.info("evento importante")
write_log("mi_modulo", "evento_importante", level="INFO")
```

### 6. Frontend: React 18 + TanStack Query

**Arquitectura Operator UI:**
- **Vite dev server** (port 5173) con HMR para desarrollo local
- **React 18 con Concurrent features** activadas
- **TanStack Query v5** para caching automático (ya instalado en package.json)
- **Zustand** para state management (store.ts)
- **WebSocket reconnection automática** con exponential backoff (hasta 30s)

**Patrón: Custom Hooks con TanStack Query**

```typescript
// En operator_backend/frontend/src/services/api-improved.ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useChat(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch(`/operator/chat`, {
        method: "POST",
        headers: { "X-VX11-Token": TOKEN_VALUE, "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message }),
      });
      return response.json();
    },
    onSuccess: () => {
      // Auto-invalidate session queries para refetch
      queryClient.invalidateQueries({ queryKey: ["operatorSession", sessionId] });
    },
  });
}

export function useOperatorSession(sessionId: string) {
  return useQuery({
    queryKey: ["operatorSession", sessionId],
    queryFn: async () => {
      const response = await fetch(`/operator/session/${sessionId}`, {
        headers: { "X-VX11-Token": TOKEN_VALUE },
      });
      return response.json();
    },
    staleTime: 30000, // 30s
    cacheTime: 5 * 60 * 1000, // 5 min
    retry: 1,
  });
}
```

**Reglas Frontend:**
- Siempre usar `import.meta.env.VITE_*` para config (env vars en build time)
- WebSocket URL: `${OPERATOR_BASE_URL.replace(/^http/, "ws")}/ws`
- Token de config: `config.ts` centralizado
- Componentes lazy-loaded si tamaño >30KB
- Style: inline o CSS modules, NO Tailwind en componentes críticos

---

## 📋 MODO NO-PREGUNTAR (Copilot)

**Regla de oro:** Actúa por fases, escribe REPORTs, NO pidas confirmación.

**Auto-STOP solo si:**
- Token/credencial expuesto en código (fail CI, corrije antes de commit)
- `node_modules/` o `dist/` en git (remueve, actualiza `.gitignore`)
- Tests reventados (ejecuta localmente, diagnóstica, repara o documenta bloqueador)
- Import cruzado entre módulos detectado (refactoriza a HTTP)

**Flujo:**
1. Lee plan
2. Crea rama + tag backup
3. Implementa por fase (0 → G → F → H)
4. Valida tras cada fase (tests, compile check, curl tests)
5. Commiteao lógico por fase
6. Genera REPORT per phase en `docs/audit/`
7. Cierre: `GFH_FINAL_SUMMARY.md`

---

## 🔍 Índice de Documentos Canónicos

### Arquitectura y Diseño
- [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) — Visión general
- [docs/API_REFERENCE.md](../../docs/API_REFERENCE.md) — Endpoints detallados
- [.copilot-audit/OPERATOR_AUDIT_FASE1_REAL_STATE.md](../../.copilot-audit/OPERATOR_AUDIT_FASE1_REAL_STATE.md) — Auditoría Operator (qué existe, qué no)

### Operativo y Deployment
- [docs/DEPLOYMENT_TENTACULO_LINK.md](../../docs/DEPLOYMENT_TENTACULO_LINK.md) — Tentáculo Link config
- [docs/WORKFLOWS_VX11_LOW_COST.md](../../docs/WORKFLOWS_VX11_LOW_COST.md) — Workflows a bajo costo (fase 0)
- [docs/API_OPERATOR_CHAT.md](../../docs/API_OPERATOR_CHAT.md) — Contrato `/operator/chat` (fase F)
- [docs/OPERATOR_UI_RUNTIME.md](../../docs/OPERATOR_UI_RUNTIME.md) — Cómo corre UI dev vs prod (fase H)

### Código Referencia
- [config/module_template.py](../../config/module_template.py) — Template módulo FastAPI
- [config/db_schema.py](../../config/db_schema.py) — Schema BD, `get_session()`
- [config/settings.py](../../config/settings.py) — URLs, env vars
- [config/tokens.py](../../config/tokens.py) — Gestión tokens
- [operator_backend/backend/main_v7.py](../../operator_backend/backend/main_v7.py) — Backend API

### Auditorías y Reportes de Fases
- [docs/audit/PHASE0_COPILOT_CONTROLPLANE_REPORT.md](../../docs/audit/PHASE0_COPILOT_CONTROLPLANE_REPORT.md)
- [docs/audit/PHASEF_OPERATOR_CHAT_IMPLEMENTATION_REPORT.md](../../docs/audit/PHASEF_OPERATOR_CHAT_IMPLEMENTATION_REPORT.md)
- [docs/audit/PHASEH_OPERATOR_UI_TIER1_REPORT.md](../../docs/audit/PHASEH_OPERATOR_UI_TIER1_REPORT.md)
- [docs/audit/GFH_FINAL_SUMMARY.md](../../docs/audit/GFH_FINAL_SUMMARY.md)

---

## 🎯 Quick Reference: Cambios Comunes

| Necesidad | Archivos a Tocar | Patrón |
|-----------|------------------|--------|
| Agregar endpoint | [operator_backend/backend/main_v7.py](../operator_backend/backend/main_v7.py) | usar `@app.post()`, validar token, delegar HTTP si es necesario |
| Agregar tabla BD | [config/db_schema.py](../config/db_schema.py) | usar `Base` + `Column`, add `create_if_not_exists`, NO migración destructiva |
| Llamar módulo remoto | Usa `httpx.AsyncClient` + `settings.{module}_url` | ver patrón "Llamar Otro Módulo" arriba |
| Agregar variable env | [config/settings.py](../config/settings.py) + `.env` | nunca hardcodear, sempre `settings.my_var` |
| Mejorar logs | [config/forensics.py](../config/forensics.py) | usar `write_log(module, event)` |

---

## ✅ Validación Pre-Commit

Antes de hacer push (o tras cada fase):

```bash
# Compilar Python (syntax check)
python -m compileall tentaculo_link operator_backend config || exit 1

# Tests (si existen)
pytest tests/ -q --tb=short || echo "⚠️ Tests failed, review"

# Frontend (si cambias operator_backend/frontend)
cd operator_backend/frontend && npm ci && npm run type-check && npm run build

# Docker compose (si cambias docker-compose.yml)
docker-compose config > /dev/null && echo "✓ Compose valid"

# Health checks (si sistema running)
for port in 8000 8001 8002 8011; do
  curl -s http://127.0.0.1:$port/health | jq . || echo "Port $port down"
done

# Git status
git status
git diff --stat
```

**En CI:** Ver `.github/workflows/ci.yml` — ejecuta py_compile, compose_validate, frontend_build automáticamente.

---

## 🛡️ Límites y "NO Tocar"

**❌ NUNCA CAMBIAR:**
- Puertos en `docker-compose.yml`
- Layout de módulos raíz (`switch/`, `madre/`, etc.) sin autorización
- `tokens.env.master`, `tokens.env`
- Schema de DB (solo INSERT/SELECT existentes, sin ALTER TABLE destructiva)

**✅ SEGUROS:**
- Lógica dentro de módulos (mantener endpoint namespacing)
- Frontend en [operator_backend/frontend/src/](../operator_backend/frontend/src/)
- Config en `settings.py` (env-aware, no hardcodes)
- Tests y docs
- Mensajes de log, docstrings

---

## 🤖 VX11 AGENTS SUITE (v7.1)

### Tres Agentes Operacionales Permanentes

**Ubicación:** `.github/copilot-agents/`

En Copilot Chat, escribe `@` y verás:
- **VX11-Operator** — Full execution (validation + workflows + autosync)
- **VX11-Inspector** — Audit only (read-only, never modifies)
- **VX11-Operator-Lite** — Low cost (rules-based, optional DeepSeek)

### VX11-Operator (FULL EXECUTION)

Commands:
```
@vx11-operator status          → Module health + drift detection
@vx11-operator validate        → Python + Docker + imports + tests
@vx11-operator fix drift       → Auto-repair stale files + violations
@vx11-operator run task: desc  → Execute via Madre (spawns hijas)
@vx11-operator chat: msg       → Chat with /operator/chat
@vx11-operator audit imports   → Deep import analysis
@vx11-operator cleanup         → Auto-maintenance
```

**Autosync:** Sí (si validación pasa).  
**DeepSeek:** Sí (reasoning).  
**Archivo:** `.github/copilot-agents/VX11-Operator.prompt.md`

### VX11-Inspector (AUDIT ONLY)

Commands (READ-ONLY, never executes):
```
@vx11-inspector audit structure   → Layout validation
@vx11-inspector audit imports     → Cross-module violations
@vx11-inspector audit security    → Secrets + .gitignore
@vx11-inspector audit ci          → Workflows
@vx11-inspector audit docs        → Staleness check
@vx11-inspector detect drift      → Full drift scan
@vx11-inspector forensics         → Deep analysis
```

**Output:** Reportes en `docs/audit/AUDIT_*_<timestamp>.md`  
**Autosync:** No (read-only).  
**Archivo:** `.github/copilot-agents/VX11-Inspector.prompt.md`

### VX11-Operator-Lite (LOW COST)

Commands (free/cheap, rules-based by default):
```
@vx11-operator-lite status        → Binary check
@vx11-operator-lite validate      → Syntax only
@vx11-operator-lite cleanup       → Safe ops
@vx11-operator-lite health        → HTTP checks
@vx11-operator-lite chat: msg     → Simple chat
@vx11-operator-lite use deepseek: task → Optional reasoning
```

**Autosync:** Solo docs/limpieza (safe).  
**DeepSeek:** No (a menos que `use deepseek:`).  
**Archivo:** `.github/copilot-agents/VX11-Operator-Lite.prompt.md`

### Tabla Rápida de Selección

| Necesidad | Agente | Tiempo | Costo |
|-----------|--------|--------|-------|
| Status del sistema | Lite | ~2s | $0 |
| Validación completa | Operator | ~30s | $$ |
| Auditoría sin modificar | Inspector | ~10s | $$ |
| Fijar drift | Operator | ~1m | $$ |
| Decisión arquitectónica | Operator+DeepSeek | ~2m | $$$ |
| Deep security audit | Inspector | ~5m | $$$$ |
| Chat simple | Lite | ~5s | $0 |

### Reglas de Precedencia

1. **Inspector primero** (antes de cualquier ejecución)
   ```
   @vx11-inspector detect drift
   ```
   Si crítico → STOP. Si limpio → proceed.

2. **Operator para tareas reales** (validación + ejecución + autosync)
3. **Lite para checks rápidos** (status, cleanup, chat simple)
4. **Operator+DeepSeek para decisiones arquitectónicas** (reasoning pesado)

### Memoria File-Based (Importantísimo)

**NO chat memory.** Estado persiste en archivos git-tracked:

```
docs/audit/AGENT_STATE_CURRENT.md    ← System state map
docs/audit/DRIFT_LATEST.md           ← Latest drift analysis
docs/audit/AGENT_LOG.md              ← Operational log
docs/audit/INSPECTOR_LAST_AUDIT.md   ← Last audit results
```

Cada nueva sesión de chat: leer archivos frescos, validar contra `git status`, reconstruir estado. Esto permite resumir operaciones y multi-user collaboration.

### GitHub Actions Coordination

Agentes coordinan con:
- `.github/workflows/vx11-autosync.yml` — Autosync gated by validation
- `.github/workflows/vx11-validate.yml` — PR/push validation

**Autosync STOP CONDITIONS** (8 critical issues):
- Secretos detectados
- node_modules o dist tracked
- CI workflow roto
- Cross-module imports encontrados
- Tests fallan
- DB schema issues
- Port conflicts
- Fork divergence from main

### Documentación de Agentes

- `docs/VX11_OPERATOR_AGENT_MANUAL.md` — Manual completo (cost, usage, troubleshooting)
- `docs/VX11_OPERATOR_AGENT_EXAMPLES.md` — 7 ejemplos reales

---

## 📞 Contacto / Escalada

Si detectas:
- Token expuesto → crea `docs/audit/STOP_BLOCKER.md`, rota credencial
- Node_modules o dist tracked → limpiar, actualizar `.gitignore`
- Tests reventados → diagnostica, repara, documenta
- Ambigüedad arquitectónica → lee [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) y `.copilot-audit/`

---

**Versión:** 7.1  
**Mantienen:** Copilot + CI + Agentes IA  
**Última actualización:** 2025-12-14 (Fase 0)
