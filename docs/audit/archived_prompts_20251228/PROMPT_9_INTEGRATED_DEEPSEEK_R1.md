# PROMPT 9 + VISOR SPEC — INTEGRATED FOR DEEPSEEK R1

---

## FASE 0: RECEPCIÓN DE SPEC ✅

El usuario ha proporcionado el spec completo del Operator VX11 en JSON:

**Archivo Base**: `docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json`

**Características**:
- Completo (frontend_spec + backend_spec + API surface)
- Invariantes claras (single_entrypoint, solo_madre, no_unsafe_ui, db_ownership, security_minimum)
- Feature sets detallados (overview, topology, hormiguero, jobs, audit, explorer, settings)
- Phase plan (P0, P1, P2)
- Acceptance criteria (must/should)

---

## MATRIZ DE REQUISITOS — PARSER AUTOMÁTICO

Extraído del JSON spec, clasificado por prioridad:

### FRONTEND FEATURES (P0 — PRODUCTION-MINIMUM)

| ID  | Feature | Componente | Endpoint(s) | Prioridad | Estado | Notas |
|-----|---------|-----------|-------------|-----------|--------|-------|
| F1  | Overview Dashboard | `DashboardView.tsx` | `/api/status`, `/api/modules`, `/api/scorecard`, `/api/audit?limit=10` | P0 | TODO | 4 widgets: module_cards, alerts_strip, score_radar, recent_runs |
| F2  | Chat Panel (P0) | `ChatPanel.tsx` | `/api/chat`, `/api/sessions`, `/api/events` | P0 | PARTIAL | Message states (draft/sending/delivered/routed/degraded/failed); markdown; copy code; session management |
| F3  | Status Bar | `StatusBar.tsx` | `/api/status` | P0 | TODO | Global status chip (mode + alerts) |
| F4  | Left Rail Navigation | `LeftRail.tsx` | `/api/sessions`, `/api/modules` | P0 | TODO | Sessions list, module quick list, search |
| F5  | Right Drawer Context | `RightDrawer.tsx` | `/api/status` | P0 | TODO | Mode indicator, active modules, daughters list, recent events, alerts, quick_actions |
| F6  | Module Detail Drawer | `ModuleDetailDrawer.tsx` | `/api/modules/{name}` | P0 | TODO | Endpoints list, logs tail, health status |
| F7  | Audit Center | `AuditView.tsx` | `/api/audit`, `/api/audit/{id}`, `/api/audit/{id}/download` | P0 | TODO | Run list, run detail, download artifacts; no patch apply (P1+) |
| F8  | Settings Panel | `SettingsView.tsx` | `/api/settings` | P0 | TODO | Appearance, events, chat, security, developer settings |
| F9  | Degraded Mode UI | `DegradedModeBanner.tsx` + state logic | `/api/status` (degraded field) | P0 | TODO | Persistent banner when route_taken = degraded; resend pending UI |
| F10 | Accessibility + Keyboard Nav | global | N/A | P0 | TODO | Ctrl+Enter send, Ctrl+K palette, Alt+1/2/3 panel jump, Esc close |
| F11 | Error Boundaries + Empty States | global | N/A | P0 | TODO | No blank screens; show "OFF by policy" for disabled modules |

### FRONTEND FEATURES (P1 — ADVANCED)

