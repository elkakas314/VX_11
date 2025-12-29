# PHASE 3 — Steps 3-5 Implementation Plan

**Status**: In Progress  
**Estimated Duration**: 1-1.5 hours

---

## STEP 3: Use Provider Registry in /operator/api/chat

**Objective**: Replace hardcoded DeepSeek with unified provider pattern (PHASE 2)

**Changes**:
1. Import `get_provider()` from `switch.providers`
2. Replace DeepSeekClient() call with `await get_provider("deepseek_r1").call(...)`
3. Use MockProvider for tests (deterministic, no network)
4. Maintain rate limiting + cache + correlation_id

**Code Flow**:
```python
# Before:
deepseek = DeepSeekClient()
response = await deepseek.chat(message=req.message)

# After:
provider = get_provider("deepseek_r1" if allow_deepseek else "mock")
response = await provider(req.message, correlation_id)
```

**Benefits**:
- Unified provider interface (no more DeepSeekClient direct usage)
- Easy to swap providers (mock for tests, deepseek for prod, local for fallback)
- Correlation_id flows through provider
- Graceful degradation built-in

---

## STEP 4: Add /operator/api/events (SSE)

**Objective**: Real-time event streaming

**Endpoint**:
```
GET /operator/api/events?follow=true
```

**Response** (text/event-stream):
```
event: service_status
data: {"service":"madre","status":"up","timestamp":"2025-12-29T04:35:00Z"}

event: feature_toggle
data: {"feature":"chat","status":"on","timestamp":"2025-12-29T04:35:05Z"}

:heartbeat (every 30s)
```

**Implementation**:
- Use FastAPI StreamingResponse
- Tail copilot_actions_log table (polling every 5s)
- Send events as new rows appear
- Heartbeat every 30s (prevent proxy timeout)
- Connection timeout: 5 minutes

---

## STEP 5: Add /operator/api/metrics (GET)

**Objective**: Performance metrics + usage stats

**Endpoint**:
```
GET /operator/api/metrics?period=1h
```

**Response** (200):
```json
{
  "ok": true,
  "data": {
    "correlation_id": "uuid",
    "period": "1h",
    "request_counts": {
      "total": 245,
      "by_endpoint": {"/operator/api/chat": 120, ...},
      "by_status": {"200": 230, "429": 10, ...}
    },
    "latencies": {
      "p50_ms": 35,
      "p95_ms": 150,
      "p99_ms": 500,
      "avg_ms": 52
    },
    "errors": {"timeout": 3, "network": 1, ...},
    "provider_usage": {"mock": 180, "deepseek_r1": 40, ...}
  },
  "timestamp": "2025-12-29T04:35:00Z"
}
```

**Implementation**:
- Query performance_logs table (aggregated by time window)
- Calculate percentiles from latency data
- Cache for 5 minutes
- Support periods: 1h, 6h, 24h

---

## IMPLEMENTATION SEQUENCE

1. STEP 3: Modify /operator/api/chat (5 minutes)
2. Test provider integration (5 minutes)
3. STEP 4: Add SSE endpoint (10 minutes)
4. STEP 5: Add metrics endpoint (10 minutes)
5. DS-R1(B) REVIEW: Security + compliance (10 minutes)
6. Final commit + push (5 minutes)

**Total**: ~45 minutes

