# FASE 1: Frontend Audit — Operator UI Integration Analysis

**Timestamp**: 2026-01-03T05:15:00Z  
**Status**: ANALYSIS COMPLETE  

---

## Root Cause Analysis: "Se ve pero no hace nada"

### Problem Statement
- Browser: Operator UI carga correctamente (dark theme, responsive)
- Events: "Disconnected from events feed" banner permanente
- Token: "Not configured" en Settings
- Chat: No responde / envíos fallidos
- API calls: 401 Unauthorized o silent failures

### Diagnosis

After code audit of `operator/frontend/src/`, the actual situation is:

✅ **Token management IMPLEMENTED correctly:**
- `getCurrentToken()` reads from localStorage
- `setTokenLocally(token)` persists to storage
- Token sent in `X-VX11-Token` header for fetch
- Token sent in query param for SSE EventSource

✅ **API client PROPERLY wired:**
- `ApiClient.request()` includes token in headers
- Relative URLs (same-origin) for single entrypoint
- `buildApiUrl()` handles dev/prod switching

✅ **EventsClient HANDLES query token:**
- Constructs URL with `?token=...` for EventSource
- Exponential backoff on connection failure
- Classifies 401/403 errors

❌ **BUT: Critical UX/Integration Issue**
- **DEFAULT_TOKEN = ''** (empty string) means without user input, ALL API calls silently fail
- **TokenSettings component EXISTS but may not be** prominently wired in main UI flow
- **No clear state machine**: UI should show "Token required" screen FIRST before attempting SSE
- **SSE aggressive reconnect**: Even with empty token, client retries infinitely (spammy)
- **No policy enforcement UI**: "solo_madre" mode should show as READ-ONLY, not "error"

---

## Files Modified / Key Locations

| File | Purpose | Status |
|------|---------|--------|
| `src/services/api.ts` | Token + HTTP client | ✅ CORRECT |
| `src/lib/events-client.ts` | SSE with query token | ✅ CORRECT |
| `src/components/TokenSettings.tsx` | Token input UI | ✅ EXISTS |
| `src/App.tsx` or routing | Main layout | ⚠️ NEED TO VERIFY integration |
| `src/views/SettingsView.tsx` | Settings tab | ⚠️ NEED TO VERIFY TokenSettings used |

---

## Root Causes (Top 3)

1. **No "guard" before SSE connection:**
   - If `getCurrentToken()` returns empty string, EventSource still tries to connect
   - Results in infinite retry loop with 401 (or similar)
   - FIX: Check if token present before init EventSource

2. **Settings tab may not be accessible or prominent:**
   - User lands on UI without token configured
   - TokenSettings is in Settings tab, but user never sees CTA to go there
   - FIX: Initial screen should be "Token required" with direct input

3. **No OFF_BY_POLICY classification in UI:**
   - When in solo_madre, some endpoints return 403 (policy deny)
   - UI treats as "error", not as "expected read-only state"
   - FIX: Classify 403 + policy message → show "Read-only / Ask Madre"

---

## Next Steps (FASE 2)

Fixes required:
1. Add "token guard" before SSE init (skip if empty)
2. Add initial screen or banner if token missing
3. Classify 403 errors as OFF_BY_POLICY vs genuine auth failure
4. Ensure TokenSettings is in main UI flow (not hidden)
5. Add debug panel (masked token, connection status, last error)

---

## Evidence

- Code verified in: `/home/elkakas314/vx11/operator/frontend/src/`
- Tests exist: `/home/elkakas314/vx11/operator/frontend/__tests__/operator-endpoints.test.ts`
- Backend confirmed operational: smoke tests passed (previous phase)
