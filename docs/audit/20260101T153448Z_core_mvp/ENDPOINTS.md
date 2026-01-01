# CORE MVP: Endpoints Documentation

## INVARIANTS

1. **Single Entrypoint**: All external API routes via `:8000` (tentaculo_link)
2. **Default solo_madre**: Switch OFF by policy; only fallback_local execution
3. **Token Auth**: X-VX11-Token header required (from env: `vx11-test-token` in full-test profile)
4. **Uniform Errors**: 200 + error in response (not 4xx/5xx for policy errors)
5. **Reproducible**: 6 curl commands + pytest test suite

---

## EXTERNAL ENDPOINTS (tentaculo_link, :8000)

### A) `GET /health`
- **Purpose**: Canonica health check
- **Auth**: None
- **Response**: `{status: "ok", module: "tentaculo_link", version: "7.0"}`
- **Test**: CURL 1 ✅

### B) `GET /vx11/status`
- **Purpose**: Policy state + best-effort health
- **Auth**: X-VX11-Token required
- **Response**:
```json
{
  "mode": "solo_madre|windowed|full",
  "policy": "SOLO_MADRE",
  "madre_available": true,
  "switch_available": false,
  "spawner_available": false
}
```
- **Test**: CURL 2 ✅

### C) `POST /vx11/intent`
- **Purpose**: Execute intent (sync or async)
- **Auth**: X-VX11-Token required
- **Request Body**:
```json
{
  "intent_type": "chat|plan|exec|spawn",
  "text": "optional instruction",
  "payload": {},
  "require": {"switch": false, "spawner": false},
  "priority": "P0|P1|P2",
  "correlation_id": "uuid-optional",
  "user_id": "local",
  "metadata": {}
}
```
- **Response (sync)**:
```json
{
  "correlation_id": "...",
  "status": "DONE",
  "mode": "MADRE",
  "provider": "fallback_local",
  "response": {...},
  "degraded": false
}
```
- **Response (spawner)**:
```json
{
  "correlation_id": "...",
  "status": "QUEUED",
  "mode": "SPAWNER",
  "provider": "spawner",
  "response": {"task_id": "..."}
}
```
- **Response (off_by_policy)**:
```json
{
  "correlation_id": "...",
  "status": "ERROR",
  "mode": "FALLBACK",
  "error": "off_by_policy",
  "response": {"reason": "switch required but SOLO_MADRE policy active", "policy": "SOLO_MADRE"}
}
```
- **Tests**:
  - CURL 3 (require.switch=false) → 200 DONE ✅
  - CURL 4 (require.switch=true) → 200 ERROR off_by_policy ✅✅✅
  - CURL 5 (require.spawner=true) → 200 QUEUED ✅

### D) `GET /vx11/result/{correlation_id}`
- **Purpose**: Query result of prior intent
- **Auth**: X-VX11-Token required
- **Response**:
```json
{
  "correlation_id": "...",
  "status": "QUEUED|RUNNING|DONE|ERROR",
  "result": {...},
  "error": null,
  "mode": "MADRE",
  "provider": "fallback_local"
}
```
- **Test**: CURL 6 ✅

---

## INTERNAL ENDPOINTS (madre, :8001)

### E) `POST /madre/intent`
- **Purpose**: Internal intent processing
- **Called by**: tentaculo_link
- **Request**: Same as `/vx11/intent` (from tentaculo_link)
- **Response**: Same format as external
- **Logic**:
  - If `require.spawner=true`: queue to spawner, return QUEUED
  - Otherwise: execute fallback plan, return DONE

### F) `GET /madre/result/{correlation_id}`
- **Purpose**: Internal result query
- **Called by**: tentaculo_link
- **Response**: Same as external format

---

## CONTRACTS

### INTENT Request (Canonical)
```python
class CoreIntent(BaseModel):
    intent_type: "chat" | "plan" | "exec" | "spawn"
    text: Optional[str]
    payload: Dict[str, Any]
    require: {"switch": bool, "spawner": bool}
    priority: "P0" | "P1" | "P2"
    correlation_id: Optional[str]
    user_id: str
    metadata: Optional[Dict]
```

### Intent Response (Canonical)
```python
class CoreIntentResponse(BaseModel):
    correlation_id: str
    status: "QUEUED" | "RUNNING" | "DONE" | "ERROR"
    mode: "MADRE" | "SWITCH" | "FALLBACK" | "SPAWNER"
    provider: Optional[str]  # "fallback_local" | "switch" | "spawner"
    response: Optional[Dict | str]
    error: Optional[str]
    degraded: bool
    timestamp: datetime
```

### Error Response (off_by_policy)
- **Status Code**: 200 (NOT 423, as per MVP design)
- **Body**: `{"error": "off_by_policy", "response": {"reason": "...", "policy": "SOLO_MADRE"}}`
- **Semantic**: "This operation requires switch but SOLO_MADRE policy is active"

---

## IMPLEMENTATION DETAILS

### tentaculo_link/main_v7.py
- Import `CoreIntent`, `CoreIntentResponse`, `CoreStatus`, `CoreResultQuery` from `tentaculo_link/models_core_mvp.py`
- `/vx11/intent` endpoint:
  - Validates token via `TokenGuard`
  - Checks `require.switch`: if true → return off_by_policy (200 ERROR)
  - Proxies to madre via HTTP
  - Returns response in canonical format
- `/vx11/result` endpoint:
  - Proxies to madre
  - Returns result status

### madre/main.py
- Added `CoreMVPIntentRequest` model for internal requests
- `/vx11/intent` endpoint:
  - Stores intent in `intent_log`
  - If `require.spawner=true`: creates task, returns QUEUED
  - Otherwise: returns DONE with fallback execution
- `/vx11/result` endpoint:
  - Returns synchronous status (DONE for immediate, QUEUED for spawner)

### tentaculo_link/models_core_mvp.py
- Defines all canonical contracts (Pydantic models)
- Enums: `IntentTypeEnum`, `StatusEnum`, `ModeEnum`
- Models: `CoreIntent`, `CoreIntentResponse`, `CoreResultQuery`, `CoreStatus`, `ErrorResponse`

---

## TESTING (DoD)

All endpoints verified via:
1. Direct curl against localhost:8000 (6 calls)
2. Pytest test suite (5+ test cases)
3. No external dependencies (no Operator required)

### Test Environment
- Token: `vx11-test-token` (from docker-compose.full-test.yml)
- Host: `http://localhost:8000` (single entrypoint)
- Profile: `full-test` (madre, tentaculo_link, switch, operator-backend)

---

## DEPLOYMENT READY

✅ Single entrypoint verified
✅ Auth enforced (401/403 without/wrong token)
✅ off_by_policy clear (not opaque error)
✅ Reproducible tests (6 curls)
✅ No Operator dependency
✅ Token from env (no hardcoding)
✅ DB persistence working
✅ All endpoints documented
