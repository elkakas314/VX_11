# P12 — OPERATOR UI FLOW AUDIT
**Date**: 2025-12-28T22:45Z  
**Purpose**: Audit current Operator UI frontend setup, API routing, and serve mechanism.

---

## A. FRONTEND STRUCTURE

### Location
- **Frontend code**: `/home/elkakas314/vx11/operator/frontend/`
- **Build output**: `/home/elkakas314/vx11/operator/frontend/dist/`
- **Build config**: `vite.config.ts`

### Key Files
| File | Status | Notes |
|------|--------|-------|
| `src/services/api.ts` | HARDCODED BASE_URL | `const BASE_URL = 'http://localhost:8000'` (❌ NOT RELATIVE) |
| `src/App.tsx` | React 18 | Main component, imports apiClient |
| `vite.config.ts` | HAS PROXY CONFIG | `/api` proxy → `http://localhost:8000` (dev mode only) |
| `package.json` | Standard | `vite` + `react` + `typescript` + `tailwind` |
| `dist/` | EXISTS | Built output mounted in tentaculo_link |

---

## B. VITE CONFIG ANALYSIS

```typescript
// vite.config.ts (current)
export default defineConfig({
    plugins: [react()],
    base: '/operator/ui/',  // ✓ Correct base path for mounted position
    server: {
        host: '0.0.0.0',
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, ''),  // /api/chat → /chat
            },
        },
    },
    build: {
        outDir: 'dist',
        sourcemap: false,
    },
})
```

### Issues Found
1. **Proxy in dev mode**: `/api/*` routes to `http://localhost:8000`  
   **Problem**: But production (dist build) has NO proxy; browser calls hardcoded `http://localhost:8000` directly

2. **API client hardcoded**: `const BASE_URL = 'http://localhost:8000'`  
   **Problem**: Cannot run Operator on different host/IP; depends on localhost port 8000

---

## C. API CLIENT ANALYSIS (`src/services/api.ts`)

### Current Implementation
```typescript
const TOKEN = 'vx11-local-token'
const BASE_URL = 'http://localhost:8000'  // ❌ HARDCODED

class ApiClient {
    async request<T>(...): Promise<ApiResponse<T>> {
        const url = `${BASE_URL}${path}`
        // ... fetch with x-vx11-token header
    }
    
    async chat(message: string, sessionId?: string) {
        return this.request('POST', '/operator/api/chat', {...})
    }
    
    async status() {
        return this.request('GET', '/operator/api/status')
    }
    // ... other endpoints
}
```

