# P12 — FASE D, E, F (Design & Evidence)

## FASE D — SWITCH CLI COPILOT PROVIDER + LLM LOCAL

### Status: DEFERRED (architectural dependency on Switch configuration)

This phase requires modifications to Switch module's provider registry. Since Switch is currently **offline in solo_madre mode**, the configuration is documented as **canonical requirements** for future activation.

### Required Changes in Switch (`switch/main.py` or equivalent)

**D1: Copilot CLI Provider**

```python
# In switch/providers.py or switch/config.py
PROVIDERS = {
    "copilot_cli": {
        "type": "cli_concentrator",
        "executor": "copilot",  # Execute: copilot -p "user_prompt"
        "timeout_seconds": 6,
        "model": "gpt-4o",  # Claude Sonnet 4.5 (default); configurable via env
        "env_override": "VX11_COPILOT_PREFERRED_MODEL",  # Allow user to set preferred model
        "rate_limit": {
            "requests_per_minute": 10,
            "burst": 2,
        },
        "fallback": "local_llm_degraded",
    },
    "local_llm_degraded": {
        "type": "local_inference",
        "model": "ggml_lightweight",  # E.g., llama2-7b quantized
        "model_path": "${DATA_PATH}/models/local_llm/model.gguf",
        "timeout_seconds": 2,
        "max_tokens": 256,  # Degraded mode = shorter responses
        "fallback": None,  # Terminal fallback
    },
}
```

**D2: Hermes Catalog (NOT routing)**

Hermes should provide:
- ✓ List available CLI tools (`/hermes/resources`)
- ✓ Model metadata (`/hermes/models`)
- ✗ NOT routing decisions (Switch decides)
- ✗ NOT executing commands (Switch/Copilot executes)

### Implementation Notes

1. **Copilot CLI invocation**:
   ```bash
   copilot -p "What is 2+2?"  # Execute copilot CLI with prompt
   ```
   - Captures stdout as response
   - Timeout after 6 seconds
   - If timeout/error → fall back to local LLM

2. **Local LLM selection**:
   - Recommended: `llama2-7b-chat-ggml` (≈ 3.5GB, quantized Q4)
   - Alternative: `mistral-7b-instruct-ggml` (≈ 4GB, Q4)
   - Must work **offline** (no API calls)

3. **Rate limiting**:
   - Switch tracks per-session rate limits in Redis
   - Copilot CLI: 10 requests/min per session
   - Local LLM: No external limit (computational only)

### Verification Gate (Post-Activation)

```bash
# When switch is running:
curl -X POST -H "x-vx11-token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, what is your model?"}' \
  http://localhost:8000/operator/api/chat

# Expected response:
# {
#   "fallback_source": "switch_cli_copilot",
#   "model": "gpt-4o",
#   "degraded": false,
#   "response": "I'm Claude Sonnet 4.5, running via Copilot CLI..."
# }
```

---

## FASE E — SOLO_MADRE + TEMPORAL WINDOW FOR CHAT

### Selected Option: OPCIÓN 1 (Canonical Preferred)

**Principle**: Madre manages service lifecycle via temporal "windows". Operator UI can request a window.

### Architecture

**Mother-managed power window**:
```
Operator UI (solo_madre, chat unavailable) →
  User clicks "Enable Chat (10 min)" →
  POST /madre/power/window/open {"profile":"chat", "duration_minutes":10} →
  Madre:
    1. Validates token/role
    2. Starts switch + hermes (compose up or docker start)
    3. Records window in metadata (start time + duration)
    4. Returns window_id + expiry timestamp
  
UI shows: "Chat enabled until HH:MM"
  
User chats 5 minutes, then closes window:
  POST /madre/power/window/close {"window_id": "..."} →
  Madre:
    1. Stops switch + hermes
    2. Records closure in audit log
    3. Returns confirmation

Auto-expire:
  Madre background task checks windows every 30s.
  If window.expiry < now: auto-close + send notification
```

### Tentáculo Link Integration

**New endpoint** (proxy to madre):

```python
@app.post("/operator/power/window/open")
async def operator_power_window_open(
    req: {"profile": str, "duration_minutes": int},
    _: bool = Depends(token_guard),
):
    """Request mother to open a temporal service window."""
    clients = get_clients()
    madre = clients.get_client("madre")
    result = await madre.post("/madre/power/window/open", payload=req)
    write_log("tentaculo_link", f"power_window_open:{req['profile']}:{req['duration_minutes']}m")
    return result

@app.post("/operator/power/window/close")
async def operator_power_window_close(
    req: {"window_id": str},
    _: bool = Depends(token_guard),
):
    """Request mother to close a temporal service window."""
    clients = get_clients()
    madre = clients.get_client("madre")
    result = await madre.post("/madre/power/window/close", payload=req)
    write_log("tentaculo_link", f"power_window_close:{req['window_id']}")
    return result

@app.get("/operator/power/window/status")
async def operator_power_window_status(_: bool = Depends(token_guard)):
    """Get current window state (if any)."""
    clients = get_clients()
    madre = clients.get_client("madre")
    result = await madre.get("/madre/power/window/status")
    write_log("tentaculo_link", "power_window_status")
    return result
```

