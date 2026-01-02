# PHASE 0.5: DECISION MATRIX & STRATEGY

**Generated**: 2026-01-02T18:25:00Z  
**Decisions Made By**: Copilot PHASE 0 Verification  

---

## INPUT DATA (from PHASE 0)

| Metric | Count | Finding |
|--------|-------|---------|
| Hardcoded localhost URLs in production code | 0 | ✓ PASS (vite config + test files only) |
| OFF_BY_POLICY implementations in tentaculo_link | 0 | ✗ FAIL (need to add) |
| 403 responses with plain "forbidden" detail | 9+ | ✗ FAIL (need to upgrade) |
| SSE endpoint exists | 1 | ✓ PASS (line 4124) |
| EventSource implementations in frontend | 0 | ⚠️ INFO (may not be used) |
| Retry/backoff logic in api.ts | ✓ YES | ✓ PASS (exists, need to verify SSE wiring) |

---

## DECISION 1: P0-1 Fix (403 JSON Contract)

### Decision: **PROCEED WITH FIX**

**Rationale**:
- Current 403 responses are opaque ("forbidden" only)
- Client has NO indication of WHY they're blocked
- No way to know if it's a temporary policy block vs permanent 403
- operator/backend already uses OFF_BY_POLICY, so contract is known

**Implementation Strategy**:
1. Define OFF_BY_POLICY response schema in a shared file
2. Update all 9 files in tentaculo_link/routes/ to use the schema
3. Add madre/ responses to match contract
4. Test with curl/Postman to verify JSON is returned

**Priority**: 🔴 **CRITICAL** (blocks P0 clearance)

**Files to modify**:
```
tentaculo_link/routes/audit.py (line 28)
tentaculo_link/routes/events.py (line 25)
tentaculo_link/routes/hormiguero.py (line 20)
tentaculo_link/routes/internal.py (line 19)
tentaculo_link/routes/metrics.py (line 27)
tentaculo_link/routes/rails.py (lines ?)
tentaculo_link/routes/settings.py (line 25)
tentaculo_link/routes/spawner.py (line ?)
tentaculo_link/routes/window.py (line 42)
madre/ responses (as found)
```

---

## DECISION 2: SSE & Retry Logic

### Decision: **VERIFY BEFORE IMPLEMENTING**

**Current Status**:
- ✓ SSE endpoint exists at line 4124
- ✓ Retry/backoff logic exists in api.ts
- ⚠️ Unclear if EventSource errors→retry pipeline is wired

**Verification needed**:
```bash
# 1. Check how EventSource is used
grep -r "new EventSource\|fetch.*events" operator/frontend/src

# 2. Check if error handler calls retry logic
grep -A10 "onerror" operator/frontend/src

# 3. Verify if OFF_BY_POLICY affects SSE flow
grep -B5 -A5 "SSE\|EventSource" tentaculo_link/main_v7.py
```

**If NOT wired**:
- Implement `connectWithRetry()` method for SSE
- Wire OFF_BY_POLICY errors to exponential backoff
- Test with solo_madre mode active

**Priority**: 🟡 **MEDIUM** (optional for P0 clearance, nice-to-have for P1)

---

## DECISION 3: Hardcoded Ports Assessment

### Decision: **ACCEPT AS-IS (No action required)**

**Finding**: localhost:8000 found in:
- `operator/frontend/vite.config.ts` (dev proxy)
- `operator/frontend/__tests__/operator-endpoints.test.ts` (test config)
- node_modules/ (documentation only)

**Why it's OK**:
- Vite config is development-time only; not included in production build
- Test files can hardcode for unit tests
- Production code uses window.location.origin (relative URLs) ✓

**Priority**: 🟢 **SKIP**

---

## DECISION 4: Import Chain Integrity

### Decision: **ACCEPT (No broken imports)**

**Finding**:
- madreactor: 0 imports found (reserved name, not yet used)
- shubniggurath: 55 imports found (mostly legacy in attic/)
- Active code in switch/, shubniggurath/ uses shub_ functions (no imports broken)

**Why it's OK**:
- shubniggurath/ module exists and is importable
- No circular dependencies detected
- Legacy code in attic/ is archived; not in active flow

**Priority**: 🟢 **SKIP**

---

## EXECUTION PLAN (PHASE 1)

### Step 1: Implement OFF_BY_POLICY Schema (P0-1)
**Time**: ~30 min
**Files**:
- Create: `tentaculo_link/models/errors.py` with `OffByPolicyError` Pydantic model
- Modify: 9 route files (replace HTTPException with raise OffByPolicyError)
- Test: `curl http://localhost:8000/audit -H "X-VX11-Token: invalid" -v`

### Step 2: Verify SSE Wiring (P0-2)
**Time**: ~20 min
**Files**:
- Check: operator/frontend/src/services/api.ts (EventSource usage)
- If missing: Implement EventSource→retry pipeline
- Test: Open browser console, trigger solo_madre mode, observe retry behavior

### Step 3: E2E Test (P0 Clearance)
**Time**: ~10 min
**Command**:
```bash
cd /home/elkakas314/vx11
docker-compose -f docker-compose.full-test.yml down
docker-compose -f docker-compose.full-test.yml up -d
sleep 5
# Test P0-1: 403 with OFF_BY_POLICY
curl http://localhost:8000/events/ingest \
  -H "X-VX11-Token: wrong" \
  -H "Content-Type: application/json" -v
# Should return JSON with "off_by_policy" status
```

### Step 4: Git Commit
**Message**: `vx11: tentaculo_link: implement OFF_BY_POLICY JSON contract (P0-1) + post-task`
**Evidence**: docs/audit/phase0_final/PHASE1_IMPLEMENTATION_LOG.md

---

## DECISION SUMMARY TABLE

| Decision | Choice | Priority | Action |
|----------|--------|----------|--------|
| P0-1 (403 JSON) | PROCEED | 🔴 CRITICAL | Implement OFF_BY_POLICY in 9 files |
| P0-2 (SSE retry) | VERIFY | 🟡 MEDIUM | Check EventSource wiring, implement if needed |
| P0-3 (hardcoded ports) | ACCEPT | 🟢 SKIP | No action needed (dev/test only) |
| P0-4 (imports) | ACCEPT | 🟢 SKIP | No broken imports detected |

---

## BLOCKERS REMAINING

**Critical Path**:
1. ✅ PHASE 0: Verification complete
2. 🟠 PHASE 0.5: Decision matrix complete (this document)
3. ⏳ PHASE 1: Ready to implement (awaiting GO signal)

**GO/NO-GO Criteria**:
- ✅ All services UP
- ✅ Invariants I1/I2 verified
- ✅ P0 issues identified and documented
- ⏳ Ready for PHASE 1 implementation

**Status**: **READY FOR PHASE 1 ⏳** (awaiting user confirmation)