### Problem
- **Dev mode**: Works via Vite proxy (http://localhost:3000 → proxy → http://localhost:8000)
- **Prod mode** (dist): Calls `http://localhost:8000` directly from browser, causing:
  - CORS errors if Operator UI served from different origin
  - DNS failures if browser host != localhost
  - Mixed content errors if UI on HTTPS, API on HTTP

---

## D. HOW OPERATOR IS SERVED

### Current Mechanism (Tentáculo Link)

In `tentaculo_link/main_v7.py` (~line 174):

```python
# Mount Operator UI static files
operator_ui_path = Path(__file__).parent.parent / "operator" / "frontend" / "dist"
if operator_ui_path.exists():
    app.mount(
        "/operator/ui",
        StaticFiles(directory=str(operator_ui_path), html=True),
        name="operator_ui",
    )
```

### Flow
1. **Browser** requests `http://localhost:8000/operator/ui/`
2. **Tentáculo Link** (FastAPI StaticFiles) serves `dist/index.html`
3. **Browser** loads JS; JS contains hardcoded `BASE_URL = 'http://localhost:8000'`
4. **Browser** makes fetch to `http://localhost:8000/operator/api/chat` (✓ same origin, works!)

### When It Breaks
- **If Operator served from proxy** (e.g., nginx on :3000 with reverse proxy to tentaculo_link:8000)
  - Browser at `http://proxy:3000/operator/ui/`
  - Browser JS tries `http://localhost:8000/operator/api/chat` (❌ different origin, CORS error)

- **If Operator served on different IP/hostname**
  - Browser at `http://192.168.1.100:8000/operator/ui/`
  - Browser JS tries `http://localhost:8000/operator/api/chat` (❌ DNS fails, not found)

---

## E. OPERATOR API ENDPOINTS (in tentaculo_link)

### P0 Implemented (in `main_v7.py`)

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/operator/api/status` | GET | ✓ NATIVE | No operator_backend dependency |
| `/operator/api/modules` | GET | ✓ NATIVE | Lists core + optional modules |
| `/operator/api/chat` | POST | ✓ NATIVE (P1) | Routes to Switch + DeepSeek fallback |
| `/operator/api/events` | GET | (stub) | Minimal implementation |
| `/operator/api/scorecard` | GET | (stub) | Reads from DB |
| `/operator/api/audit` | GET | (stub) | Lists audit runs |
| `/operator/api/settings` | GET/POST | (stub) | Settings management |
| `/operator/api/topology` | GET | (stub) | Module topology |
| `/operator/api/health` | GET | ✓ NATIVE | Health check |

### Chat Endpoint Details

**Current Logic** (`@app.post("/operator/api/chat")`):
1. Rate limit check (10 req/min per session_id) ✓
2. Message size cap (4000 chars) ✓
3. Cache check (60s TTL) ✓
4. Try Switch (4s timeout)
5. Try DeepSeek (15s timeout)
6. Return degraded response

**Problem for P12**: DeepSeek is default fallback; **P12 requires Switch-only with DeepSeek disabled**.

---

## F. CHAT FLOW: CURRENT vs. DESIRED

### Current (P11)
```
UI (http://localhost:8000/operator/ui/) →
  fetch /operator/api/chat (to http://localhost:8000) →
  tentáculo_link: /operator/api/chat →
    TRY: switch (4s) →
      IF FAIL: DeepSeek API (15s) →
        IF FAIL: degraded response
```

### Desired for P12 (Switch-Only)
```
UI (any origin/IP, relative URL "") →
  fetch /operator/api/chat (relative = same origin) →
  tentáculo_link: /operator/api/chat →
    TRY: switch ONLY (4s–8s) →
      IF FAIL: Local LLM degraded (NO DeepSeek) ←
        model: copilot_cli / local_llm
        degraded: true
        fallback_source: "local_llm_degraded"
```

---

## G. POLICY & ARCHITECTURE

### SOLO_MADRE (default)
- madre + redis + tentáculo_link only
- switch **NOT running** by default

### Issue
- Chat endpoint tries to call switch (which is offline in solo_madre)
- Falls back to DeepSeek immediately (P11 design)

### P12 Solution
**Opción 1 (canonical preferred)**:
- Operator UI can request madre to open a temporal "chat window"
- Madre temporarily starts switch + hermes for N minutes
- Chat endpoint calls switch (now available)
- Close window → madre stops switch

**Opción 2 (dev explicit)**:
- Compose profile: `solo_madre_plus_chat` (madre + redis + tentáculo_link + switch + hermes)
- Documented as non-production

---

## H. SUMMARY TABLE

| Aspect | Current | P12 Target | Status |
|--------|---------|-----------|--------|
| Base URL | Hardcoded `http://localhost:8000` | Relative (env var or empty) | ❌ TO FIX |
| Dev proxy | ✓ Vite `/api` proxy | Keep + document | ✓ OK |
| Prod serve | Static mount at `/operator/ui` | Same (keep) | ✓ OK |
| Chat fallback | Switch → DeepSeek | Switch → Local LLM | ❌ TO FIX |
| Switch availability | Not in solo_madre | Add temporal window | ❌ TO DESIGN |
| Hermes role | Routing (❌ wrong) | Catalog only | ❌ TO FIX |
| Flag for DeepSeek | None | `VX11_CHAT_ALLOW_DEEPSEEK=0` | ❌ TO ADD |

---

## I. AUDIT VERDICT

**Current State**: Functional in localhost dev + solo_madre mode with DeepSeek fallback.  
**P12 Blockers**:
1. ❌ API client hardcoded BASE_URL (not relative)
2. ❌ Chat always tries DeepSeek (P12 requires Switch-only)
3. ❌ No temporal window mechanism for switch in solo_madre
4. ❌ Hermes has wrong role (should not route)

**Next Steps**: FASE B → FASE C → FASE D → FASE E

