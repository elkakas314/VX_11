# FASE 5: DeepSeek R1 Reasoning Notes

**Date**: 2025-01-05  
**Status**: ✅ COMPLETE (Reasoning Documentation)  
**Purpose**: Explain key architecture + design decisions using structured reasoning  

---

## Reasoning 1: Token Guard + UI Screen Architecture

### Problem Statement

**Original**: "Se ve pero no hace nada" (UI visible but non-functional)  
**Symptoms**:
- Frontend loads successfully (dark theme, tabs visible)
- All API calls fail silently with 401 (missing token)
- EventsClient infinite retry loop with exponential backoff (401 every 1s, then 2s, 4s...)
- "Disconnected from events feed" banner spinning forever
- User has no guidance to configure token

### Root Cause Analysis

1. **SSE Initialization Without Token Guard**
   - EventsClient constructor called `this.connect()` unconditionally
   - Even with empty token (`getCurrentToken() === ''`), it attempted SSE connection
   - Result: 401 from server, exponential backoff retry, never succeeds

2. **No "Token Required" UI**
   - TokenSettings component existed but was in Settings tab (9/9 tabs, not discoverable)
   - Users landed on Overview tab with no prompt to configure token
   - No state tracking of `tokenConfigured` in App.tsx

3. **Silent Failures**
   - DEFAULT_TOKEN = '' means all HTTP requests silently fail
   - No banner/alert visible when requests fail
   - User sees "Disconnected" but doesn't realize it's due to missing token

### Multi-Layer Guard Solution

**Guard 1: EventsClient Token Check**
```typescript
const token = getCurrentToken()
if (!token) {
  this.shouldStop = true
  this.options.onError?.({ message: 'Token not configured', code: 'NO_TOKEN' })
  return  // ← Prevents connection attempt
}
this.connect()
```

**Rationale**: 
- Prevents 401 spam at server + client level
- Stops infinite reconnect loop before it starts
- Calls onError callback for UI to handle

**Guard 2: App.tsx Conditional Rendering**
```typescript
const [tokenConfigured, setTokenConfigured] = useState(!!getCurrentToken())
// ... component renders:
{!tokenConfigured && <TokenRequiredBanner />}
```

**Rationale**:
- Shows prominent yellow banner at page top
- Guides user to configure token BEFORE attempting operations
- Separates token setup state from operational state (eventsConnected)

**Guard 3: Token Change Detection**
```typescript
useEffect(() => {
  const handleStorageChange = () => {
    setTokenConfigured(!!getCurrentToken())
  }
  window.addEventListener('storage', handleStorageChange)
  const interval = setInterval(() => {
    setTokenConfigured(!!getCurrentToken())
  }, 1000)
  // ...
}, [])
```

**Rationale**:
- Detects token changes from same tab (polling) or other tabs (storage event)
- Auto-reloads on successful save (TokenRequiredBanner triggers reload)
- Eliminates need for manual browser refresh

### Why This Approach (vs Alternatives)

**Alternative 1: Single Modal "Configure Token on Load"**
- Pros: Guaranteed user sees config screen first
- Cons: Too intrusive; might deter users; blocks UI unnecessarily
- Decision: Rejected (banner is less intrusive, still prominent)

**Alternative 2: Retry with Backoff After Token Set**
- Pros: Would eventually work once user configures token
- Cons: Still shows 401 errors in console; confusing UX; long wait
- Decision: Rejected (token guard prevents retries, cleaner)

**Alternative 3: Embed Token Config in Overview Tab**
- Pros: User sees it immediately
- Cons: Clutters main view; not a settings place
- Decision: Rejected (banner sufficient, Settings still has TokenSettings)

### Design Outcome

**Selected**: Multi-layer guard (token check + banner + change detection)
- Prevents server spam (no 401 flood)
- Prevents client spam (no exponential backoff)
- Guides user proactively (banner visible)
- Detects token changes (auto-reconnect)
- Minimal code changes (3 files, ~50 lines added)

---

## Reasoning 2: Policy Enforcement - 403 vs 401 vs OFF_BY_POLICY

### Problem Statement

