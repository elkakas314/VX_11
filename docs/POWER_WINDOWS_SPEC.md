# VX11 Power Windows Specification (Phase 2)

**Date**: 2025-12-28  
**Status**: SPECIFICATION (Phase 2 - Real Execution)  
**Based on**: FASE 0 Audit + Existing Madre Capabilities  

---

## Executive Summary

VX11 already has docker compose execution via `/madre/power/service/{name}/start|stop` endpoints. This specification upgrades the system to provide:

1. **Named Power Windows** (TTL + Hold modes)
2. **E2E Conductor** (real flow validation)
3. **Optional CORE Mode** (tentaculo_link always-on)
4. **INEE + Manifestator** (intent-driven, flags OFF by default)

---

## 1. Service Allowlist

**Allowed services** for window control:

```
tentaculo_link       # Front-door (optional CORE mode)
switch               # Router
hermes               # Audio
spawner              # Daughter process manager
hormiguero           # CPU Guardian (INEE namespaced)
operator-backend     # UI Backend
operator-frontend    # UI Frontend
manifestator         # Builder (emit-intent only)
shubniggurath        # Shoggoth
mcp                  # Model Context Protocol
```

**Always-on** (SOLO_MADRE):
```
madre                # Orchestrator
redis                # Cache/Session
```

---

## 2. Power Windows API

### Existing (Already Implemented)

```
GET /madre/power/status
GET /madre/power/policy/solo_madre/status
POST /madre/power/policy/solo_madre/apply

POST /madre/power/service/{name}/start
POST /madre/power/service/{name}/stop
POST /madre/power/service/{name}/restart
```

### New (To Implement - Phase 2)

```
POST /madre/power/windows/open
  Request: {
    "services": ["switch", "hermes", "spawner"],
    "ttl_sec": 300,           # 0 = no TTL (hold forever)
    "hold": false,            # true = manual close only
    "reason": "e2e_test",     # audit logging
    "skip_health": false      # skip health checks (for testing)
  }
  Response: {
    "window_id": "uuid",
    "state": "open",
    "services": [...],
    "deadline": "ISO8601 or null",
    "ttl_remaining_sec": int
  }

POST /madre/power/windows/close
  Request: { "window_id": "uuid" (optional, uses active) }
  Response: { "window_id": "uuid", "state": "closed", "services": [...] }

POST /madre/power/windows/hold
  Request: { "window_id": "uuid", "hold": true|false }
  Response: { "window_id": "uuid", "hold": true|false }

GET /madre/power/windows/status
  Response: {
    "active_window": { ... },
    "history": [ ... ],
    "policy": "solo_madre" | "windowed"
  }
```

### Proxy (Optional - Tentaculo Front-Door)

```
POST /power/windows/open       → POST /madre/power/windows/open
POST /power/windows/close      → POST /madre/power/windows/close
POST /power/windows/hold       → POST /madre/power/windows/hold
GET  /power/windows/status     → GET /madre/power/windows/status
```

---

## 3. Control Rules

### Authentication
- **Header**: `X-VX11-Token: <token>`
- **Source**: Environment variables (VX11_TENTACULO_LINK_TOKEN, VX11_GATEWAY_TOKEN, etc.)
- **Fallback**: Internal token guard (see madre/routes_power.py)

### Behavior
- **Single-entrypoint**: All control via tentaculo_link:8000 (when proxy enabled)
- **Default state**: SOLO_MADRE (madre + redis)
- **Concurrent windows**: 1 active at a time (queueing not supported yet)
- **TTL enforcement**: Background task checks every 1 second, auto-closes expired windows
- **Hold mode**: When enabled, window stays open until explicit close or timeout reaches 0

### Retries & Backoff
```
docker compose start/stop:
  - timeout: 30 seconds
  - retries: 1 (on timeout, log and fail)
  - backoff: exponential 1s → 5s
```

### Audit & Logging
- **All operations logged** to forensic/madre/ + sqlite3 copilot_actions_log
- **Evidence dir**: docs/audit/<TIMESTAMP>_power_* (per operation)
- **Cleanup**: Rotate backups in data/backups/ (keep 2 latest, archive rest)

---

## 4. Control Modes

### Mode A: SOLO_MADRE (Default - Always Safe)
```
✅ Madre + Redis running
❌ All other services stopped
```

### Mode B: Windowed (Temporary Services)
```
✅ Madre + Redis (always)
✅ 1+ services from allowlist (temporary)
⏱️  Auto-closes on TTL expiration
🔒 Cannot open another window while active
```

### Mode C: CORE Optional (NOT Default)
```
Enabled via: VX11_POWER_WINDOWS_CORE_MODE=1
✅ Madre + Redis (always)
✅ tentaculo_link (always - when CORE enabled)
✅ 0+ additional services from allowlist
```

**Note**: CORE mode is OFF by default. To enable:
```bash
export VX11_POWER_WINDOWS_CORE_MODE=1
docker compose restart madre
```

---

## 5. Implementation Details

### WindowManager (Madre)