| ID  | Feature | Componente | Endpoint(s) | Prioridad | Estado | Notas |
|-----|---------|-----------|-------------|-----------|--------|-------|
| F12 | Topology View (Interactive) | `TopologyView.tsx` | `/api/topology`, `/api/status` | P1 | TODO | React Flow (preferred) or SVG; nodes + edges; click -> detail drawer; hover -> latency |
| F13 | Hormiguero Visualization | `HormigueroView.tsx` | `/api/hormiguero/status`, `/api/hormiguero/pheromones`, `/api/spawner/daughters` | P1 | TODO | Queen/daughters/pheromones; colony_status + heatmap + daughter_fleet + scan_control |
| F14 | Jobs Board (Unified) | `JobsView.tsx` | `/api/jobs`, `/api/job/{id}` | P1 | TODO | Table + kanban views; filters; live updates (SSE/WS) |
| F15 | Explorer (Read-only) | `ExplorerView.tsx` | `/api/explorer/fs/tree`, `/api/explorer/fs/file`, `/api/explorer/db/tables`, `/api/explorer/db/query_preset` | P1 | TODO | FS browser + DB preset query tool (no raw SQL); whitelist-only |
| F16 | SSE/WS Realtime | global | `/api/events/stream` (SSE) or `/ws` (WS) | P1 | TODO | Auto-reconnect, heartbeat, backoff jitter, offline banner integration |
| F17 | Command Palette | global | `/api/status`, `/api/modules`, etc | P1 | TODO | Ctrl+K; commands: /status /audit /window /spawn /restart (role-gated) |

### FRONTEND FEATURES (P2 — FUTURE)

| ID  | Feature | Componente | Endpoint(s) | Prioridad | Estado | Notas |
|-----|---------|-----------|-------------|-----------|--------|-------|
| F18 | Runbooks + Safe Actions | `RunbooksPanel.tsx` | (new endpoint) `/api/runbooks`, `/api/runbooks/{id}/execute` | P2 | TODO | Pre-approved actions only; confirm + audit trail |
| F19 | File Dropzone + Analysis | `FileDropzone.tsx` | (new endpoint) `/api/artifacts/upload` | P2 | TODO | Zip/txt/json/md/log only; madre decides analysis |
| F20 | Timeline Playback | `TimelinePlayback.tsx` | (new endpoint) `/api/timeline/{correlation_id}` | P2 | TODO | Replay events per correlation_id |

---

### BACKEND API ENDPOINTS (P0)

| ID  | Method | Path | Status | Endpoint | Auth | Body/Params | Returns | Notas |
|-----|--------|------|--------|----------|------|------------|---------|-------|
| A1  | GET | `/api/status` | MUST | ✓ | token | - | mode + modules[] + alerts + scorecard | Global status summary |
| A2  | GET | `/api/modules` | MUST | ✓ | token | - | modules[] | Module list (same shape as A1) |
| A3  | GET | `/api/modules/{name}` | MUST | - | token | - | module + logs_tail + endpoints | Module detail |
| A4  | POST | `/api/chat` | MUST | PARTIAL | token | session_id, message, attachments, client_context | request_id + route_taken + degraded + intent + reply + structured | Chat (proxied or degraded) |
| A5  | GET | `/api/events` | MUST | - | token | - | events[] | Polling feed (SSE stream at `/api/events/stream`) |
| A6  | POST | `/api/audit` | MUST | - | token | scope, include_fs_drift, include_db_map | audit_id + status + request_id | Trigger manual audit |
| A7  | GET | `/api/audit` | MUST | - | token | - | runs[] | List audit runs |
| A8  | GET | `/api/audit/{id}` | MUST | - | token | - | audit_id + findings + artifacts | Audit detail |
| A9  | GET | `/api/audit/{id}/download` | MUST | - | token | - | binary ZIP | Download artifacts |
| A10 | POST | `/api/module/{name}/restart` | MUST | STUB | admin | reason, window_ttl_s | request_id + status + detail | Restart via madre power_manager |
| A11 | GET | `/api/settings` | MUST | - | token | - | settings | Get UI + behavior settings |
| A12 | POST | `/api/settings` | MUST | - | token | settings | ok | Update settings |
| A13 | GET | `/api/topology` | MUST | - | token | - | nodes[] + edges[] + mode | Topology graph |

### BACKEND API ENDPOINTS (P1)

