# VX11 Operator V7.0 P0 Fix - Executive Summary (20260101)

**Commit**: `c4c46b7`  
**Branch**: `vx_11_remote/main`  
**Status**: ✅ **PRODUCTION READY**

---

## Problem Statement

The Operator V7.0 UI in solo_madre mode showed:
- ⚠️ "Disconnected from events stream. Retrying…" (continuous)
- No window control buttons visible
- No clear indication that OFF_BY_POLICY is expected (not an error)

**User Experience Impact**: Looked like a broken service when it was actually the expected solo_madre behavior.

---

## Root Cause

**File**: `operator/frontend/src/App.tsx` (lines 55-59)

```typescript
// OLD CODE:
if (eventsResp.ok && eventsResp.data) {
    const events = eventsResp.data.events || eventsResp.data
    setEvents(events)
    setEventsConnected(true)
} else {
    setEventsConnected(false)  // ❌ TREATS ALL FAILURES THE SAME
}
```

**Problem**:
- Polling events every 15s via `apiClient.events()`
- Backend responds with **403 OFF_BY_POLICY** in solo_madre (expected & correct)
- Code did NOT differentiate between:
  - 403 OFF_BY_POLICY (expected, not error) ← Should NOT show as disconnected
  - Real errors (network, auth failure, etc.) ← Should show as error
- Both cases set `eventsConnected = false` → UI shows "Disconnected" banner
- Result: Infinite false "reconnect" warning in normal operation

---

## Solution Implemented

### 1. Fix App.tsx Polling Logic (Lines 55-70)

```typescript
// NEW CODE:
if (eventsResp.ok && eventsResp.data) {
    const events = eventsResp.data.events || eventsResp.data
    setEvents(events)
    setEventsConnected(true)
} else if (eventsResp.status === 403 && eventsResp.data?.status === 'OFF_BY_POLICY') {
    // OFF_BY_POLICY in solo_madre is expected, not an error
    // Keep eventsConnected=true to avoid showing "Disconnected" banner
    setEventsConnected(true)
} else {
    // Real error (not 403 OFF_BY_POLICY)
    setEventsConnected(false)
}
```

**Key Changes**:
- Explicitly detect 403 OFF_BY_POLICY responses
- Keep `eventsConnected = true` for OFF_BY_POLICY (expected state, not error)
- Only set `eventsConnected = false` for real errors

### 2. Add Missing HormigueroView.css

- File was missing but imported in `HormigueroView.tsx`
- Caused build failure: `Could not resolve "./HormigueroView.css"`
- Created comprehensive CSS with:
  - Layout and theming
  - Event card styles
  - Progress bar styling
  - Dynamic width variable support

### 3. Refactor HormigueroView Summary Bars

```typescript
// OLD: Inline style with --bar-width variable
<div style={{ '--bar-width': `${Math.min(100, count * 10)}%` }}>

// NEW: CSS class-based dynamic width
const pct = Math.min(100, count * 10)
<div className={`summary-card bar-${pct}`}>
```

**Benefits**:
- Eliminates inline style warnings from linters
- Maintains dynamic width functionality
- Better separation of concerns (logic vs styling)

---

## Verification & Testing

### Backend Endpoints (All Via :8000)
```
✓ GET    /operator/api/chat/window/status     → status=none or open
✓ POST   /operator/api/chat/window/open       → returns window_id + deadline
✓ GET    /operator/api/events                 → 403 OFF_BY_POLICY (expected)
✓ POST   /operator/api/chat/window/close      → closes window gracefully
```

### E2E Flow - 6 Steps All PASSED ✅
1. Check initial status (solo_madre) ✓
2. Open window (ttl 600s) ✓
3. Verify window status changed ✓
4. Test chat endpoint ✓
5. Close window ✓
6. Verify status reverted to solo_madre ✓

### Build Status
```
npm run build
✓ 62 modules transformed
✓ built in 1.78s (no errors, no warnings)
```

---

## UI/UX Improvements

### Before Fix
- ⚠️ "Disconnected from events feed. Retrying…" banner (always visible in solo_madre)
- No indication that this is expected
- User confused: "Is the service broken?"

