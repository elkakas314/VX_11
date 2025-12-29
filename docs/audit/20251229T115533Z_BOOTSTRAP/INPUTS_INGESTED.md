# VX11 INPUTS INGESTED — LOCAL DOCUMENTS CONSOLIDATION

**Bootstrap Timestamp**: 2025-12-29T11:55:33Z

---

## 📄 Source Files

### 1. **Informe de Auditoría Remoto (A).pdf** (91.8K, 9 pages)
**Location**: `/home/elkakas314/Documentos/Informe de Auditoría Remoto (A).pdf`  
**Format**: PDF v1.7 (A4)  
**Author**: ChatGPT Deep Research  

#### Key Findings
- ✅ **Servicios activos**: Madre (8001), Redis (6379) — policy `solo_madre`
- ✅ **BD**: Intacta, PRAGMA ok, 71 tablas, ~1.15M filas, 2 backups activos + 23 archivados
- ✅ **Switch**: Initially stopped by policy, but manual `docker compose up switch` works correctly
- ✅ **Chat routing**: `/switch/route` responds HTTP 200, events logged to BD
- ✅ **Tentáculo_link**: Operator API `/operator/api/chat` active, rate-limit + size checks working
- ⚠️ **UI Chat bug**: Frontend BASE_URL hardcoded to `http://localhost:8000` → fixed to relative path
- ✅ **Drift check**: Zero drift from canon; FS audit shows no unexpected modules
- ✅ **Policy enforcement**: Deployment gates verified (8/8 PASS)

#### Diagrams Included
1. **Chat Flow**: Browser → Tentáculo → Cache/Rate-limit → Switch (6s) → Fallback LLM (2s)
2. **Fallback Chain**: Switch → LLM local → DeepSeek (optional) → Error response
3. **Post-task/Maintenance**: PRAGMA checks → DB regeneration → Backup rotation
4. **Temporal Windows**: Window open → docker compose up → TTL → docker compose stop
5. **Test Plan**: Smoke tests (API + UI), fallback scenarios, post-task validation, CI pipeline

#### Acceptance Criteria
- All P0 endpoints respond correctly under `solo_madre`
- Rate-limit and payload size enforced
- UI loads without NetworkError
- Fallback to LLM works when Switch unavailable
- Post-task regenerates artifacts without error
- Zero hardcoded secrets

---

### 2. **operatorjson.txt** (809 lines)
**Location**: `/home/elkakas314/Documentos/operatorjson.txt`

#### Operator Superpack Canon v7.0.0
- **Target**: operator_frontend + operator_backend + minimal wiring for E2E
- **Canon sources**: 3 audit PDFs + spec documents

#### Canon Invariants (Embedded)
- Single entrypoint: Frontend → operator_backend → tentaculo_link/madre (no direct internal calls)
- Runtime default: `solo_madre` (full_profile OFF)
- No unsafe UI: No shell execution; only approved runbooks
- DB ownership: Operator tables only (`operator_sessions`, `operator_messages`, `operator_events`, `operator_settings`, `operator_audit_runs_cache`)
- Security minimum: JWT + roles, rate-limit, CSRF, no hardcoded secrets

#### Current State Observed
**Backend (FastAPI v7)**
- ✅ Existing: `/health`, `/operator/chat`, `/operator/session/{id}`, `/operator/vx11/overview`, `/ws`, `/ws/{session_id}`, `/api/chat`, `/api/status`
- ❌ Stubs/gaps: `/api/audit`, `/api/audit/{id}/download`, `/api/module/{name}/restart`, `/api/events`, `/api/settings`
- Routing: Fallback chain (tentaculo_link:8000 → madre:8001 → degraded)
- Response fields: `request_id`, `route_taken`, `degraded`, `errors[]`

**Frontend (React 18 + TypeScript + Tailwind + Zustand)**
- ✅ Functional panels: ChatPanel, StatusBar, LogsPanel, SwitchQueuePanel, HermesPanel, MCPPanel, SpawnerPanel
- ❌ Stubs/basic: PowerManagerPanel, MetricsPanel, AuditPanel, RewardsPanel
- Layout: 3-panel dark theme