| ID  | Method | Path | Status | Endpoint | Auth | Body/Params | Returns | Notas |
|-----|--------|------|--------|----------|------|------------|---------|-------|
| A14 | POST | `/api/module/{name}/power` | P1 | - | admin | action (up/down), ttl_s, reason | request_id + status + detail | Time-boxed power up/down |
| A15 | GET | `/api/hormiguero/status` | P1 | - | token | - | queen + active_daughters + recent_pheromones + progress | Hormiguero status |
| A16 | POST | `/api/hormiguero/scan` | P1 | - | operator | scope (full/path/incremental), path | request_id + scan_id + status | On-demand scan |
| A17 | GET | `/api/jobs` | P1 | - | token | - | jobs[] | Unified jobs list |
| A18 | GET | `/api/job/{id}` | P1 | - | token | - | job_id + status + logs_tail + artifacts | Job detail |
| A19 | GET | `/api/events/stream` | P1 | - | token | - | SSE stream | Live events (SSE) |
| A20 | WebSocket | `/ws` | P1 | - | token | - | bidirectional | Chat streaming (optional) |

### BACKEND API ENDPOINTS (P2)

| ID  | Method | Path | Status | Endpoint | Auth | Body/Params | Returns | Notas |
|-----|--------|------|--------|----------|------|------------|---------|-------|
| A21 | GET | `/api/runbooks` | P2 | - | token | - | runbooks[] | List pre-approved safe actions |
| A22 | POST | `/api/runbooks/{id}/execute` | P2 | - | admin | params (runbook-specific) | result + audit_id | Execute (confirmed + audited) |
| A23 | POST | `/api/artifacts/upload` | P2 | - | operator | file (multipart) | artifact_id | Upload for analysis |
| A24 | GET | `/api/timeline/{correlation_id}` | P2 | - | token | - | events[] (timeline) | Replay events |

---

### SECURITY + AUTH (P0)

| ID  | Task | Component | Status | Notas |
|-----|------|-----------|--------|-------|
| S1  | Token Guard (middleware) | `tentaculo_link/main_v7.py` + `operator_backend` | EXIST | x-vx11-token header required on all `/api/*` |
| S2  | JWT + Roles (login flow) | `operator_backend/auth.py` (new) | TODO | POST /auth/login; roles: admin/operator/readonly |
| S3  | Rate Limit | `operator_backend` | TODO | 20/min chat, 5/min module actions |
| S4  | CSRF (if cookie auth) | `operator_backend` | TODO | Double-submit token strategy |
| S5  | Audit Trail (mutation log) | DB + logs | TODO | Every mutation logs: request_id, user, role, action, target, timestamp |
| S6  | Secrets in env only | `.env` files | OK | No tokens in git |

---

## DEPENDENCIAS ADICIONALES (si aplica)

### Librerías Nuevas (Permitidas P0)
- **React Flow** (opcional P1, para topology): ~30KB gzipped
- **Recharts** (opcional P1, para score radar): ~40KB gzipped
- **react-virtual** (si chat/logs > 500 items): ~10KB gzipped

**REGLA**: Ninguna nueva sin justificación en PLAN.md

## POLÍTICA DE EJECUCIÓN (OBLIGATORIA) — SIN ESTIMACIONES DE HORAS

```
- Prohibido dar estimaciones tipo "X horas".
- Trabajar por TAREAS ATÓMICAS con COMMITS atómicos.
- Timebox por tarea: 60–90 minutos.
  - Si no se completa en el timebox: PARAR y entregar:
    1) qué falta,
    2) cuál es el bloqueo real,
    3) siguiente comando/cambio exacto para continuar.
- P0 primero. P1/P2 solo si P0 pasa todos los gates.
- Cada tarea termina con evidencia en docs/audit/<TIMESTAMP>_...
```

---

## FASE 1: BOOTSTRAP OBLIGATORIO (Copilot/DeepSeek debe ejecutar primero)

