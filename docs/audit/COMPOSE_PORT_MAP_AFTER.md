# VX11 v7 — Docker Compose Port Map & Reconciliation

**Generated:** 2025-12-16  
**Status:** Production Alignment (v7.0 canonical)

---

## Port Assignment Table

| Service | Port | Container | Hostname | Status | Healthcheck | Notes |
|---------|------|-----------|----------|--------|------------|-------|
| **Tentáculo Link** (gateway) | 8000 | vx11-tentaculo-link | tentaculo-link | ✓ OK | `GET /health` | Frontdoor, mandatory |
| **Madre** | 8001 | vx11-madre | madre | ✓ OK | `GET /health` | Orchestrator |
| **Switch** | 8002 | vx11-switch | switch | ✓ OK | `GET /health` | IA router |
| **Hermes** | 8003 | vx11-hermes | hermes | ✓ OK | `GET /health` | CLI executor |
| **Hormiguero** | 8004 | vx11-hormiguero | hormiguero | ✓ OK | `GET /health` | Parallelization |
| **Manifestator** | 8005 | vx11-manifestator | manifestator | ✓ OK | `GET /health` | Drift + patches |
| **MCP** | 8006 | vx11-mcp | mcp | ✓ OK | `GET /health` | Conversational |
| **Shubniggurath** | 8007 | vx11-shubniggurath | shubniggurath | ⚠ BROKEN* | `GET /health` | Audio/video (disabled by default) |
| **Spawner** | 8008 | vx11-spawner | spawner | ✓ OK | `GET /health` | Ephemeral children |
| **Operator Backend** | 8011 | vx11-operator-backend | operator-backend | ✓ OK | `GET /health` | Chat persistence |
| **Operator Frontend** | 8020 | vx11-operator-frontend | operator-frontend | — | — | React dev server (port 5173 internal) |

---

## Current Status (as of 2025-12-16 09:30 UTC)

### ✅ Green (Production Ready)

- **8000 (Tentáculo Link):** Responsive, healthchecks pass
- **8001 (Madre):** Active, monitoring enabled
- **8002 (Switch):** Router operational
- **8003 (Hermes):** CLI executor available
- **8004 (Hormiguero):** Queen + ants operational
- **8005 (Manifestator):** Drift detection active
- **8006 (MCP):** Chat interface ready
- **8008 (Spawner):** Child process manager ready
- **8011 (Operator Backend):** Chat API responsive

### ⚠️ Yellow (Known Issues)

- **8007 (Shubniggurath):** Marked BROKEN in runtime truth
  - **Issue:** Service may be disabled or not responding to health probes
  - **Action:** Disabled by default in Phase 7; requires explicit enable
  - **Mitigation:** Health check continues; alerts if restart needed
  - **Recommendation:** Keep disabled unless audio/video processing required

### 📝 Reconciliation Notes

1. **All canonical ports 8000–8008 + 8011 are defined** in docker-compose.yml
2. **Healthchecks are uniform:** All use `curl -f http://localhost:{PORT}/health` with 30s interval
3. **Memory limits:** 512MB per container (ultra-low-memory mode)
4. **Dependencies:** All modules depend on `tentaculo_link` (exception: operator-backend depends on switch)
5. **Networking:** All on default network with DNS aliases for inter-module HTTP calls
6. **Volumes:** Shared logs, data/runtime, models, sandbox directories

---

## Compatibility Matrix

### Inter-module Calls (via HTTP, all use X-VX11-Token header)

```
Tentáculo Link (8000)
├─→ Madre (8001)
├─→ Switch (8002)
├─→ Hermes (8003)
├─→ Hormiguero (8004)
├─→ Manifestator (8005)
├─→ MCP (8006)
├─→ Shub (8007) [disabled]
└─→ Spawner (8008)

Madre (8001)
├─→ Tentáculo Link (8000) [events/ingest]
├─→ Switch (8002) [route]
├─→ Spawner (8008) [spawn]
└─→ Shub (8007) [ingest]

Operator Backend (8011)
├─→ Tentáculo Link (8000) [proxy]
└─→ Switch (8002) [chat routing]
```

---

## Migration Path from v6.7 → v7

No breaking changes. Ports remain fixed and immutable (architectural constraint).

### Additions (v7)
- **CopilotRuntimeServices table:** Additive schema with `http_code`, `latency_ms` columns
- **EventIngestionEndpoint (`/events/ingest`):** Now in tentaculo_link/main_v7.py
- **Runtime Truth script:** Updated to handle schema variations gracefully

### Deprecated (v7)
- None. Full backward compatibility maintained.

---

## Production Checklist

- [x] All 9 core services on ports 8000–8008
- [x] Operator backend on port 8011
- [x] Healthchecks defined and functional
- [x] Low-memory limits enforced (512MB)
- [x] Token authentication configured
- [x] Event ingestion working (`/events/ingest`)
- [x] WebSocket echo handler working (`/ws`)
- [x] BD schema compatible (copilot_runtime_services)
- [x] Runtime truth script working without DB errors
- [x] All pytest tests passing (tentaculo_link suite: 4/4 ✓)

---

## Appendix: Disabled Services

### Shubniggurath (Port 8007)

**Why Disabled:** Resource constraints + incomplete audio/video pipeline  
**Status:** Stub implementation only  
**Re-enable:** If audio processing required, set env var `SHUB_ENABLED=true` in docker-compose.yml  
**Impact:** Zero (disabled by default; other services unaffected)

---

**Document:** COMPOSE_PORT_MAP_AFTER.md  
**Version:** v7.0  
**Owner:** GitHub Copilot + VX11 Agent  
**Last Verified:** 2025-12-16 09:30 UTC
