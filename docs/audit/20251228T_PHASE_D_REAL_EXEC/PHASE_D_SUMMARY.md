# FASE D: REAL EXECUTION (Power Windows) — SUMMARY

## Objectives
- D1) Verify real docker compose execution (not just metadata)
- D2) Implement allowlist + audit logging
- D3) Test open/close window cycles

## Findings

### D1: Real Docker Compose Execution ✅
**Status**: Already implemented in `madre/routes_power.py`

**Implementation Details**:
- `docker_compose_up()` function (lines 105-192)
- `docker_compose_stop()` function (lines 192-260)
- Uses `subprocess.run()` with real docker compose commands
- Per-service execution with timeout (30s default)
- Error handling: partial failures continue, total failure aborts

**Evidence**: Successful window cycle test:
```
POST /madre/power/window/open
  → docker compose up -d switch hermes
  → window_id: 3fe74d4b-906c-453f-92ad-5c336c22c767
  → state: open

POST /madre/power/window/close
  → docker compose stop switch hermes
  → state: closed

Result: ✅ SOLO_MADRE_CORE restored (3 containers)
```

### D2: Allowlist + Audit Logging ✅
**Status**: Implemented

**Allowlist Services** (from `power_windows.py`):
- tentaculo_link (core)
- madre (core)
- redis (core)
- switch
- hermes
- spawner
- hormiguero
- manifestator
- shubniggurath
- mcp

**Audit Trail**:
- Window open/close logged to `log.info()` → /app/logs/madre-*
- Each service execution logged (returncode, elapsed_ms, stdout/stderr[:500])
- Audit timestamp included in all responses (ISO8601)

### D3: Window Cycle Test Results ✅

**Test Scenario**:
1. Open window with switch + hermes
2. Verify docker compose up succeeds
3. Wait 10s for containers to start
4. Check ps output
5. Close window
6. Verify return to SOLO_MADRE_CORE

**Result**:
```
Step 1: Opening power window...
  ✅ Window opened (ID: 3fe74d4b-906c-453f-92ad-5c336c22c767)
  ✅ Window lifecycle: created_at + deadline + ttl_remaining_sec

Step 2: Containers detected in docker compose ps
  ✅ Switch container present (Restarting due to app-level issue)
  ✅ Hermes container present (Restarting due to app-level issue)

Step 3: Closing power window...
  ✅ Window closed (services_stopped: [switch, hermes])

Step 4: Restoration verified
  ✅ 3 containers running (madre + tentaculo + redis)
  ✅ SOLO_MADRE_CORE stable
```

## Known Issue: Service Crashes

**Problem**: Switch and Hermes containers are in "Restarting" state (crashloop)

**Root Cause**: Application-level startup issues (not infrastructure)
- uvicorn import errors (ModuleNotFoundError: 'switch')
- Likely missing dependencies or path issues in container

**Impact on Test**: 
- ⚠️  Health checks timeout (services crash before /health responds)
- ✅ NOT a power window issue (execution is real)
- ✅ Infrastructure works correctly

**Mitigation**:
- Fix switch/hermes Dockerfiles (application concern, not power windows)
- Or: Use services that start successfully (e.g., redis, postgres)
- Autofix conductor (FASE 4) can diagnose and suggest patches

## Implementation Details

### docker_compose_up() Internals
```python
cmd = [
  "docker", "compose",
  "-p", "vx11",
  "-f", "/app/docker-compose.yml",
  "-f", "/app/docker-compose.override.yml",
  "up", "-d", SERVICE_NAME
]
result = subprocess.run(cmd, timeout=30, cwd="/app")
# Returns: {"status": "ok|partial|fail", "results": [...], "timestamp": ISO8601}
```

### Window State Machine
```
SOLO_MADRE_CORE
    ↓ POST /madre/power/window/open (services=[...])
OPEN (TTL countdown active)
    ↓ docker compose up -d [services]
    ↓ interval health checks
OPEN (running)
    ↓ POST /madre/power/window/close (manual or TTL expired)
CLOSING
    ↓ docker compose stop [services]
SOLO_MADRE_CORE (guaranteed)
```

### Timeout Behavior

| Scenario | Behavior |
|----------|----------|
| Service up OK | Continue, log elapsed time |
| Service up TIMEOUT (30s) | Mark as partial fail, continue |
| docker compose not available | Mark as total fail, close window |
| TTL expired | Auto-close, stop all services |

## Security & Safety

✅ **Allowlist Enforced**: Only registered services can be started  
✅ **Token Validation**: x-vx11-token required  
✅ **Audit Trail**: All operations logged (service, rc, elapsed, stdout/err)  
✅ **Timeout Protection**: 30s max per service (prevent hangs)  
✅ **Auto-close**: TTL-based windows auto-terminate  
✅ **Graceful Degradation**: Partial failures don't crash madre  

## Next Phase

**FASE E**: E2E Test Conductor v2 (Real Health Checks + Metrics)
- Use real window open/close
- Collect docker stats
- Adaptive throttling
- Capture metrics to docs/audit/

**FASE F**: INEE + Manifestator (Enterprise Features OFF)
- Namespace structure
- Intent-driven builds
- Flags OFF by default

---

**Timestamp**: 2025-12-28T04:30Z  
**Status**: ✅ PASSED — Real docker execution validated  
**Note**: Service crashes are application-level, not infrastructure  
**Next**: FASE E (Advanced E2E conductor)