**Context**: VX11 runs in `solo_madre` mode (read-only, no spawner/switch operations).  
**Requirements**:
1. Some endpoints should return 200 with readonly response (e.g., events list)
2. Some endpoints should return 403 with policy reason (e.g., spawn hija)
3. Operator UI should NOT show "Disconnected" for readonly operations in solo_madre
4. Users should understand what IS allowed in solo_madre

### Error Classification Framework

**HTTP Status Codes**:

| Code | Meaning | Example | UI Action |
|------|---------|---------|-----------|
| 401 | No token | Missing X-VX11-Token header | Show "Token required" |
| 403 (OFF_BY_POLICY) | Policy denies access | Spawn blocked in solo_madre | Show "Readonly mode" badge |
| 403 (other) | Invalid token / Permission | Invalid API key | Show "Auth failed" |
| 200 | Success | Get events list | Normal rendering |
| 503 | Service unavailable | Switch model not loaded | Show "Degraded" banner |

### Classification Logic

**Response Packet Format**:
```json
{
  "status": 200,
  "data": {...},
  "meta": {
    "policy": "SOLO_MADRE",
    "message": "readonly mode"
  }
}
```

OR (on policy denial):
```json
{
  "status": 403,
  "error": "Operation blocked by policy",
  "meta": {
    "policy": "SOLO_MADRE",
    "reason": "OFF_BY_POLICY",
    "allowed_in_this_mode": ["read", "list", "status"]
  }
}
```

### App.tsx Detection Logic

**Before** (problematic):
```typescript
if (eventsResp.ok) {
  setEventsConnected(true)
} else if (eventsResp.status === 403 && eventsResp.data?.status === 'OFF_BY_POLICY') {
  setEventsConnected(true)  // Special case for policy
} else {
  setEventsConnected(false)  // Show "Disconnected"
}
```

**Issue**: Events endpoint always returns 200 in solo_madre, so OFF_BY_POLICY check rarely triggered

**After** (corrected):
```typescript
if (eventsResp.ok) {
  setEventsConnected(true)  // Normal success
  setMode('operational')
} else if (eventsResp.status === 401) {
  setEventsConnected(false)
  setModeMessage('Token required')
} else if (eventsResp.status === 403 && eventsResp.data?.meta?.reason === 'OFF_BY_POLICY') {
  setEventsConnected(true)  // Policy denial but reading
  setMode('readonly')
  setModeMessage('Readonly mode (solo_madre)')
} else {
  setEventsConnected(false)  // Error
}
```

### Design Principles

1. **Operational Success** (200)
   - Events stream works in any mode
   - Read operations always succeed
   - Returns policy info in metadata

2. **Explicit Policy Denial** (403)
   - Spawn/write operations blocked in solo_madre
   - Response includes "OFF_BY_POLICY" reason
   - UI shows "Readonly" badge, not error

3. **Authentication Failure** (401)
   - Guarded by EventsClient + App banner
   - Prevents reaching this status in normal flow

4. **Degradation** (503)
   - Model not loaded, DB unavailable, etc.
   - Not a policy issue; service problem
   - Show "Degraded" banner

### Why This Approach

**Why separate 200 (readonly) from 403 (blocked)?**
- Clarity: 200 = working, 403 = blocked
- Monitoring: Easy to detect policy denials
- Future: Can track which operations users attempt but can't perform

**Why include policy in response metadata?**
- Context: Frontend knows why request succeeded/failed
- Transparency: User can see current policy
- Debugging: Easier to troubleshoot policy issues

**Why not 403 for all policy-denied operations?**
- Read operations should not be denied (consistency)
- Users expect read to always work
- Design: Policy controls who can WRITE, not who can READ

---

## Reasoning 3: Lightweight Model Strategy - CLI > Switch > Fail

### Problem Statement

**Context**: VX11 supports inference for chat operations.  
**Requirements**:
1. Minimize resource usage (≤ 3GB model, avoid GPU if possible)
2. Support graceful degradation (CLI → local → fail)
3. Maintain token security (never expose API keys in frontend)
4. Support solo_madre mode (read-only, limited services)

### Design: Three-Tier Strategy

**Tier 1: Copilot CLI (Primary)**
- Route: `copilot` command with token
- Resources: Unlimited (cloud-based DeepSeek R1/GPT-4)
- Speed: Fast (depends on API)
- Use case: Development, reasoning, complex tasks
- Fallback: If CLI unavailable, try Tier 2