### After Fix
- ✓ No "Disconnected" banner in solo_madre (correct behavior)
- ✓ Badge shows state: "⊘ solo_madre" or "✓ window_active"
- ✓ Buttons available: "↑ Open Window" or "↓ Close Window"
- ✓ Clear indication that OFF_BY_POLICY is expected

---

## Invariants Preserved (All 6) ✅

1. **Single Entrypoint**: All requests via :8000 (tentaculo_link) only
2. **Token Validation**: X-VX11-Token header on every request
3. **solo_madre Default**: Full-profile OFF by default
4. **Window Gating**: Logical DB-backed approach (no docker-in-docker)
5. **OFF_BY_POLICY Semantics**: 403 expected in solo_madre, not shown as error
6. **No Hardcoded Secrets**: All tokens from env vars, not in code

---

## Files Modified

| File | Changes | Reason |
|------|---------|--------|
| `operator/frontend/src/App.tsx` | OFF_BY_POLICY detection logic (15 lines) | Fix false "Disconnected" banner |
| `operator/frontend/src/views/HormigueroView.tsx` | Refactor summary bars (class-based width) | Eliminate inline style warnings |
| `operator/frontend/src/views/HormigueroView.css` | **NEW** (~150 lines) | Was missing, causing build failure |
| `operator/frontend/src/App.css` | Minor newline fix | Code quality |

---

## Definition of Done ✅

- [x] Root cause identified and fixed
- [x] Backend endpoints verified working
- [x] Frontend polling logic corrected
- [x] ChatView window controls present and functional
- [x] No false "Disconnected" banner in solo_madre
- [x] No reconnect loops
- [x] Build succeeds (npm run build)
- [x] E2E flow all 6 steps PASSED
- [x] Evidence reproducible
- [x] All invariants preserved
- [x] Atomic commit with clear message
- [x] Pushed to vx_11_remote/main

---

## Deployment Impact

✅ **Ready for Production**

- **Backward Compatible**: No breaking changes
- **User-Facing Improvement**: Better error clarity
- **Monitoring**: Same endpoints, same auth, same performance
- **Rollback Plan**: Revert commit c4c46b7 if needed
- **Testing**: Manual E2E verified, ready for CI/CD

---

## How to Test Locally

### 1. Build
```bash
cd operator/frontend
npm ci && npm run build
# Expect: ✓ built in ~1.8s
```

### 2. Verify UI State
```bash
# Navigate to http://localhost:8000/operator/
# In solo_madre mode, you should see:
# - NO "Disconnected" banner
# - Chat tab shows: ⊘ solo_madre + "↑ Open Window" button
```

### 3. Test Window Control Flow
```bash
# Step 1: Check status
curl -s http://localhost:8000/operator/api/chat/window/status \
  -H "X-VX11-Token: vx11-test-token" | jq .status
# Expect: "none"

# Step 2: Open window
curl -X POST http://localhost:8000/operator/api/chat/window/open \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"services":["switch","hermes"],"ttl_sec":600}'
# Expect: window_id + deadline

# Step 3: Click "↓ Close Window" in UI or:
curl -X POST http://localhost:8000/operator/api/chat/window/close \
  -H "X-VX11-Token: vx11-test-token"
# Expect: closed successfully
```

---

## Evidence Location

All test artifacts, logs, and curl responses saved in:  
`docs/audit/20260101_operator_p0_window_audit/`

- `README.md` - Detailed technical analysis
- `E2E_VALIDATION_REPORT.md` - Full flow results
- `step*.json` - Individual endpoint responses

---

## Technical Debt Addressed

- ❌ False "Disconnected" banner removed
- ❌ Missing CSS file added
- ❌ Inline styles eliminated (code quality)
- ✅ OFF_BY_POLICY semantics clarified

---

**Status: ✅ PRODUCTION READY**  
**Next Step**: Deploy to staging/production as usual  
**Support**: Reference docs/RUNBOOK_OPERATOR_V7.md for operation guides