**LEER EN ORDEN**:
1. `docs/audit/CLEANUP_EXCLUDES_CORE.txt`
2. `docs/audit/DB_SCHEMA_v7_FINAL.json`
3. `docs/audit/DB_MAP_v7_FINAL.md`
4. `docs/audit/PERCENTAGES.json`
5. `docs/audit/SCORECARD.json`
6. `docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json` ← **THIS**
7. `docker-compose.yml`
8. `tentaculo_link/main_v7.py` (lines 1-220 + /operator/api router)
9. `operator/frontend/vite.config.ts`, `package.json`, `tsconfig.json`
10. `operator/frontend/src/services/api.ts`

**EJECUTAR SNAPSHOT**:
```bash
git status --porcelain=v1
git log --oneline -5
docker compose ps
curl -s http://localhost:8000/health | jq .
curl -s -H "x-vx11-token: vx11-local-token" http://localhost:8000/operator/status | jq .
curl -s -H "x-vx11-token: vx11-local-token" http://localhost:8000/operator/api/status | jq .
```

**GUARDAR EN**: `docs/audit/<TIMESTAMP>_OPERATOR_P9_BASELINE/`

---

## FASE 2: TRABAJO (4 TAREAS ATÓMICAS)

### TAREA 1 — Auditoría + Plan Ejecutable (SIN CAMBIOS)

**Entregable**: `docs/audit/<TIMESTAMP>_OPERATOR_P9_PLAN.md`

**Contenido**:
- Resumen de requisitos (usar matriz arriba)
- Riesgos identificados + mitigación
- Archivos a tocar + líneas aprox.
- Endpoints nuevos (comparar spec vs actual)
- Timeline estimada
- Criterios P0 para esta tarea

**Referencia**: use la matriz de requisitos de arriba para listar qué está DONE vs TODO

---

### TAREA 2 — Pulido Visual + UX (Frontend)

**Objetivo**: UI "acabada", oscura, usable, sin glitch.

**Requisitos Mínimos P0**:

1. **Layout Sólido** (conforme a spec)
   - Navigation: 8 primary nav tabs (overview, chat, topology, hormiguero, jobs, audit, explorer, settings) ← DE SPEC
   - Left rail: sessions list, module quick list, search
   - Right drawer: mode indicator, active modules, daughters list, recent events, alerts, quick_actions
   - Responsive (no rompe en móvil ni desktop)

2. **Estados** (CRÍTICO)
   - Loading: skeleton screens / spinners (message_states: draft/sending/delivered/routed)
   - Error boundaries: mensajes claros
   - Empty states: "⊘ [Module] is OFF by policy (solo_madre mode)" ← DE SPEC
   - Success: confirmación visual

3. **Chat Panel** (si está en P0 requisitos)
   - Scroll automático a último mensaje
   - Markdown: `**bold**`, `_italic_`, `` `code` ``
   - Copy button en bloques código
   - Session management: rename, tag, search, clear
   - Degraded indicator: "route_taken: madre", etc.

4. **Status/Scorecard/Alerts**
   - Colores estándar (spec): ok=#22C55E, warn=#F59E0B, crit=#EF4444, info=#38BDF8
   - Badges: "solo_madre" (blue), "OFF_BY_POLICY" (grey), "OK" (green)
   - No blank screens si un servicio está OFF

5. **Dark Theme**
   - Usar tokens de spec:
     ```
     bg_0: #070A12, bg_1: #0B1020, panel: #0F172A, panel_2: #111B33
     border: rgba(148,163,184,0.15)
     text: #E5E7EB, muted: #94A3B8
     accent_primary: #7C3AED, accent_secondary: #06B6D4
     ```

6. **TypeScript Red Squiggles**
   - `tsconfig.json`: `"types": ["node", "vitest/globals"]`
   - `vite.config.ts`: `globals: true`
   - No imports raros

