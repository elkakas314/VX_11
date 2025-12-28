# OPERATOR ENDPOINTS SPECIFICATION (PROMPT 3)

**Date**: 2025-12-28  
**Version**: 1.0  
**Status**: Implemented & Deployed

---

## 📍 Single Entrypoint

All Operator requests go through **tentaculo_link:8000** (gateway).

```
Operator Frontend (or any client)
    ↓
tentaculo_link:8000 (entrypoint)
    ├─ Validates x-vx11-token header
    ├─ Routes to:
    │  ├─ Switch (for chat/intent)
    │  ├─ Madre (for power management)
    │  └─ Redis (for caching)
    └─ Responses to client
```

---

## 🔐 Authentication

**Header**: `x-vx11-token`  
**Value**: Must match `VX11_TENTACULO_LINK_TOKEN` env var  
**Default (DEV)**: `vx11-local-token`  
**Fallback**: `VX11_GATEWAY_TOKEN`

**Error**: Missing/invalid token → 401 (Unauthorized) or 403 (Forbidden)

**Note**: Token validation is set via `VX11_AUTH_MODE`:
- `off` — DEV mode, bypass auth
- `token` — x-vx11-token header required
- `jwt` — Authorization: Bearer <JWT> required

---

## 📡 Endpoints (PROMPT 3)

### 1. POST /operator/chat/ask

**Summary**: Send a chat message (simplified alternative to `/operator/chat`)

**Authentication**: Required (x-vx11-token)

**Request**:
```json
POST /operator/chat/ask
Content-Type: application/json
x-vx11-token: vx11-local-token

{
  "message": "What is the capital of France?",
  "session_id": "session-001",  // optional
  "mode": "chat",                // optional
  "metadata": {                  // optional
    "source": "operator-frontend",
    "user_id": "alice"
  }
}
```

**Response (Success)**:
```json
{
  "session_id": "session-001",
  "response": "The capital of France is Paris.",
  "metadata": {
    "source": "switch"  // or "madre" if fallback
  }
}
```

**Response (Fallback - Switch Offline)**:
```json
{
  "session_id": "session-001",
  "response": "I'm running in fallback mode with limited capabilities. ...",
  "metadata": {
    "source": "madre_fallback",
    "reason": "switch_circuit_open"
  }
}
```

**Response (Error)**:
```json
{
  "status": "service_offline",
  "module": "switch",
  "reason": "circuit_open",
  "message": "Chat service temporarily unavailable"
}
```

**Status Codes**:
- `200` — Success (with response)
- `401` — Missing/invalid token
- `422` — Invalid request body
- `503` — Switch unavailable (but fallback attempted)

**Behavior**:
1. Validate token
2. Create/reuse session (Context-7)
3. Try to route to switch
4. If switch offline: fallback to madre
5. Return response (always try to respond)

**Notes**:
- Session ID created if not provided
- Context-7 tracks message history
- Fallback to madre is automatic
- Same behavior as `/operator/chat` but with simpler signature

---

### 2. GET /operator/status

**Summary**: Get aggregated system health without waking services

**Authentication**: Required (x-vx11-token)

**Request**:
```
GET /operator/status
x-vx11-token: vx11-local-token
```

**Response (Healthy)**:
```json
{
  "status": "ok",
  "components": {
    "tentaculo_link": {
      "status": "ok",
      "port": 8000
    },
    "madre": {
      "status": "ok",
      "port": 8001
    },
    "redis": {
      "status": "ok",
      "port": 6379
    },
    "switch": {
      "status": "available",
      "port": 8002
    }
  },
  "windows": {
    "policy": "solo_madre",
    "active_count": 0
  }
}
```

**Response (Degraded)**:
```json
{
  "status": "degraded",
  "components": {
    "tentaculo_link": {
      "status": "ok",
      "port": 8000
    },
    "madre": {
      "status": "unreachable",
      "error": "connection timeout after 2s",
      "port": 8001
    },
    "redis": {
      "status": "ok",
      "port": 6379
    },
    "switch": {
      "status": "offline",
      "reason": "circuit_open",
      "port": 8002
    }
  },
  "windows": {
    "policy": "solo_madre",
    "active_count": 0
  }
}
```

**Response (Circuit Breaker Open)**:
```json
{
  "status": "ok",
  "components": {
    "switch": {
      "status": "offline",
      "reason": "circuit_open",
      "port": 8002
    },
    ...
  },
  "windows": {
    "policy": "solo_madre",
    "active_count": 0
  }
}
```

**Status Codes**:
- `200` — Always succeeds (returns current health)
- `401` — Missing/invalid token

**Behavior**:
1. **No service wakeup**: Uses passive checks only
2. GET madre:8001/health (2s timeout)
3. GET redis:6379/ping (2s timeout)
4. Check switch circuit breaker state (no direct call)
5. GET madre:8001/madre/power/state (window info)
6. Aggregate and return

