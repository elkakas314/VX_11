# VX11 DEGRADED MODE ROOT CAUSE ANALYSIS
**Date**: 2026-01-03T12:00:00Z  
**Component**: Frontend ↔ Tentaculo_link API v1 Mismatch

## PROBLEM STATEMENT
Frontend shows: **"⚠️ Degraded Mode: Some services are unavailable (solo_madre policy active)"**

## ROOT CAUSES

### 1. API VERSION MISMATCH (CRITICAL)
**Expected by frontend**: `/operator/api/v1/events`  
**Available in tentaculo_link**: `/operator/api/events` (no `/v1`)  
**Status**: 404 NOT FOUND

**Files affected**:
- [tentaculo_link/main_v7.py#L5292](tentaculo_link/main_v7.py#L5292) - Route defined WITHOUT `/v1`
- [tentaculo_link/main_v7.py#L263](tentaculo_link/main_v7.py#L263) - Middleware proxy doesn't rewrite v1

### 2. MIDDLEWARE PROXY MISCONFIGURATION
**Current behavior**: Forwards `/operator/api/*` to removed `operator-backend` service  
**Expected**: Either:
- Option A: Rewrite v1→native AND route to native handlers
- Option B: Disable proxy, use native P0 endpoints only

**Problem line**: [tentaculo_link/main_v7.py#L286](tentaculo_link/main_v7.py#L286)
```python
target_url = f"{operator_url}{upstream_path}"  # No v1 translation
```

### 3. POLICY HARDCODED TO SOLO_MADRE
**Line**: [tentaculo_link/main_v7.py#L5091](tentaculo_link/main_v7.py#L5091)
```python
return CoreStatus(
    mode="solo_madre",
    policy="SOLO_MADRE",  # ← ALWAYS SOLO_MADRE
```

**Impact**: Even if services are UP, frontend sees "degraded"

## ARCHITECTURE CLARIFICATION

### Switch vs Hermes
**Switch (Port 8002)**:
- Deterministic routing engine (CLI-first)
- Activation: When operator-backend DOWN AND all APIs DOWN
- TTL: 3600s fallback window
- Status: Can be OFF_BY_POLICY (needs window)

**Hermes (Port 8003)**:
- Local 7B inference model (edge LLM)
- Complementary to Switch, NOT replacement
- Window-gated (requires policy window)
- Status: Optional but recommended

**Current Setup**: Both OFF_BY_POLICY in solo_madre (expected behavior)

## SOLUTIONS

### Fix Priority 1: Add v1 Compatibility Route
**File**: [tentaculo_link/main_v7.py](tentaculo_link/main_v7.py)

Add before native endpoints (after line 5290):
```python
@app.get("/operator/api/v1/{path:path}", tags=["operator-api-compat"])
@app.post("/operator/api/v1/{path:path}", tags=["operator-api-compat"])
async def operator_api_v1_compat(path: str, request: Request):
    """Compatibility bridge: /operator/api/v1/* → /operator/api/*"""
    # Redirect v1 to native routes
    from starlette.responses import RedirectResponse
    new_path = f"/operator/api/{path}"
    return RedirectResponse(url=new_path, status_code=308)
```

### Fix Priority 2: Disable Proxy if Backend Archived
**File**: [docker-compose.full-test.yml](docker-compose.full-test.yml)

In tentaculo_link service:
```yaml
environment:
  - VX11_OPERATOR_PROXY_ENABLED=0  # Only use native handlers
```

### Fix Priority 3: Unhard code Policy Mode
**File**: [tentaculo_link/main_v7.py#L5091](tentaculo_link/main_v7.py#L5091)

Replace:
```python
# BEFORE
return CoreStatus(
    mode="solo_madre",
    policy="SOLO_MADRE",  # ← HARDCODED
)

# AFTER
policy = "SOLO_MADRE"  # Default
if switch_available and spawner_available:
    policy = None  # Full mode
elif switch_available or spawner_available:
    policy = "WINDOWED"  # Partial

return CoreStatus(
    mode=mode,
    policy=policy,  # ← DYNAMIC
)
```

## EXPECTED OUTCOMES

After applying fixes:

1. **Frontend can access events**:
   ```
   ✓ GET /operator/api/v1/events → (translated) → /operator/api/events → SSE stream
   ```

2. **Policy reflects actual state**:
   ```
   ✓ solo_madre=true when switch/spawner DOWN
   ✓ solo_madre=false when either UP
   ```

3. **Logs show SUCCESS** (not 404):
   ```
   [tentaculo_link] operator_api_events:success:correlation_id=<uuid>
   ```

## VERIFICATION STEPS

```bash
# 1. Check if /v1 routes exist
curl -v http://localhost:8000/operator/api/v1/status

# 2. Verify policy is dynamic
curl -s http://localhost:8000/vx11/status | jq .policy

# 3. Test events endpoint
curl -N http://localhost:8000/operator/api/v1/events

# 4. Check madre power state
curl -s http://localhost:8001/madre/power/state | jq .policy
```

---

**Status**: READY FOR DEPLOYMENT  
**Risk**: LOW (backwards-compatible changes)  
**Rollback**: Revert PROXY_ENABLED=1 if needed  
