# VX11 Copilot Instructions — Quick Navigation Guide

> **For AI agents starting work on VX11** — Where to find what you need

---

## 🎯 Immediate Context (Read First)

**Location:** `.github/copilot-instructions.md` → Section: **"🎯 TL;DR — Lo Esencial"**

Contains:
- Stack summary (FastAPI + React 18 + SQLite + Docker)
- All port mappings (8000-8008, 8011, 8020)
- Key tech (TanStack Query, WebSocket, Circuit Breaker)
- Typical data flow (Intent → Tentáculo Link → Switch → Executor → DB)

**Read time:** 30 seconds | **Refresh rate:** When architecture changes

---

## 🏗️ Understanding System Layout

**Location:** Section **"🏗️ ARQUITECTURA CANÓNICA"**

### Visual Topology Diagram
Shows 9 modules + Operator with clear hierarchies and responsibilities.

### Route Table & Circuit Breaker
- **Route Table:** `tentaculo_link/routes.py`
  - Intent types: CHAT, CODE, AUDIO, ANALYSIS, TASK, SPAWN, STREAM
  - Each maps to specific module endpoint
- **Circuit Breaker:** `tentaculo_link/clients.py`
  - States: CLOSED → OPEN → HALF_OPEN
  - Threshold: 3 failures, 60s recovery

### Context-7 Sessions
- File: `tentaculo_link/context7_middleware.py`
- Persistence: `data/runtime/context7_sessions.json`
- TTL with topic clustering

---

## 📝 Adding Backend Features

**Location:** Section **"🎓 Patrones Esenciales de Código"**

### Pattern 1: New Endpoint
Use `config/module_template.py` as boilerplate.
```python
from config.module_template import create_module_app
app = create_module_app("mi_modulo")
@app.post("/mi_modulo/endpoint")
async def handler(req: dict):
    return {"resultado": "ok"}
```
**File:** `operator_backend/backend/main_v7.py` (existing chat endpoint example)

### Pattern 2: Call Another Module
Never import directly. Use HTTP + circuit breaker.
```python
async with httpx.AsyncClient() as client:
    resp = await client.post(
        f"{settings.switch_url}/switch/route-v5",
        json={"prompt": prompt},
        headers={settings.token_header: token}
    )
```
**Files:** `tentaculo_link/clients.py`, `config/settings.py`

### Pattern 3: Database Access
Single-writer SQLite with proper cleanup.
```python
db = get_session("mi_modulo")
try:
    task = Task(uuid="...", name="test", module="mi_modulo")
    db.add(task)
    db.commit()
finally:
    db.close()
```
**Files:** `config/db_schema.py`, `config/settings.py`

### Pattern 4: Tokens & Auth
Never hardcode. Read from environment.
```python
TOKEN = get_token("ENV_VAR_NAME")
HEADERS = {"X-VX11-Token": TOKEN}
```
**Files:** `config/tokens.py`, `config/settings.py`

---

## ⚛️ Adding Frontend Features

**Location:** Section **"🎓 Patrones Esenciales de Código"** → Subsection 6 **"Frontend: React 18 + TanStack Query"**

### Frontend Stack
- Vite dev server: port 5173 (npm run dev)
- React 18 + TanStack Query v5 (already in package.json)
- WebSocket with exponential backoff reconnection
- Zustand for state management

### Pattern: TanStack Query Hooks

**For sending messages (mutation):**
```typescript
const chatMutation = useMutation({
  mutationFn: async (message: string) => {
    const response = await fetch(`/operator/chat`, {
      method: "POST",
      headers: { "X-VX11-Token": TOKEN, "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    return response.json();
  },
  onSuccess: () => {
    queryClient.invalidateQueries(["operatorSession", sessionId]);
  },
});
```

**For fetching session history (query):**
```typescript
const sessionQuery = useQuery({
  queryKey: ["operatorSession", sessionId],
  queryFn: async () => {
    const resp = await fetch(`/operator/session/${sessionId}`);
    return resp.json();
  },
  staleTime: 30000,  // 30s
  cacheTime: 300000, // 5 min
  retry: 1,
});
```

**File:** `operator_backend/frontend/src/services/api-improved.ts`

### Environment Variables
- `VITE_OPERATOR_API_URL` — Backend endpoint
- `VITE_VX11_TOKEN` — Auth token
- Check `config.ts` for centralized configuration

---

## 🔧 Debugging & Validation

**Location:** Section **"✅ Validación Pre-Commit"**

### Health Checks
```bash
# Quick loop
for port in 8000 8001 8002 8011; do
  curl -s http://127.0.0.1:$port/health | jq .
done
```

