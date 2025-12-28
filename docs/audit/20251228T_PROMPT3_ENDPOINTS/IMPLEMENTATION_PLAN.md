# PROMPT 3: OPERATOR BACKEND + TENTACULO ROUTING

**Goal**: Operator always talks to tentaculo_link (single entrypoint). Implement missing 3 canonical endpoints.

## Endpoints to Implement

### 1. POST `/operator/chat/ask`
**Purpose**: Simplified chat endpoint (alternative to `/operator/chat`)
**Request Body**: `{"message": str, "session_id?: str, "mode?: str}`
**Response**: Same as `/operator/chat` but simplified
**Behavior**:
  - Token validation: x-vx11-token required
  - SOLO_MADRE_CORE: fallback to madre chat service
  - With switch ON: route to switch via clients.route_to_switch()
  - Context-7 integration: track session

### 2. GET `/operator/status`
**Purpose**: Aggregated health without waking services
**Request**: No body; token required
**Response**: 
```json
{
  "status": "ok|degraded|offline",
  "madre": {"status": "ok|unreachable"},
  "redis": {"status": "ok|unreachable"},
  "tentaculo_link": {"status": "ok"},
  "switch": {"status": "ok|unavailable|offline", "reason": "circuit_open|solo_madre|..."},
  "windows": {"active_count": 0, "policy": "solo_madre"}
}
```
**Behavior**:
  - Fetch madre/health (fast check, no docker spawn)
  - Fetch redis/health (fast check)
  - Check circuit breaker for switch (don't call switch directly)
  - Get window state from madre (fast lookup)

### 3. GET `/operator/power/state`
**Purpose**: Current power window state
**Request**: No body; token required
**Response**:
```json
{
  "policy": "solo_madre|operative_core|full",
  "active_windows": [],
  "running_services": ["madre", "tentaculo_link", "redis"],
  "available_services": ["switch", "hermes", "hormiguero", ...]
}
```
**Behavior**:
  - Query madre /madre/power/state (GET, fast)
  - Return current policy + active windows + runstatus

## Implementation Strategy

1. **Add 3 new endpoints** to tentaculo_link/main_v7.py (before event_ingest if possible)
2. **Token validation**: All require `token_guard` dependency
3. **Error handling**: 
   - If madre unreachable: return degraded status
   - If redis unreachable: return degraded status
   - If switch circuit open: report as offline, not timeout
4. **Logging**: write_log() all requests + responses

## Files Modified
- tentaculo_link/main_v7.py (add 3 endpoints)
- operator_backend/backend/main_v7.py (no changes - already proxying OK)

## Tests
- P0 tests in docs/audit/20251228T_PROMPT3_TESTS/