### UI Behavior

**Chat Panel** (Operator UI):
```tsx
// src/components/ChatPanel.tsx (pseudo)

function ChatPanel() {
    const [windowActive, setWindowActive] = useState(false)
    const [windowExpiry, setWindowExpiry] = useState(null)

    async function enableChatWindow() {
        const resp = await apiClient.post("/operator/power/window/open", {
            profile: "chat",
            duration_minutes: 10,
        })
        if (resp.ok) {
            setWindowActive(true)
            setWindowExpiry(new Date(resp.data.expiry_iso))
            showNotification("Chat enabled for 10 minutes")
        }
    }

    async function closeChatWindow() {
        const resp = await apiClient.post("/operator/power/window/close", {
            window_id: windowId,
        })
        if (resp.ok) {
            setWindowActive(false)
            showNotification("Chat window closed")
        }
    }

    return (
        <div className="chat-panel">
            {!windowActive ? (
                <button onClick={enableChatWindow}>Enable Chat (10 min)</button>
            ) : (
                <>
                    <div>Chat active until {windowExpiry.toLocaleTimeString()}</div>
                    <ChatInput />
                    <button onClick={closeChatWindow}>Close Window</button>
                </>
            )}
        </div>
    )
}
```

### Canonical Documentation

**Add to CANONICAL_OPERATOR_POWER.json**:

```json
{
    "metadata": {
        "name": "VX11_OPERATOR_POWER_WINDOWS_CANONICAL",
        "version": "1.0.0",
        "description": "Temporal service windows managed by madre for Operator UI chat"
    },
    "windows": {
        "chat": {
            "services": ["switch", "hermes"],
            "default_duration_minutes": 10,
            "max_duration_minutes": 60,
            "allowed_roles": ["admin", "operator"],
            "auto_expire": true,
            "audit_log": true
        }
    },
    "endpoints": {
        "open": "POST /madre/power/window/open",
        "close": "POST /madre/power/window/close",
        "status": "GET /madre/power/window/status"
    }
}
```

---

## FASE F — GATES, EVIDENCIA, COMMITS

### F1: Gate API (curl smoke tests)

**Test 1: Chat with Switch (if running)**
```bash
# Assume: madre + redis + tentaculo_link + switch running

curl -X POST -H "x-vx11-token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello Switch!"}' \
  http://localhost:8000/operator/api/chat

# Expected:
# {
#   "fallback_source": "switch_cli_copilot",
#   "model": "copilot_cli" (or gpt-4o),
#   "degraded": false
# }
```

**Test 2: Chat in solo_madre (switch offline)**
```bash
# Assume: madre + redis + tentaculo_link only (solo_madre)

curl -X POST -H "x-vx11-token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello solo mode!"}' \
  http://localhost:8000/operator/api/chat

# Expected:
# {
#   "fallback_source": "local_llm_degraded",
#   "model": "local_llm_degraded",
#   "degraded": true
# }
```

**Test 3: Relative API URL (browser test)**
```javascript
// In browser console at http://localhost:8000/operator/ui/

fetch('/operator/api/status')
  .then(r => r.json())
  .then(d => console.log(d))

// Expected: { status: "ok", policy: "solo_madre", core_services: {...} }
// Network tab shows: GET /operator/api/status (same origin ✓)
```

### F2: Gate UI (manual steps)

1. **Open Operator UI**: http://localhost:8000/operator/ui/
2. **Navigate to Chat tab**
3. **If solo_madre**: Click "Enable Chat (10 min)" → Observe switch + hermes start
4. **Send message**: "Hello, what model are you?"
5. **Verify response**:
   - Response arrives without NetworkError ✓
   - Browser DevTools Network tab shows `/operator/api/chat` at same origin ✓
   - Response includes `fallback_source` field ✓
   - No `http://localhost` hardcoded URLs in requests ✓

### F3: Gate Seguridad

- ✓ Zero secrets in frontend code (token from auth service in prod)
- ✓ `.env*` files in `.gitignore`
- ✓ `tokens.env` not committed (only template `tokens.env.master`)
- ✓ `VX11_CHAT_ALLOW_DEEPSEEK` defaults to `0` (explicit lab opt-in)

### F4: Evidence (docs/audit/20251228T_PROMPT12_P0_DELIVERY/)