---

### 3. **hormiguero_manifetsaator.txt** (3273 lines)
**Location**: `/home/elkakas314/Documentos/hormiguero_manifetsaator.txt`

#### INEE + Builder + Colonia Remota (Dormant Feature Pack)

**Purpose**: Handoff to architect for integrating INEE + Hormiga Builder + Remote Colony as "PAQUETE DORMIDO" (OFF by default)

**Hard Rules (Non-negotiable)**
1. Single entrypoint: All remote traffic via `tentaculo_link` only (NO direct hormiguero exposure)
2. Runtime default: `solo_madre` → INEE/Builder/Rewards must be "dormido" (no tasks, timers, threads, active queues, WS)
3. OFF by default: Flags/env in false; endpoints respond 503/403 "disabled" without state side-effects
4. Additive-only: No breaking changes to existing endpoints/DB/contracts
5. No new top-level Docker services: INEE/Builder/Rewards live as internal modules (preferably in `hormiguero/`)
6. Real execution (adult/execute) requires: Window open by Madre + human approval via Operator
7. Full audit: All events with correlation_id, append-only

**Architecture (Target Location)**
- `hormiguero/inee/`: Core (registry, intents, policies, audit, dedupe, killswitch)
- `hormiguero/builder/`: Hormiga Builder (packaging + evidence; delegates heavy to HIJA)
- `hormiguero/rewards/`: Reward engine + budgets + penalties
- `tentaculo_link/`: API routes `/api/v1/inee/*` (register/heartbeat/submit_intents/windows/status)
- `operator/`: INEE panels (behind flag, non-breaking)

**DB Schema (Additive)**
- `inee_colonies(status, last_seen)` + index
- `inee_agents(colony_id, role)` + index
- `inee_intents(status, created_at)` + index
- `inee_audit_events(correlation_id, created_at)` + index
- `inee_nonces(colony_id, nonce)` UNIQUE
- `reward_accounts(entity_type, entity_id)` UNIQUE
- `reward_events(account_id, created_at)` + index
- Requirement: NO table scans; all queries indexed

**Gating (Dormant Package)**
- `VX11_INEE_ENABLED=false` (default)
- `VX11_INEE_REMOTE_PLANE_ENABLED=false` (default)
- `HORMIGUERO_BUILDER_ENABLED=false` (default)
- `VX11_REWARDS_ENABLED=false` (default)
- `VX11_INEE_WS_ENABLED=false` (default)

**Security Contracts (Minimum)**
- HMAC SHA-256 on canonical JSON (stable order)
- Timestamp window (e.g., 5 min), nonce dedupe, rate-limit per colony/IP
- Killswitch: soft (telemetry only) / hard (block all except health/audit)
- Onboarding: manual registration → "pending" until Operator approval

**Temporal Windows (Madre)**
- Interface: `request_window(type, duration, reason, requested_by)`, `is_window_open(type)`, `close_window(id, reason)`
- Types: `inee_simulate`, `inee_execute`, `builder_active`
- On close: abort or finalize, return to dormido mode

**HIJA (Spawner) — Canonical Use**
- Simulations + heavy validations always in ephemeral sandbox HIJA
- Builder does NOT apply; only packages patch + evidence

**Acceptance**
1. Default mode (`solo_madre`): P0/contracts/health PASS (no degradation)
2. Endpoints return "disabled" consistently when flags=false
3. With window simulate: intents run in HIJA, audit recorded
4. No breaking changes to existing API/DB/contracts

---

### 4. **shubjson.txt** (3612 lines)
**Location**: `/home/elkakas314/Documentos/shubjson.txt`

#### ShubNiggurath 2.1.1-Autopilot Low-Power Mode

**Objective**: Implement ShubNiggurath with strict single entrypoint, solo_madre default, low-power concurrency

