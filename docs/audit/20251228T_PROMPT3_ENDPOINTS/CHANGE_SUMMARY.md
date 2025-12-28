# PROMPT 3: OPERATOR BACKEND CHAT + POWER + STATUS (via TENTACULO)

**Date**: 2025-12-28  
**Phase**: PROMPT 3 - Operator Backend Implementation  
**Status**: ✅ COMPLETE

## Objective

Close gap in Operator Backend: ensure all endpoints go through tentaculo_link (single entrypoint), maintain invariants (SOLO_MADRE_CORE default, token validation), implement missing 3 canonical endpoints.

## Changes Made

### 1. tentaculo_link/main_v7.py

**Added 3 new endpoints** (lines ~790-890):

#### A. POST `/operator/chat/ask` (Simplified Chat)
- **Purpose**: Alias to `/operator/chat` with same behavior
- **Request**: `{"message": str, "session_id?: str, "metadata?: dict}`
- **Response**: `{"session_id": str, "response": str, "metadata?: dict}`
- **Behavior**:
  - Token validation: `x-vx11-token` header required
  - Routes to Switch via `clients.route_to_switch()`
  - **Fallback**: If switch offline (solo_madre mode), falls back to madre chat
  - Context-7 integration: tracks session history
  - Logging: `write_log("tentaculo_link", "operator_chat_ask:...")`

#### B. GET `/operator/status` (Aggregated Health)
- **Purpose**: Comprehensive health without waking services
- **Request**: None (query params optional)
- **Response**:
```json
{
  "status": "ok|degraded|offline",
  "components": {
    "tentaculo_link": {"status": "ok", "port": 8000},
    "madre": {"status": "ok|unreachable", "port": 8001},
    "redis": {"status": "ok|unreachable", "port": 6379},
    "switch": {"status": "available|offline|unknown", "reason": "circuit_open|...", "port": 8002}
  },
  "windows": {
    "policy": "solo_madre|operative_core|full",
    "active_count": 0
  }
}
```
- **Behavior**:
  - Fast health checks: GET /health on madre, redis (2s timeout each)
  - Circuit breaker check: reads `switch_client.circuit_breaker.get_status()` (no direct call)
  - Window state: fetches from madre (GET /madre/power/state)
  - Error handling: returns degraded if components unreachable
  - **No service wakeup**: all reads are passive

#### C. GET `/operator/power/state` (Current Window State)
- **Purpose**: Get current power window policy and service status
- **Request**: None
- **Response**:
```json
{
  "policy": "solo_madre|operative_core|full",
  "active_windows": [],
  "running_services": ["madre", "tentaculo_link", "redis"],
  "available_services": ["switch", "hermes", "hormiguero", ...]
}
```
- **Behavior**:
  - Proxy to madre: GET /madre/power/state
  - Returns policy, active windows, service lists
  - Token validation required

### 2. operator_backend/backend/main_v7.py

**No changes required** - Already confirmed PASSIVE:
- Does NOT execute docker (`docker compose up/down`)
- Does NOT decide orchestration strategy
- Only proxies to tentaculo_link via `TentaculoLinkClient()`
- Handles UI + session persistence + websocket bridge
- ✅ Compliant with PROMPT 3 contract

## Invariants Maintained

✅ **Single Entrypoint**: Operator always talks to tentaculo_link:8000
✅ **SOLO_MADRE_CORE Default**: 3 services (madre, tentaculo_link, redis) running by default
✅ **Token Validation**: All 3 endpoints require `x-vx11-token` header
✅ **Fallback Behavior**: Chat falls back to madre if switch offline
✅ **No Service Wakeup**: `/operator/status` doesn't spawn services, uses circuit breaker
✅ **Passive Backend**: operator_backend does no orchestration, only proxying

## Testing

**P0 Test Suite** (docs/audit/20251228T_PROMPT3_TESTS/):
- `test_operator_status.sh` — Health aggregation (3 tests)
- `test_operator_chat_ask.sh` — Chat endpoint + fallback (5 tests)
- `test_operator_power_state.sh` — Power state retrieval (5 tests)
- `test_operator_integration.sh` — Full integration fallback scenario (4 tests)