**Component Status Values**:
- `ok` — Service responding normally
- `available` — Service available but untested (switch via CB)
- `unreachable` — Timeout or connection error
- `offline` — Circuit breaker open
- `unknown` — Status unknown

**Policy Values**:
- `solo_madre` — Only madre + tentaculo_link + redis running
- `operative_core` — Madre + selected services (switch, etc.)
- `full` — All services running

**Notes**:
- All component checks have 2s timeout
- Timeouts result in "degraded" overall status
- Switch checked via circuit breaker (no timeout risk)
- Used by frontend for status dashboard

---

### 3. GET /operator/power/state

**Summary**: Get current power window state (policy, active windows, services)

**Authentication**: Required (x-vx11-token)

**Request**:
```
GET /operator/power/state
x-vx11-token: vx11-local-token
```

**Response (SOLO_MADRE_CORE)**:
```json
{
  "policy": "solo_madre",
  "active_windows": [],
  "running_services": [
    "madre",
    "tentaculo_link",
    "redis"
  ],
  "available_services": [
    "switch",
    "hermes",
    "hormiguero",
    "mcp",
    "shubniggurath",
    "spawner",
    "manifestator",
    "operator-backend",
    "operator-frontend"
  ]
}
```

**Response (Window Open)**:
```json
{
  "policy": "operative_core",
  "active_windows": [
    {
      "window_id": "win-abc123",
      "created_at": "2025-12-28T12:34:56.789Z",
      "ttl_seconds": 300,
      "services": ["switch", "hermes"]
    }
  ],
  "running_services": [
    "madre",
    "tentaculo_link",
    "redis",
    "switch",
    "hermes"
  ],
  "available_services": [
    "hormiguero",
    "mcp",
    "shubniggurath",
    "spawner",
    "manifestator",
    "operator-backend",
    "operator-frontend"
  ]
}
```

**Status Codes**:
- `200` — Success
- `401` — Missing/invalid token
- `503` — Madre unavailable (fatal)

**Behavior**:
1. Validate token
2. Proxy to madre: GET /madre/power/state
3. Return response (policy, windows, services)

**Fields**:
- `policy` — Current power policy (solo_madre|operative_core|full)
- `active_windows` — Array of open power windows (with TTL, services)
- `running_services` — Services currently running (docker compose up)
- `available_services` — Services available to start

**Notes**:
- Single call to madre (fast)
- Used by frontend to update UI (services list, window countdown)
- Policy changes trigger service start/stop
- Windows have TTL and auto-close

---

## 🔄 Related Endpoints (Pre-Existing)

### GET /operator/status (different from power/status)
```
GET /operator/power/status
x-vx11-token: vx11-local-token

Response: {
  "policy": "solo_madre",
  "windows": {...},
  "docker_state": {...}
}
```

### GET /operator/session/{session_id}
```
GET /operator/session/session-001
x-vx11-token: vx11-local-token

Response: {
  "session_id": "session-001",
  "user_id": "alice",
  "created_at": "2025-12-28T10:00:00Z",
  "message_count": 5,
  "messages": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ]
}
```

---

## 🔀 Routing Diagram

```
Client (Frontend)
  │
  └─→ tentaculo_link:8000 (entrypoint)
       │
       ├─ POST /operator/chat/ask
       │  │
       │  └─→ switch:8002 (if available)
       │     └─→ madre:8001 (fallback)
       │
       ├─ GET /operator/status
       │  │
       │  ├─→ madre:8001/health (check)
       │  ├─→ redis:6379/ping (check)
       │  └─→ switch CB (circuit breaker state, no call)
       │
       └─ GET /operator/power/state
          │
          └─→ madre:8001/madre/power/state (proxy)
```

---

## 🛡️ Security

### Token Validation
- All endpoints require `x-vx11-token` header
- Validation at tentaculo_link level (gateway)
- Invalid/missing → 401/403

### No Credentials in Response
- Responses never include API keys or tokens
- Error messages safe for logging

### Fallback Safety
- Chat fallback to madre prevents total service failure
- Status checks use short timeouts (2s) to avoid cascading delays
- Power state is fast query (no spawn)

---

## 🧪 Testing

See `docs/audit/20251228T_PROMPT3_TESTS/` for:
- `test_operator_status.sh` — Health checks
- `test_operator_chat_ask.sh` — Chat endpoint
- `test_operator_power_state.sh` — Power state
- `test_operator_integration.sh` — Full scenario

Run any test:
```bash
bash docs/audit/20251228T_PROMPT3_TESTS/test_operator_status.sh
```

---

## 📝 Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-28 | Initial implementation (PROMPT 3) |

---

## 📚 Related Documents

- Power Windows: `docs/audit/20251228T_PHASE_D_REAL_EXEC/`
- Architecture: `docs/audit/20251228T_PHASE_EF_FINAL/ARCHITECTURE_FINAL_REPORT.md`
- Invariants: `docs/audit/20251228T_PHASE_B_CORE_FIX/SOLO_MADRE_CORE_DEFINITION.md`