**Invariants (VX11-enforced)**
1. Single entrypoint external: `/shub/*` proxy ONLY via tentaculo_link (no direct bypass)
2. Runtime default: Shub OFF; tentaculo responds 503 in <3s if Shub is OFF
3. Ports: Shub HTTP 8007, Spawner HTTP 8008, REAPER OSC UDP 9008, Carla UDP 22752-22762
4. DB: SQL retention with `datetime('now','-30 days')` (NOT `date()`)
5. Dry-run: `plan_only` in submit generates plan without touching REAPER/FS
6. Degraded mode: logs in `shub_degraded_logs` when plugins/kits missing or resource pressure
7. Compat layer: lazy imports + importlib, wake idempotent with state file
8. Low-power: 1 job / 1 track / 1 render concurrent

**Proxy Setup (tentaculo_link)**
- Route: `/shub/{path}` with HMAC validation (dev bypass OFF by default)
- Timeout: 30s normal; rejection/no-route → 503 in ≤3s
- Test script: `tentaculo_link/scripts/validate_shub_proxy.py`

**Acceptance**
- With Shub OFF: `curl /tentaculo_link/shub/health` → 503 in <3s
- With Shub ON: → 200 + envelope correct
- `/jobs/submit/plan` → plan without FS/REAPER side-effects, `degraded_mode_required` if missing plugins
- Events inserted in `shub_job_events`, degradations in `shub_degraded_logs`
- Migrations idempotent: run 2x without break (INSERT OR IGNORE)
- No module breakage; `solo_madre` remains default

---

### 5. **diagrams.txt** (677 lines)
**Location**: `/home/elkakas314/Documentos/diagrams.txt`

#### Power Windows + E2E Test Conductor Design

**Control-Plane Diagram**
- Madre service (tentaculo_link:8000) = single entrypoint
- Power Manager controls ephemeral window services
- Test Conductor schedules + executes test matrix
- Window Lifespan Tracker monitors TTL
- Recovery Handler analyzes logs, generates PATCH_INTENT.md

**Data-Plane & Evidence Flow (Sequence)**
1. Test Conductor → Power Manager: `open_window(service, ttl, hold_flag)`
2. Power Manager → Docker Compose: `docker-compose up service`
3. Service → Metrics Collector: Health check, response, timing
4. Loop: E2E test execution (HTTP/gRPC) → Metrics → Evidence log (timestamp, latency, resource_usage)
5. TTL expired/test complete: Power Manager → Docker Compose: `docker-compose stop service`
6. Test Conductor → Power Manager: `ensure_solo_madre()`

**Test Orchestration**
- Test Queue + Matrix Executor
- Metrics Collector
- Evidence Log (`/var/log/vx11/e2e/`)
- Recovery Handler generates recovery patches

---

## 📊 Ingestion Summary

| Input | Lines | Key Scope | Status |
|-------|-------|-----------|--------|
| Audit PDF | — | System health, gates, diagrams, test plan | ✅ Incorporated |
| operatorjson.txt | 809 | Operator canon, gaps, contracts | ✅ Incorporated |
| hormiguero_manifetsaator.txt | 3273 | INEE/Builder/Rewards dormant pack, rules | ✅ Incorporated |
| shubjson.txt | 3612 | ShubNiggurath low-power, proxy setup | ✅ Incorporated |
| diagrams.txt | 677 | Power windows, test conductor, E2E flows | ✅ Incorporated |
| **TOTAL** | ~8,371 | VX11 full system + dormant features | **✅ COMPLETE** |

---

## 🔄 Action Items Derived

### Immediate (P0)
- [ ] Debug and fix vx11-switch crash (exitcode 1)
- [ ] Implement 5 missing Operator endpoints: `/api/audit`, `/api/audit/{id}/download`, `/api/module/{name}/restart`, `/api/events`, `/api/settings`

### Short-term (P1)
- [ ] INEE/Builder/Rewards: Create module structure (dormant, all flags OFF)
- [ ] ShubNiggurath: Set up proxy validation + low-power concurrency
- [ ] E2E test conductor: Power windows + metrics + recovery handler

### Medium-term (P2)
- [ ] Activate feature packs via controlled windows (Madre approval)
- [ ] Implement full audit trails (correlation_id throughout)
- [ ] Deploy test matrix (smoke + fallback + post-task)

---

**✅ Bootstrap COMPLETE** — All local documents ingested, decoded, and mapped to VX11 architecture.