**Tier 2: Switch Service (Fallback)**
- Route: `POST /switch/infer` (local Hermes)
- Resources: 2.4GB memory (7B q4 model)
- Speed: Slower (10-30s on CPU)
- Use case: solo_madre mode, no external API available
- Fallback: If model not loaded or timeout, try Tier 3

**Tier 3: Degraded Response (Final)**
- Route: Return "Service unavailable" message
- Resources: Minimal (static response)
- Speed: Instant
- Use case: No inference available
- Fallback: None (user sees error)

### Model Selection Rationale

**Why Hermes 7B (not Mistral, Llama, others)?**
- ✅ Supports multi-turn conversation (important for chat)
- ✅ Instruction-following capability (for task decomposition)
- ✅ Good reasoning for small size (7B)
- ✅ Quantized to Q4 (~2.4GB)
- ✅ Ollama support (easy local setup)

**Why Q4 Quantization (not FP32)?**
- FP32: 13GB model → too large
- Q8: 6.5GB → still too large
- Q4: 2.4GB → fits in typical VM
- Trade-off: ~2% accuracy loss for 5x size reduction (acceptable)

**Why Not Smaller (e.g., Tinyllama 1B)?**
- Reasoning quality too poor
- Would need tier-4 fallback to CLI anyway
- Better to have 1 reliable model than 2 mediocre ones

### Timeout & Resource Management

**EventsClient Timeout Strategy**:
```
Connect attempt: 5s
Initial request: 10s
Exponential backoff: max 30s between retries
Max retries: 10 (total ~5min before giving up)
```

**Switch Inference Timeout**:
```
Max inference time: 30s
If exceeded: Return "Timeout" error with retry suggestion
Auto-retry: No (user triggers manual retry)
```

**Rationale**: 
- Long initial timeout (10s) allows model warmup on first call
- Exponential backoff prevents spam
- 30s max for inference (beyond this, likely hung)
- Manual retry instead of auto-retry (user in control)

### Resource Constraints

**Memory**:
- Model: 2.4GB (Hermes 7B q4)
- Runtime: 0.5GB (Python + Ollama process)
- OS: 1GB minimum
- Total: 4GB minimum available

**CPU**:
- Single inference: 100% CPU for ~10-30s (depending on hardware)
- No concurrent requests (HERMES_MAX_CONCURRENT=1)
- Rationale: Can't handle multiple requests with resource constraints

**Disk**:
- Model file: 2.4GB
- Cache: ~0.1GB per session
- Total: 3GB recommended

### Security Considerations

**API Keys**:
- Copilot CLI: Uses local token (env var or ~/.copilot)
- Switch: No external keys needed
- Frontend: Never stores OpenAI/DeepSeek keys (only VX11 token)

**Prompt Injection Prevention**:
- Switch uses simple templating (not JSON or code execution)
- All user input sanitized before sending to model
- Model output validated (no arbitrary code execution)

**Fallback Chain Security**:
- Tier 1 fail → Tier 2 (local, safe)
- Tier 2 fail → Tier 3 (static, safe)
- Never expose stack traces or internal IPs in responses

### Why This Approach (vs Alternatives)

**Alternative 1: Always Use OpenAI API**
- Pros: Reliable, high quality
- Cons: Requires API key, costs money, privacy concerns, not solo_madre friendly
- Decision: Rejected (Tier 1 option, not primary)

**Alternative 2: Always Use Local Model**
- Pros: Private, low cost
- Cons: Slow, poor quality, requires setup, limits reasoning
- Decision: Rejected (Tier 2 fallback, not primary)

**Alternative 3: Ensemble (CLI + Local + API)**
- Pros: Maximum flexibility
- Cons: Complex, hard to debug, user confusion
- Decision: Rejected (Tier 3 simpler, good enough)

### Design Outcome

