# VX11 COPILOT AUDIT SUMMARY
**Run ID**: 20260102_235356
**Date**: vie 02 ene 2026 23:55:41 CET
**Branch**: main

## SCENARIO CONFIRMED
✅ **Scenario A**: Operator under single entrypoint (:8000)
- All traffic → tentaculo_link:8000
- Frontend served at /:8000/operator
- Backend proxied at /:8000/operator/api/* → operator_backend:8011/api/v1

---

## KEY FINDINGS

### 1. Single Entrypoint (I1 Invariant)
✅ **VERIFIED**: Only tentaculo_link:8000 exposed
- No internal ports (madre, switch, spawner) exposed
- Operator frontend: dev proxy in vite.config.ts (acceptable)
- Operator test: BASE_URL hardcoded (acceptable, tests only)

### 2. 403 Response Format (P0-1)
📊 **ANALYSIS**:
- Total 403 responses found: **11**
- Structured (OFF_BY_POLICY): **9** ✅
- Opaque ("forbidden"): **2** ⚠️ (auth_required, not policy-deny)

✅ **CONCLUSION**: P0-1 nearly complete. Only 2 auth-related opaques (not policy-deny).

### 3. SSE & Retry Logic (P0-2)
- SSE references in operator frontend: **100** (extensively used)
- EventSource connection: ✅ FOUND
- Retry logic: ✅ FOUND in api.ts (backoffMs exponential)
- Recommendation: Wire EventSource errors to retry backoff

### 4. OFF_BY_POLICY Contract
27 mentions found (policy enforcement active)
- Lines 1940, 1960, 1980, 2000: power control (solo_madre)
- Line 297: operator proxy exception handler

---

## DELIVERABLES

### Created/Modified
- : Helper function (json_response_403_off_by_policy)
- Evidence: All evidence saved to 
- Backups: Pre-modification backups in 

### Validation Results
```
Health check: ✅ OK (status: "ok", module: "tentaculo_link")
Hardcoded URLs: ✅ OK (2/38 real, both acceptable - vite dev proxy + tests)
Services: ✅ All UP
```

---

## NEXT STEPS (Manual Copilot Tasks)

### DONE (Automated)
- ✅ Single entrypoint verified
- ✅ 403 analysis complete (mostly already structured)
- ✅ Helper function created
- ✅ Evidence bundled

### TODO (Copilot Review)
1. **If fixing 2 auth 403s**: Replace lines 126 and 248 with structured format
2. **SSE retry**: Integrate connectSSEWithRetry util from evidence (if needed)
3. **Vite base path**: Verify vite.config.ts uses correct base (already set to /)
4. **Frontend wiring**: Verify each API call maps to real tentaculo_link path

---

## EVIDENCE MANIFEST
Location: `docs/audit/20260102_235356/`
- evidence/00_git_history.txt - Git baseline
- evidence/01_module_structure.txt - Code structure
- evidence/05_tentaculo_route_decorators.txt - All FastAPI routes
- evidence/06_tentaculo_paths.txt - Extracted paths
- evidence/14_403_references.txt - 403 locations
- validation/00_endpoints_detected.txt - Detected endpoints
- validation/01_docker_ps.txt - Service state
- validation/02_health.json - Health response
- backups/ - Pre-modification snapshots
- diffs/ - Comparative diffs (if generated)

---

## AUDIT RUN METADATA
```
AUDIT_RUN_ID=20260102_235356
SCENARIO=A
BASE_PATH=/operator
TENTACULO_PORT=8000
HARDCODED_COUNT=2 (real)
OFF_BY_POLICY_HINTS=27
SSE_HITS=100
```

---

## Status: ✅ P0 NEARLY COMPLETE (Minor cleanups optional)