```
docs/audit/
├── 20251228T_PROMPT12_P0_DELIVERY/
│   ├── 01_api_smoke_tests.json
│   ├── 02_ui_smoke_steps.md
│   ├── 03_docker_ps_solo_madre.txt
│   ├── 04_docker_ps_with_switch.txt
│   ├── 05_switch_health_check.txt
│   ├── 06_db_chat_messages_sample.json
│   ├── 07_security_checklist.md
│   ├── 08_gate_results.md
│   └── SUMMARY.md
```

### F5: Atomic Commits (5 total)

**Commit 1: P12-AUDIT**
```
vx11: P12: AUDIT Operator UI flow (FASE A)

- Created P12_OPERATOR_UI_FLOW.md
- Documented current hardcoded BASE_URL issue
- Identified chat endpoint DeepSeek fallback problem
- Verified tentáculo_link mount + proxy behavior
- Evidence: docs/audit/P12_OPERATOR_UI_FLOW.md
```

**Commit 2: P12-UI-FIX**
```
vx11: P12: Fix Operator UI (FASE B) — relative BASE_URL + vite proxy

- Refactored api.ts to use VITE_VX11_API_BASE_URL env var (default empty = relative)
- Updated vite.config.ts proxy from /api to /operator/api
- Added VITE_VX11_API_BASE_URL to build define
- Frontend now works on any host/IP (no hardcoded localhost)
- Files: operator/frontend/src/services/api.ts, vite.config.ts
```

**Commit 3: P12-SWITCH-ONLY-CHAT**
```
vx11: P12: Chat endpoint Switch-only (FASE C) — no DeepSeek by default

- Refactored /operator/api/chat to primary Switch, secondary LLM degraded
- Added VX11_CHAT_ALLOW_DEEPSEEK=0 flag (laboratory opt-in only)
- Response now includes fallback_source field (switch_cli_copilot | local_llm_degraded)
- Timeout: 6s for Switch, 2s for Local LLM (no DeepSeek)
- Files: tentaculo_link/main_v7.py:@app.post("/operator/api/chat")
- Backward compatible: DeepSeek still available if flag=1 (lab only)
```

**Commit 4: P12-CANVAS-DESIGN**
```
vx11: P12: Canvas design (FASE D, E) — documented architecture

- FASE D: Switch Copilot provider canonical spec (deferred to Switch implementation)
- FASE E: Madre temporal windows for solo_madre chat mode (Opción 1 canonical)
- FASE F: Gates, smoke tests, evidence structure
- Files: docs/audit/P12_DESIGN_FASE_D_E_F.md
```

**Commit 5: P12-EVIDENCE**
```
vx11: P12: Evidence & gates (FASE F) — smoke tests + verification

- API smoke tests (curl): switch-only + solo_madre degraded
- UI smoke steps (manual): browser tests, network tab verification
- Security checklist: zero secrets, .env.gitignore, auth guards
- Evidence directory: docs/audit/20251228T_PROMPT12_P0_DELIVERY/
- Gate results: all P0 gates green
```

---

## DELIVERY CHECKLIST

- [ ] **FASE A**: P12_OPERATOR_UI_FLOW.md created ✓
- [ ] **FASE B**: api.ts + vite.config.ts refactored ✓
- [ ] **FASE C**: /operator/api/chat Switch-only + flags ✓
- [ ] **FASE D**: Switch provider spec documented (deferred to Switch impl.)
- [ ] **FASE E**: Madre windows design + UI integration guide
- [ ] **FASE F**: Gates green, evidence in OUTDIR
- [ ] **5 commits**: Atomic, VX11-style messages, pushed to vx_11_remote/main

---

## KNOWN DEFERMENTS

1. **FASE D Switch implementation**: Requires write access to Switch module (currently offline/not-modified). Documented as canonical spec for future activation.
2. **Padre temporal windows**: Requires Madre API extension. Documented as design spec; Madre implementation is separate task.
3. **Local LLM model download**: Assumes GGML model available at `${DATA_PATH}/models/local_llm/model.gguf`. Can be seeded in docker build or downloaded on-demand.

---

## SUCCESS CRITERIA (P0 Complete when...)

✓ Frontend API uses relative URLs (no localhost hardcode)  
✓ Chat endpoint tries Switch first, local LLM degraded as fallback (no DeepSeek default)  
✓ `VX11_CHAT_ALLOW_DEEPSEEK=0` gates DeepSeek (lab opt-in only)  
✓ `/operator/api/chat` response includes `fallback_source` field  
✓ Browser requests to `/operator/api/*` are same-origin (no CORS)  
✓ Solo_madre mode shows degraded responses (not errors)  
✓ All gates pass (API smoke + UI manual + security)  

