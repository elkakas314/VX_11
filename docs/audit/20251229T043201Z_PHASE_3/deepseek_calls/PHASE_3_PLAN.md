# PHASE 3 — DeepSeek R1(A) PLAN: Operator Superpack Alignment

**Generated**: 2025-12-29T04:32:01Z  
**Model**: DeepSeek R1  
**Rail**: PLAN (API design + contract + alignment)

---

## EXECUTIVE SUMMARY

**Objective**: Align Operator UI (frontend + backend) to VX11 SPEC with strict compliance:
- Single entrypoint (tentaculo:8000)
- No stubs (all real data or degraded)
- Correlation_id tracking throughout
- Feature state visibility
- Auth header validation

**Scope**: Redesign /operator/api/* endpoints to use new provider pattern + real DB data

**Estimated Effort**: 2-3 hours implementation + 1 hour testing

---

## DESIGN: /operator/api/* Contract

### 1. /operator/api/chat (POST) — Chat with reasoning

**Current State**: Works but NO correlation_id

**Planned**:
```
POST /operator/api/chat
Headers:
  x-vx11-token: <auth>
  x-correlation-id: <uuid>  (NEW: required for traceability)
Body:
{
  "session_id": "user-123",
  "message": "What modules are running?",
  "provider": "auto"  // auto|mock|deepseek_r1|local
}

Response (200):
{
  "ok": true,
  "data": {
    "correlation_id": "12345-uuid",
    "session_id": "user-123",
    "provider_used": "mock",  // which actually responded
    "status": "success",  // success|degraded|error
    "response": "3 core services running: madre, redis, tentaculo...",
    "reasoning": "Checked service_configs table, filtered enabled services...",
    "latency_ms": 45,
    "feature_disabled": false
  },
  "timestamp": "2025-12-29T04:32:01Z"
}

Error (429):
{
  "ok": false,
  "detail": "Rate limit exceeded (10 requests/minute)",
  "timestamp": "2025-12-29T04:32:01Z"
}
```

**Implementation**:
- Validate auth: x-vx11-token (check against madre state)
- Inject correlation_id in headers (use uuid4 if not provided)
- Route to switch provider registry (use PHASE 2 providers)
- Log all operations (correlation_id in audit_logs)
- Cache responses for 60s (by message hash)
- Timeout: 15s
- Rate limit: 10 requests/minute per session_id (Redis)

**Data Source**: 
- Chat handled by switch (with DeepSeek fallback)
- Feature check: query feature_flags table

---

### 2. /operator/api/status (GET) — System State

**Current State**: None (only /health)

**Planned**:
```
GET /operator/api/status
Headers:
  x-vx11-token: <auth>
  x-correlation-id: <uuid>  (NEW)

Response (200):
{
  "ok": true,
  "data": {
    "correlation_id": "12345-uuid",
    "system_state": {
      "operational_mode": "solo_madre",  // solo_madre|operative_core|full|low_power
      "policy_active": "solo_madre"  // which policy is running
    },
    "services": [
      {
        "name": "madre",
        "status": "up",  // up|down|degraded
        "port": 8001,
        "role": "orchestrator",
        "health_check_ms": 12.5,
        "last_check": "2025-12-29T04:30:00Z"
      },
      // ... 9 more services
    ],
    "features": {
      "chat": { "status": "on", "degraded": false },
      "file_explorer": { "status": "on", "degraded": false },
      "metrics": { "status": "off", "reason": "low_power_mode" },
      "events": { "status": "on", "degraded": false }
    },
    "db_health": {
      "size_mb": 591,
      "integrity": "ok",  // ok|warning|critical
      "rows_total": 1_150_000,
      "last_backup": "2025-12-29T02:00:00Z"
    }
  },
  "timestamp": "2025-12-29T04:32:01Z"
}
```

**Implementation**:
- Fetch from madre.power/status endpoint (existing)
- Augment with service_configs table data
- Add feature_flags status
- Query DB: PRAGMA quick_check, file stats
- Cache for 30s

**Data Source**: 
- madre API + service_configs table + feature_flags table

---

### 3. /operator/api/events (GET) — Server-Sent Events (SSE)

**Current State**: None

**Planned**:
```
GET /operator/api/events?follow=true
Headers:
  x-vx11-token: <auth>
  x-correlation-id: <uuid>

Response (text/event-stream, keep-alive):
event: service_status
data: {"service":"switch","status":"up","timestamp":"2025-12-29T04:32:05Z","correlation_id":"12345"}

event: feature_toggle
data: {"feature":"chat","status":"on","timestamp":"2025-12-29T04:32:10Z"}

event: performance_milestone
data: {"metric":"chat_avg_latency","value":45,"unit":"ms","timestamp":"2025-12-29T04:32:15Z"}

:heartbeat (every 30s)
```

**Implementation**:
- Open SSE connection
- Subscribe to copilot_actions_log + feature_flags + performance_logs changes
- Emit events as rows are inserted
- Connection timeout: 5 minutes
- Heartbeat: 30s (prevents proxy disconnect)

**Data Source**: 
- Real-time tail of copilot_actions_log + feature_flags + performance_logs

---

### 4. /operator/api/metrics (GET) — Performance & Usage

**Current State**: None

**Planned**:
```
GET /operator/api/metrics?period=1h
Headers:
  x-vx11-token: <auth>
  x-correlation-id: <uuid>

Response (200):
{
  "ok": true,
  "data": {
    "correlation_id": "12345-uuid",
    "period": "1h",
    "request_counts": {
      "total": 245,
      "by_endpoint": {
        "/operator/api/chat": 120,
        "/operator/api/status": 85,
        "/operator/api/events": 40
      },
      "by_status": {
        "200": 230,
        "429": 10,
        "500": 5
      }
    },
    "latencies": {
      "p50_ms": 35,
      "p95_ms": 150,
      "p99_ms": 500,
      "avg_ms": 52
    },
    "errors": {
      "timeout": 3,
      "network": 1,
      "internal": 1
    },
    "provider_usage": {
      "mock": 180,
      "deepseek_r1": 40,
      "local": 25
    }
  },
  "timestamp": "2025-12-29T04:32:01Z"
}
```

**Implementation**:
- Query performance_logs table (aggregated by time window)
- Sum requests from copilot_actions_log
- Calculate latency percentiles from performance_logs
- Cache for 5 minutes
- Support periods: 1h, 6h, 24h

**Data Source**: 
- performance_logs + copilot_actions_log tables

---

## CORRELATION_ID FLOW

Every request must carry `correlation_id` through entire chain:

```
Browser HTTP Request
  ↓ (header: x-correlation-id)
tentaculo_link:8000/operator/api/*
  ↓ (validate auth, inject in context)
madre.power/status or switch.chat
  ↓ (correlation_id in logger context)
RESPONSE
  ↓ (echo correlation_id in response.data)
Browser
  ↓ (client stores for debugging)
audit_logs table (logged at each step)
```

**Implementation Pattern**:
```python
@app.post("/operator/api/chat")
async def chat(request: ChatRequest, x_correlation_id: str = Header(None)):
    correlation_id = x_correlation_id or str(uuid4())
    logger.context["correlation_id"] = correlation_id
    
    # ... call switch provider with correlation_id
    response = await get_provider().call(
        message=request.message,
        correlation_id=correlation_id
    )
    
    # Log with correlation_id
    write_log("operator_backend", "chat:success", 
              {"correlation_id": correlation_id, ...})
    
    return {
        "ok": True,
        "data": {
            "correlation_id": correlation_id,  # echo back
            "response": response.text,
            ...
        }
    }
```

---

## FEATURE_DISABLED STATE ENUM

For each endpoint, expose feature state to frontend:

```python
enum FeatureState(str):
    ON = "on"               # Feature working normally
    OFF = "off"             # Feature disabled by policy
    DEGRADED = "degraded"   # Feature working but reduced capability
    ERROR = "error"         # Feature broken

# Example:
features = {
    "chat": FeatureState.ON,           # chat=working
    "file_explorer": FeatureState.ON,  # fs=working
    "metrics": FeatureState.OFF,       # low_power_mode disables metrics
    "events": FeatureState.DEGRADED    # SSE working but no real-time guarantee
}
```

**Implementation**:
- Query feature_flags table for each feature
- Check operational_mode (solo_madre → disable expensive features)
- Return explicit state enum in all responses

---

## SECURITY GUARDS

1. **Auth Validation** (x-vx11-token)
   - Validate token against madre state
   - Token format: `vx11_<base64_hash>`
   - Invalid token → 401 Unauthorized

2. **Correlation_id Validation**
   - Must be UUID format (or auto-generate)
   - Used for audit trail (no security impact)
   - Always echo back in response

3. **Rate Limiting**
   - 10 requests/minute per session_id
   - Redis-backed (fallback to in-memory)
   - Returns 429 Too Many Requests

4. **Input Validation**
   - Message max 4000 chars (no stubs, real truncation)
   - Provider enum validation (auto|mock|deepseek_r1|local)
   - Timeout: 15s (hard limit)

5. **Error Handling**
   - No stack traces in responses (log locally only)
   - Graceful degradation (mock provider as fallback)
   - Always return 200 with ok=false on error (no 500)

---

## COMPLIANCE CHECKLIST

✅ **Single Entrypoint**
- All /operator/api/* requests routed through tentaculo:8000
- No direct calls to operator-backend:8011 allowed

✅ **No Stubs**
- All responses backed by real data (service_configs, feature_flags, performance_logs)
- Mock provider deterministic (not random)
- Degraded state explicitly marked (not hidden)

✅ **Correlation_id Traceability**
- Injected at tentaculo entry
- Echoed in all responses
- Logged in audit_logs

✅ **Feature Visibility**
- Explicit state enums (on|off|degraded|error)
- Frontend knows why features are unavailable

✅ **Auth + Security**
- x-vx11-token required for all endpoints
- Rate limiting enforced
- Input validation strict

✅ **Error Handling**
- Timeouts respected (15s max)
- No crashes (always 200 response)
- Graceful degradation (local fallback)

✅ **Database Consistency**
- All data from schema tables (service_configs, feature_flags, performance_logs, audit_logs)
- No hardcoded service lists (generated from DB)

---

## IMPLEMENTATION SEQUENCE

1. **Step 1**: Add /operator/api/status endpoint (easiest, no routing changes)
2. **Step 2**: Inject correlation_id in tentaculo → madre routing
3. **Step 3**: Update /operator/api/chat to use new provider registry (+ correlation_id)
4. **Step 4**: Add /operator/api/events (SSE endpoint)
5. **Step 5**: Add /operator/api/metrics (aggregation queries)

**Testing**:
- Integration test: correlation_id flows through entire chain
- Mock provider responds consistently
- Feature state queries correct
- Rate limiting enforced
- Auth validation rejects invalid tokens

---

## RISK ASSESSMENT

**Low Risk**: No schema changes (all tables exist)
**Medium Risk**: Routing changes (must not break tentaculo gateway)
**Medium Risk**: Auth validation (must match madre token format)
**Low Risk**: Feature state queries (simple DB lookups)

**Mitigation**:
- Test against real DB before commit
- Use mock provider in tests (no network)
- Verify correlation_id appears in logs
- Rate limit tests (simulate burst)

---

**Status**: PLAN COMPLETE ✅  
**Next**: Implementation (PHASE 3 coding)