**Archivos a crear/modificar**:
- `operator/frontend/src/views/OverviewView.tsx` (P0)
- `operator/frontend/src/views/ChatView.tsx` (P0)
- `operator/frontend/src/views/TopologyView.tsx` (P1, stub OK)
- `operator/frontend/src/views/HormigueroView.tsx` (P1, stub OK)
- `operator/frontend/src/views/JobsView.tsx` (P1, stub OK)
- `operator/frontend/src/views/AuditView.tsx` (P0)
- `operator/frontend/src/views/ExplorerView.tsx` (P1, stub OK)
- `operator/frontend/src/views/SettingsView.tsx` (P0)
- `operator/frontend/src/components/LeftRail.tsx` (P0)
- `operator/frontend/src/components/RightDrawer.tsx` (P0)
- `operator/frontend/src/components/DegradedModeBanner.tsx` (P0)
- `operator/frontend/src/App.tsx` (refactor: nav + main container + right drawer)
- `operator/frontend/src/App.css` (theme tokens + layout)

---

### TAREA 3 — Integración Funcional (API ↔ UI) + Visor

**Backend Adjustments** (`tentaculo_link/main_v7.py`):
- Asegurar que `/operator/api/*` endpoints devuelven shapes estables (spec)
- Si hay endpoint faltante para un feature P0 del visor:
  - Agregarlo (pero responder 200 + shape estable)
  - OFF_BY_POLICY modules: devolver `{status:"off_by_policy", reason:"solo_madre"}` (NO 500)
- Check: `/api/status`, `/api/modules`, `/api/chat`, `/api/audit`, `/api/settings`, `/api/topology`

**Frontend API Layer** (`operator/frontend/src/services/api.ts`):
- Métodos por endpoint (ver matriz):
  - `status()` → GET /operator/api/status
  - `modules()` → GET /operator/api/modules
  - `moduleDetail(name)` → GET /operator/api/modules/{name}
  - `chat(message, sessionId)` → POST /operator/api/chat
  - `events()` → GET /operator/api/events (polling)
  - `audit()` → GET /operator/api/audit
  - `auditDetail(id)` → GET /operator/api/audit/{id}
  - `downloadAudit(id)` → GET /operator/api/audit/{id}/download
  - `settings()` → GET /operator/api/settings
  - `updateSettings(obj)` → POST /operator/api/settings
  - `topology()` → GET /operator/api/topology
  - `hormigueroStatus()` → GET /operator/api/hormiguero/status (P1)
  - `scan(scope)` → POST /operator/api/hormiguero/scan (P1)
  - `jobs()` → GET /operator/api/jobs (P1)
  - `jobDetail(id)` → GET /operator/api/job/{id} (P1)

**Componentes + Datos Reales**:
- Cada panel muestra datos reales o "OFF_BY_POLICY" (nunca stubs)
- Fallback a degraded si endpoint devuelve degraded=true

---

### TAREA 4 — Verificación P0 + Evidencia + Commits

**CRITERIOS P0** (DEBE PASAR TODO):

#### Frontend
```bash
npm ci
npm run build
# Output: ✓ built in X.XXs (no warnings, no errors)

npm test 2>/dev/null || echo "No tests"
# Si hay: PASS
```

#### Backend
```bash
python3 -m py_compile tentaculo_link/main_v7.py
# Output: [silent] = OK
```

#### Runtime (solo_madre policy)
```bash
# Services
docker compose ps
# Esperado: madre, redis, tentaculo_link UP; switch/hermes/etc DOWN

# Static UI
curl -s http://localhost:8000/operator/ui/ | grep -q "<title>"
# [exit 0] = OK

# Assets
curl -sI http://localhost:8000/operator/ui/assets/index-*.css | grep -q "200"
curl -sI http://localhost:8000/operator/ui/assets/index-*.js | grep -q "200"

# API endpoints (all with token)
curl -s -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/status | jq ".policy" | grep -q "solo_madre"

curl -s -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/modules | jq ".modules[0]" | grep -q "status"

curl -s -X POST -H "x-vx11-token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}' \
  http://localhost:8000/operator/api/chat | jq ".route_taken"

# TS check
npx tsc --noEmit
# [silent] = OK
```

