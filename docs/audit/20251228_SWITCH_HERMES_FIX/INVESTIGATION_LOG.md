# Switch & Hermes Crashloop Fix - Investigation Log

**Date**: 2025-12-28  
**Task**: Fix crashloop for switch/hermes when starting within power window  
**Status**: IN PROGRESS

## Step 1: Container Build & Execution Test

### Switch Container (vx11-switch:v6.7)

**Build Result**: ✅ SUCCESS
```
Step 19/19 : HEALTHCHECK
---> Successfully built 4f71ededb5fe
---> Successfully tagged vx11-switch:v6.7
```

**Runtime Execution** (docker run --rm):
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
  ✗ local_gguf_small error: All connection attempts failed
  ✗ ollama_local error: All connection attempts failed
  ✗ deepseek_r1 error: All connection attempts failed
  ✗ cli_registry error: All connection attempts failed
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
```

**Result**: ✅ HEALTHY - Uvicorn listening, no ModuleNotFoundError

---

### Hermes Container (vx11-hermes:v6.7)

**Build Result**: ✅ SUCCESS
```
Step 18/19 : CMD ["python", "-m", "uvicorn", "switch.hermes.main:app", "--host", "0.0.0.0", "--port", "8003"]
---> Successfully built f322432564de
---> Successfully tagged vx11-hermes:v6.7
```

**Runtime Execution** (docker run --rm):
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8003
```

**Result**: ✅ HEALTHY - Uvicorn listening, no errors

---

## Step 2: Problem Identification

### Discovery

Both switch and hermes containers execute successfully when run directly with `docker run`. This suggests:

1. **No missing dependencies** - fastapi, uvicorn installed correctly
2. **No module import errors** - switch.main and switch.hermes.main load without error
3. **Uvicorn starts** - Both respond to healthcheck port

### Potential Issues in docker-compose Context

1. **hermes missing build section** in docker-compose.yml
   - Only uses pre-built image: vx11-hermes:v6.7
   - No context/dockerfile specified
   - If image doesn't exist in registry, compose will fail

2. **Redis dependency**
   - tentaculo_link depends on redis service
   - switch/hermes depend on tentaculo_link
   - Redis may not be starting correctly

3. **Power Window Integration**
   - switch/hermes might fail when starting via /madre/power/service/start
   - Network connectivity issue (tentaculo_link unreachable during power window)
   - Database locking or race condition

---

## Step 3: docker-compose.yml Issues Found

### Issue 1: Hermes missing build section
```yaml
hermes:
  profiles: ["core"]
  image: vx11-hermes:v6.7      # ← ONLY image, no build context
  container_name: vx11-hermes
  ...
```

**Fix Required**: Add build section to hermes so docker-compose can build if image missing

### Issue 2: Old docker-compose version
```bash
docker-compose v1.29.2 (old, fails with ContainerConfig error)
docker compose v2.x.x (new, works correctly)
```

**Fix Required**: Add build section to docker-compose.yml for hermes

---

## Step 4: Minimal Fixes Required

### Fix 1: Add build section to hermes in docker-compose.yml

**Current**:
```yaml
  hermes:
    profiles: ["core"]
    image: vx11-hermes:v6.7
    container_name: vx11-hermes
```

**Fixed**:
```yaml
  hermes:
    profiles: ["core"]
    build:
      context: .
      dockerfile: switch/hermes/Dockerfile
    image: vx11-hermes:v6.7
    container_name: vx11-hermes
```

**Justification**: Allows docker-compose to rebuild hermes image if needed, consistent with switch service

---

## Step 5: Dockerfile Dependencies Check

### requirements_minimal.txt (used by hermes)
```
Already contains required packages (from previous investigation)
```

### requirements_switch.txt (used by switch)
```
Already contains required packages
```

**Status**: ✅ No missing dependencies

---

## Next Steps

1. [TODO] Add build section to hermes docker-compose config
2. [TODO] Open power window via tentaculo_link
3. [TODO] Start switch/hermes via power window system
4. [TODO] Verify /health endpoints respond
5. [TODO] Close power window and verify SOLO_MADRE
6. [TODO] Create P0 test script

---

## Evidence Files

- This file: INVESTIGATION_LOG.md
- Later: FIX_APPLIED.md (with actual changes)
- Later: TEST_RESULTS.md (power window test results)