```python
class WindowManager:
    ALLOWLIST = {tentaculo_link, switch, hermes, ...}
    SOLO_MADRE_SERVICES = {madre, redis}
    CORE_MODE_SERVICES = {madre, redis, tentaculo_link}
    
    def open_window(services, ttl_sec, hold, reason):
        # Validate allowlist
        # Check no active window
        # Execute docker compose up (with timeout)
        # Start TTL checker if ttl_sec > 0
        # Register in metadata
        
    def close_window(reason):
        # Execute docker compose stop
        # Clear TTL
        # Record history
        
    def check_ttl():
        # Background task (runs every 1s)
        # If window expired: auto-close
```

### Routes Protection
```python
@router.post("/windows/open")
async def open_window(req, authorized: bool = Depends(token_guard)):
    # Token validated by dependency
    # Endpoint only exposed if VX11_POWER_WINDOWS_ENABLED=1
```

### Flags (Environment)
```
VX11_POWER_WINDOWS_ENABLED=0|1          # Default: 0 (OFF)
VX11_POWER_WINDOWS_CORE_MODE=0|1        # Default: 0 (no CORE)
VX11_POWER_WINDOWS_LOG_LEVEL=DEBUG|INFO # Default: INFO
VX11_POWER_WINDOWS_TIMEOUT_SEC=30       # Default: 30
VX11_POWER_WINDOWS_TTL_CHECK_INTERVAL=1 # Default: 1 (seconds)
```

---

## 6. E2E Test Conductor (Phase 3)

**File**: scripts/e2e_test_conductor_v1.py

**Flow**:
1. **Open Window** (switch + hermes + spawner)
2. **Health Checks** (wait for services ready)
3. **Run Real Flows** (e.g., operator login, switch routes)
4. **Collect Metrics** (CPU%, memory%, I/O wait, latencies)
5. **Close Window** (verify services stopped)
6. **Verify SOLO_MADRE** (confirm back to default)

**Throttling**:
```
if cpu_usage > 70%:
    sleep(5)
    retry
if iteration > MAX_ITERATIONS (default 3):
    stop
```

**Output**: docs/audit/<TIMESTAMP>_E2E_CONDUCTOR_v1/
```
test_results.json          # JSON summary
metrics.json               # CPU/memory/latency
logs/docker_events.txt     # docker compose events
logs/services_health.txt   # health check results
CONDUCTOR_RUN_LOG.md       # Human-readable report
```

---

## 7. INEE + Manifestator Integration (Phase 5)

### Hormiguero (INEE)
```
Flags (OFF by default):
  VX11_INEE_ENABLED=0|1
  VX11_INEE_FORWARD_ENABLED=0|1
  
Namespace:
  hormiguero_inee_*     # All tables prefixed
  
Forward path:
  Hormiguero → tentaculo_link:8000 (never madre:8001 direct)
```

### Manifestator (Builder)
```
Flags (OFF by default):
  VX11_MANIFESTATOR_EMIT_INTENT_ENABLED=0|1
  
New endpoint (when enabled):
  POST /manifestator/builder/emit-intent
    Request: { "intent_type": "build", "target": "switch", ... }
    Response: { "intent_id": "uuid", "status": "pending" }
    
Behavior:
  - Never execute docker build directly
  - Always emit intent to Madre
  - Madre decides execution via window system
```

---

## 8. Deployment Readiness Checklist

- [ ] POWER_WINDOWS_SPEC.md (this file) ✅
- [ ] WindowManager implementation (Madre)
- [ ] Endpoints in routes_power.py
- [ ] Optional proxy in tentaculo_link
- [ ] E2E Test Conductor (v1, real flows)
- [ ] Autofix loop (DeepSeek R1 assisted)
- [ ] INEE flags + namespacing (Hormiguero)
- [ ] Manifestator emit-intent (OFF by default)
- [ ] DEPLOYMENT_READY_SUMMARY.md (final)

---

## 9. Backward Compatibility

- **Existing Power API** (`/madre/power/service/{name}/start|stop`) remains unchanged
- **New Windows API** is additive (no breaking changes)
- **Flags**: All OFF by default (opt-in)
- **Migration**: No data migration needed (fresh state on startup)

---

## 10. Known Limitations & Phase 3+ Roadmap

### Phase 2 (This Spec)
- Single concurrent window (no queuing)
- No distributed TTL (single Madre instance)
- Hold mode not time-limited (manual close or timeout 0)

### Phase 3 (Future)
- Multi-window queue (allow N concurrent)
- Distributed TTL (via Redis)
- Window prioritization (high/normal/low)
- Resource-aware scheduling (CPU/memory reservations)

### Phase 4 (Future)
- Predictive scaling (based on metrics)
- Auto-remediation (restart failed services)
- INEE full integration (autonomous CPU management)

---

## References

- **Existing Code**: madre/routes_power.py, madre/power_windows.py
- **E2E Conductor**: scripts/e2e_test_conductor_v0.py (v0 reference)
- **Architecture Analysis**: docs/audit/ARCHITECTURE_ANALYSIS.md
- **Phase 1 Summary**: docs/audit/POWER_WINDOWS_PHASE1_SUMMARY.md

---

**Document Status**: APPROVED FOR PHASE 2 IMPLEMENTATION