**EVIDENCIA** en `docs/audit/<TIMESTAMP>_OPERATOR_P9_EVIDENCE/`:
- `frontend_build.txt`
- `backend_syntax.txt`
- `runtime_checks.txt` (todos los curl)
- `ts_check.txt`
- `api_responses.json` (samples)

**COMMITS** (atómicos):

```bash
# Commit A
git add docs/audit/<ts>_OPERATOR_P9_*/
git commit -m "vx11: Operator P9 — baseline audit + plan + visor requirements matrix"

# Commit B
git add operator/frontend/src/views/* operator/frontend/src/components/LeftRail.tsx operator/frontend/src/components/RightDrawer.tsx operator/frontend/src/App.tsx operator/frontend/src/App.css
git commit -m "vx11: Operator P9 — frontend polish + layout + visor navigation"

# Commit C
git add tentaculo_link/main_v7.py operator/frontend/src/services/api.ts
git commit -m "vx11: Operator P9 — API endpoints + frontend integration"

# Commit D
git add docs/audit/<ts>_OPERATOR_P9_EVIDENCE/
git commit -m "vx11: Operator P9 — verification + evidence + summary"

git push vx_11_remote main
```

## FASE 2B: TIMEBOX + BLOQUEOS

**Regla crítica**: Si una tarea no termina en 60–90 minutos:
1. NO continuar "un poquito más"
2. PARAR limpiamente (git stash o commit WIP si aplica)
3. Entregar BLOQUEO en docs/audit/<TIMESTAMP>_BLOCKED/:
   ```
   Tarea: [nombre]
   Tiempo usado: [minutos]
   Falta: [qué específicamente]
   Bloqueo: [impedimento concreto]
   Siguiente paso: [comando o acción exacta]
   ```
4. Retomar en sesión siguiente

---

## FASE 3: SALIDA FINAL (QUÉ ENTREGAR)

### 1️⃣ Resumen Ejecutivo (~1 página)

```
Título: "Operator P9 — Pulido Visual + Visor Integrado"

Qué cambió:
- Frontend: 8-tab nav, left rail, right drawer, degraded banner, responsive layout
- Backend: API endpoints verified (spec-aligned), OFF_BY_POLICY handling
- UX: Accessibility (Ctrl+Enter, Ctrl+K), dark theme, error boundaries

Qué se añadió:
- Componentes: OverviewView, AuditView, SettingsView, LeftRail, RightDrawer, DegradedModeBanner
- Estilos: Theme tokens (spec colors), layout grid, responsive breakpoints
- Integración: api.ts methods (12+ endpoints mapeados)

Qué se degradó:
- Nada (P0 solo lectura + degraded mode)

Qué queda P1/P2:
- Topology interactive (React Flow)
- Hormiguero viz (queen/daughters/pheromones)
- Jobs board (kanban)
- SSE/WS live events
- Safe runbooks
- File dropzone analysis

Estado: READY FOR PRODUCTION (P0 gates ✓)
```

### 2️⃣ Matriz de Requisitos (del Visor Spec)

```markdown
| ID  | Feature | Prioridad | Status DONE/TODO | Componente | Notas |
| F1  | Overview | P0 | DONE | DashboardView | 4 widgets real |
| F2  | Chat | P0 | DONE | ChatView | markdown + copy code |
| F3  | Audit | P0 | DONE | AuditView | list + detail + download |
| ... | ... | ... | ... | ... | ... |
| F12 | Topology | P1 | TODO | TopologyView | React Flow (next) |
| F13 | Hormiguero | P1 | TODO | HormigueroView | Queen viz (next) |
```

### 3️⃣ Rutas + Endpoints Finales