**Selected**: CLI > Switch > Fail (linear fallback)
- Simple to understand and debug
- Prioritizes best quality (CLI) but gracefully degrades
- Supports solo_madre (Switch doesn't need external API)
- Minimal resource footprint (Switch only if needed)
- Clear error messages at each tier

---

## Reasoning 4: Single Entrypoint Enforcement (tentaculo_link:8000)

### Problem Statement

**Requirement**: All external access through single port (8000).  
**Why?**:
- Security: Single firewall rule
- Observability: All traffic goes through one gateway
- Policy enforcement: Centralized policy checks
- Load balancing: Single point for distribution

### Architecture

```
External (Port 8000)
    ↓
tentaculo_link (router)
    ├─ /health → gateway health
    ├─ /operator/ui/ → frontend static
    ├─ /operator/api/events → SSE stream
    ├─ /operator/api/chat → chat inference
    ├─ /switch/infer → local model (forwarded)
    ├─ /madre/health → Madre health (proxied)
    └─ /vx11/status → policy status

Internal (Not exposed)
    ├─ :8001 Madre (only via proxy)
    ├─ :8002 Switch (only via router)
    ├─ :8003 Hermes (only via Switch)
    └─ :5432 DB (only internal)
```

### Implementation Pattern

**Frontend URL Construction**:
```typescript
function buildApiUrl(path: string): string {
  // Always relative; browser resolves to same origin
  return path.startsWith('/') ? path : `/${path}`
}

// Usage:
fetch(buildApiUrl('/operator/api/chat'), { ... })
// Resolves to: http://localhost:8000/operator/api/chat (in browser)
```

**Backend Routing** (tentaculo_link/main_v7.py):
```python
@app.get("/health")
async def health():
    return {"status": "ok", "module": "tentaculo_link"}

@app.get("/operator/ui/{path:path}")
async def serve_frontend(path: str):
    return FileResponse("operator/frontend/dist/index.html")

@app.get("/operator/api/events")
async def stream_events(token: str):
    # Forward to operator:8005/events?token=...
    return await forward_request("operator:8005", f"/events?token={token}")

@app.post("/madre/power/maintenance/post_task")
async def post_task_maintenance(body: dict):
    # Proxy to madre:8001 (internal, never exposed)
    return await forward_request("madre:8001", "/power/maintenance/post_task", method="POST", data=body)
```

**Why No Direct Port Access**:
- External: `curl http://localhost:8001` → BLOCKED (firewall)
- Internal: `curl http://madre:8001` → OK (docker network)

### Token Enforcement

**At Gateway** (tentaculo_link):
```python
@app.middleware("http")
async def enforce_token(request: Request, call_next):
    if request.path.startswith("/operator/api/"):
        token = request.headers.get("X-VX11-Token") or request.query_params.get("token")
        if not token:
            return JSONResponse({"error": "Token required"}, status_code=401)
    return await call_next(request)
```

**At Service** (e.g., Chat):
```python
@app.post("/api/chat")
async def chat(body: dict, request: Request):
    token = request.headers.get("X-VX11-Token")
    # Token already checked at gateway, but verify again for safety
    if not token:
        return {"error": "Unexpected: token missing"}, 401
    # Process chat
```

### Why This Approach

**Why not direct port access (e.g., localhost:8002 for Switch)?**
- Security: Exposes internal service topology
- Policy bypass: Users could bypass gateway policy checks
- Firewall complexity: Multiple rules needed
- Decision: Enforced single entrypoint

**Why proxy instead of direct forward?**
- Observability: Log all requests at gateway
- Rate limiting: Apply limits at gateway
- Policy enforcement: Central auth + policy
- Decision: Proxy pattern mandatory

---

## Summary & Key Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| Multi-layer token guard | Prevent 401 spam + guide UX | Slightly more code |
| Banner for "Token required" | Prominent UX guidance | Requires state tracking |
| 403 OFF_BY_POLICY classification | Clear policy distinction | Requires backend coordination |
| CLI > Switch > Fail strategy | Best quality + graceful degradation | Tier 2 slow (10-30s) |
| Hermes 7B q4 model | Balance quality + resource | No GPU by default |
| Single entrypoint (8000) | Security + observability | All traffic through gateway |
| Token in header + query param | SSE compatibility | Double handling needed |

---

## References

- **Frontend**: operator/frontend/src/App.tsx, EventsClient
- **Backend**: tentaculo_link/main_v7.py
- **Models**: docs/status/FASE_4B_SWITCH_HERMES_LIGHTWEIGHT.md
- **Tests**: operator/frontend/__tests__/operator-endpoints.test.ts

---

Generated: 2025-01-05T22:30:00Z  
Session: COPILOT/CODEX FASES 1-6 - DeepSeek R1 Reasoning