### Pre-Commit Checklist
```bash
# Python syntax
python -m compileall tentaculo_link operator_backend config

# Frontend type-checking
cd operator_backend/frontend && npm run type-check

# Docker compose
docker-compose config > /dev/null

# Tests
pytest tests/ -q --tb=short
```

### Finding Logs
- Module logs: `logs/{module}.log`
- Forensics: `forensic/{module}/logs/`
- Git tracking: `docs/audit/` for phase reports

---

## 🛡️ Critical Don'ts

**Location:** Section **"🛡️ Límites y NO Tocar"**

### NEVER Change:
- Ports in `docker-compose.yml` (architectural constraint)
- Root module layout without authorization
- `tokens.env.master` or `tokens.env` (secrets)
- DB schema destructively (INSERT/SELECT only)

### ALWAYS Safe:
- Module-internal logic (keep endpoint namespacing)
- `operator_backend/frontend/src/` (frontend code)
- `config/settings.py` (environment-aware config)
- `tests/` and docs
- Log messages and docstrings

---

## 🚀 Common Tasks Checklist

### "Add new chat endpoint feature"
1. Read: Section 1 "Estructura de FastAPI Modules"
2. Edit: `operator_backend/backend/main_v7.py` (line 136+ shows example)
3. Token check: `@app.post()` with `Depends(token_guard)`
4. DB: Use `OperatorMessage` model from `config/db_schema.py`
5. Validate: `curl -X POST http://127.0.0.1:8011/operator/chat`

### "Add frontend component"
1. Read: Section 6 "Frontend: React 18 + TanStack Query"
2. Create: Component in `operator_backend/frontend/src/components/`
3. Data: Use `useChat()` or `useOperatorSession()` hooks
4. Type-check: `npm run type-check`
5. Dev test: `npm run dev` on port 5173

### "Call another module from backend"
1. Read: Section 2 "Llamar Otro Módulo"
2. Reference: `config/settings.py` for `settings.switch_url` etc.
3. Use: `httpx.AsyncClient` + `AUTH_HEADERS`
4. Handle: 401/404/timeout with fallback
5. Test: Via curl or postman with correct token

### "Debug circuit breaker"
1. Check: `GET /vx11/circuit-breaker/status` (if exists)
2. Know states: CLOSED (normal) → OPEN (failed) → HALF_OPEN (recovery)
3. Recovery: 60s default timeout
4. Force test: Stop a module, trigger failure, watch recovery

---

## 📚 Reference Files Quick Links

| Need | File | Purpose |
|------|------|---------|
| **Module template** | `config/module_template.py` | FastAPI boilerplate |
| **Database schema** | `config/db_schema.py` | All models (Task, OperatorSession, etc.) |
| **Settings/URLs** | `config/settings.py` | Centralized config, module URLs |
| **Token handling** | `config/tokens.py` | Reading env vars safely |
| **Routing** | `tentaculo_link/routes.py` | Intent type mappings |
| **Circuit breaker** | `tentaculo_link/clients.py` | HTTP client with resilience |
| **Chat endpoint** | `operator_backend/backend/main_v7.py` | Real /operator/chat implementation |
| **Frontend API** | `operator_backend/frontend/src/services/api-improved.ts` | TanStack Query hooks |
| **Frontend config** | `operator_backend/frontend/src/config.ts` | Env vars, URLs |
| **Services** | `docker-compose.yml` | Port assignments, volumes, limits |

---

## 🔄 Session Resumption

**When continuing work from a previous session:**

1. Re-read: **"🎯 TL;DR"** (60 sec refresh)
2. Check: `git status` — see what's changed
3. Review: `.copilot-audit/DRIFT_LATEST.md` (if exists) — know about recent changes
4. Validate: Run health checks (see above)
5. Context: Re-read your specific section before coding

**Critical:** Always validate CI will pass:
```bash
python -m compileall tentaculo_link operator_backend config
docker-compose config > /dev/null
npm run type-check 2>/dev/null || echo "optional"
```

---

## 📞 When You're Stuck

1. **Module not starting?** → Check `/health` endpoint for each service
2. **Token rejected?** → Verify `X-VX11-Token` header equals `vx11-local-token`
3. **Import error?** → Remember: NO cross-module imports, use HTTP instead
4. **DB locked?** → Ensure all sessions call `db.close()` in finally block
5. **Type errors (frontend)?** → Run `npm run type-check`, check `config.ts`
6. **CircuitBreaker open?** → Wait 60s or restart module
7. **Don't know the architecture?** → Start with visual diagram in **"🏗️ ARQUITECTURA"**

---

**Last Updated:** 2025-12-14  
**Applies to:** VX11 v7.1+  
**Maintained by:** GitHub Copilot + community agents