```markdown
## UI Routes
- GET  /operator/ui/           → VX11 Operator (static)
- GET  /operator/ui/assets/    → CSS, JS

## API Endpoints (all require x-vx11-token)
- GET  /operator/api/status       → spec-aligned ✓
- GET  /operator/api/modules      → spec-aligned ✓
- GET  /operator/api/modules/{name}
- POST /operator/api/chat         → degraded if switch OFF ✓
- GET  /operator/api/events       → polling (SSE P1)
- POST /operator/api/audit        → trigger scan
- GET  /operator/api/audit        → list runs ✓
- GET  /operator/api/audit/{id}   → detail ✓
- GET  /operator/api/audit/{id}/download → ZIP ✓
- GET  /operator/api/settings     → UI settings ✓
- POST /operator/api/settings     → save settings ✓
- GET  /operator/api/topology     → graph ✓
- GET  /operator/api/hormiguero/status  (P1)
- POST /operator/api/hormiguero/scan    (P1)
- GET  /operator/api/jobs               (P1)
- GET  /operator/api/job/{id}           (P1)
```

### 4️⃣ Commits + Hashes

```
[PREV] bc1e03f — vx11: Operator P0 close — API in tentaculo_link + UI stable
[NEW]  <hash1>  — vx11: Operator P9 — baseline audit + plan + visor requirements matrix
[NEW]  <hash2>  — vx11: Operator P9 — frontend polish + layout + visor navigation
[NEW]  <hash3>  — vx11: Operator P9 — API endpoints + frontend integration
[NEW]  <hash4>  — vx11: Operator P9 — verification + evidence + summary
```

### 5️⃣ Archivos Clave Modificados

```
tentaculo_link/main_v7.py
  - Lines: <endpoints verified>

operator/frontend/src/views/
  - OverviewView.tsx (new)
  - ChatView.tsx (new)
  - AuditView.tsx (new)
  - SettingsView.tsx (new)
  - [TopologyView.tsx → P1]
  - [HormigueroView.tsx → P1]
  - [JobsView.tsx → P1]
  - [ExplorerView.tsx → P1]

operator/frontend/src/components/
  - LeftRail.tsx (new)
  - RightDrawer.tsx (new)
  - DegradedModeBanner.tsx (new)

operator/frontend/src/
  - App.tsx (refactored layout)
  - App.css (theme tokens)
  - services/api.ts (12+ methods)

docs/canon/
  - VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json (reference)

docs/audit/
  - <ts>_OPERATOR_P9_BASELINE/
  - <ts>_OPERATOR_P9_PLAN.md
  - <ts>_OPERATOR_P9_EVIDENCE/
```

---

## REGLAS FINALES

✅ **HARDFACTS**:
- Single entrypoint: SOLO `/operator/api/*` desde frontend
- Invariantes: solo_madre default, OFF_BY_POLICY visible, no operator_backend
- P0 gates: npm build ✓, python compile ✓, curl endpoints ✓, npx tsc --noEmit ✓
- Evidencia: TODO en docs/audit/<ts>_*/ (nada sin audit trail)
- Commits: 4 atómicos, pushed a vx_11_remote/main

❌ **NO HACER**:
- Agregar librerías sin plan
- Secrets en git
- Stubs sin justificación
- Direct calls a puertos internos desde frontend
- rm -rf "creativo" fuera de allowlist

---

## INICIO DEL TRABAJO

1. **Lee bootstrap** ✓ (10 archivos)
2. **Ejecuta snapshot** → guardar en BASELINE/
3. **TAREA 1**: Auditoría + Plan (0 cambios de código, timebox 60-90 min)
4. **TAREA 2**: Frontend polish (timebox 60-90 min)
5. **TAREA 3**: API integration (timebox 60-90 min)
6. **TAREA 4**: P0 gates + commits (timebox 60-90 min)
7. **Entregar**: Resumen + commits + evidencia (por tarea)

**Duración**: variable. Se mide por tareas completadas, commits limpios, gates pasados; no por horas.

---

**FIN DEL PROMPT 9 INTEGRADO**