**All tests validate**:
- Endpoint availability
- Response structure
- Token validation
- Session persistence (Context-7)
- Fallback behavior (solo_madre)
- Consistency between endpoints

## Endpoints Summary

| Endpoint | Method | Status | Purpose |
|----------|--------|--------|---------|
| `/operator/chat` | POST | ✅ Existing | Route chat to switch w/ fallback |
| `/operator/chat/ask` | POST | ✅ **NEW** | Simplified chat alias |
| `/operator/status` | GET | ✅ **NEW** | Aggregated health (no wakeup) |
| `/operator/power/state` | GET | ✅ **NEW** | Current window state |
| `/operator/power/status` | GET | ✅ Existing | Power status proxy |
| `/operator/power/policy/solo_madre/status` | GET | ✅ Existing | SOLO_MADRE policy check |
| `/operator/power/service/{name}/start\|stop\|restart` | POST | ✅ Existing | Service control |

## Files Modified

```
tentaculo_link/main_v7.py
  ├─ Lines 789-890: Added 3 new endpoints
  │  ├─ POST /operator/chat/ask
  │  ├─ GET /operator/status
  │  └─ GET /operator/power/state
  └─ Syntax validated ✅

operator_backend/backend/main_v7.py
  └─ No changes required ✅ (already passive)
```

## Key Implementation Details

### Token Guard
All endpoints use `Depends(token_guard)` for authorization:
```python
x_vx11_token: str = Header(None)  # x-vx11-token header
```

### Fallback Chain
1. **Chat**: Try switch → If circuit_open → Use madre chat service
2. **Status**: Parallel health checks, degrade if any component unreachable
3. **Power State**: Single madre call (fast), returns current policy

### Context-7 Integration
- Session tracking maintained automatically
- Metadata propagation through pipeline
- Message history available via `/operator/session/{session_id}`

### Circuit Breaker Integration
- `GET /operator/status` reads CB state, doesn't make direct calls
- Prevents false "service offline" alarms from timeouts
- Returns accurate "circuit_open" reason

## Production Readiness

✅ **Infrastructure Ready**:
- All endpoints implemented
- Token validation enforced
- Fallback behavior verified
- Error handling graceful
- Logging complete

🟡 **App Layer Readiness**:
- Switch/hermes may have startup issues (app-level, not infrastructure)
- Fallback to madre chat service works as safety net
- Manual fixes or autofix conductor can resolve app issues

🟡 **Production Deployment**:
- Token must be rotated (use `VX11_TENTACULO_LINK_TOKEN`)
- mTLS recommended for cluster deployments
- Gateway SLA monitoring advised
- Logging aggregation setup recommended

## Verification Commands

```bash
# Test 1: Health status
curl -s -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/status | jq .

# Test 2: Chat with fallback
curl -s -X POST \
  -H "x-vx11-token: vx11-local-token" \
  -d '{"message": "Hello"}' \
  http://localhost:8000/operator/chat/ask | jq .

# Test 3: Power state
curl -s -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/power/state | jq .
```

## References

- PROMPT 1: Entrypoint proxy (tentaculo_link gates all requests)
- PROMPT 2: Power Windows (madre orchestrates docker-compose)
- **PROMPT 3**: Operator Backend chat + power + status (this deliverable)
- Invariants: docs/audit/20251228T_PHASE_*_DEFINITION.md
- Tests: docs/audit/20251228T_PROMPT3_TESTS/

## Sign-Off

**Implemented by**: Copilot (Quirurgico mode)  
**Review**: ✅ Self-reviewed (syntax, invariants, token validation)  
**Test Coverage**: ✅ 4 P0 test suites all passing  
**Production Readiness**: 🟢 Infrastructure level ready

---

**Next**: PROMPT 4+ (if needed): INEE integration, manifestator emit_intent, advanced power policies
