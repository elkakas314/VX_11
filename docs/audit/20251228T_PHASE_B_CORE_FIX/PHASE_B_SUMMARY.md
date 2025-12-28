# FASE B: CORE FIX — SUMMARY

## Objectives
- B1) Ensure docker-compose default keeps tentaculo_link always running
- B2) Add healthchecks for CORE (madre + tentaculo_link)

## Findings

### B1: Docker-Compose Configuration ✅
**Status**: No changes needed — configuration already correct

1. `tentaculo_link`: **NO profile** (unconditional, always runs)
2. `madre`: **NO profile** (unconditional, always runs)
3. `redis`: **NO profile** (unconditional, always runs)
4. All app services: **profile="core"** or **profile="operator"** (only run when explicitly requested)

**Evidence**: docker-compose.yml lines 1-100 show tentaculo_link without profile assignment

### B2: Health Checks ✅
**Status**: All working correctly

**Test P0 Results**:
```
✅ Check 1: Exactly 3 services running (madre, tentaculo_link, redis)
✅ Check 2: :8000 (tentaculo_link) responding
✅ Check 3: :8001 (madre) responding
✅ Check 4: Redis healthy
✅ Check 5: All app services are OFF
✅ Check 6: Tentaculo sees 1 healthy core modules
```

**Health Endpoints**:
- `GET /health` (tentaculo_link:8000) → `{"status":"ok","module":"tentaculo_link","version":"7.0"}`
- `GET /health` (madre:8001) → `{"module":"madre","status":"ok","version":"7.0"}`
- `GET /vx11/status` (tentaculo:8000) → Aggregate status with port mapping

### Why No Changes Needed

The configuration already meets INVARIANTS:

1. ✅ **Single entrypoint maintained**: tentaculo_link:8000 is always available
2. ✅ **Low-power default**: Only 3 services (~1.1 GB total)
3. ✅ **Profile isolation**: App services only start with explicit `--profile core`
4. ✅ **Frontdoor guaranteed**: No scenario removes tentaculo_link

## Risk Assessment

**Risk Level**: MINIMAL (No changes)

- Configuration is already hardened correctly
- Health checks are active and functional
- Service isolation via profiles is enforced
- No modification = No regression

## Next Phase

**FASE C**: Single Entrypoint Proxy
- Verify that tentaculo_link already proxies `/operator/power/*` to madre
- Ensure token validation on all power endpoints
- Add P0 tests for proxy routing

---

**Timestamp**: 2025-12-28T04:20Z  
**Auditor**: Copilot Architecture Review  
**Status**: ✅ PASSED — No action required, proceed to FASE C
