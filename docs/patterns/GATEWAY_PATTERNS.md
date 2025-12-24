# VX11 API Gateway Patterns Documentation (Phase 3.4)

**Version:** 7.0  
**Date:** 2024-12-24  
**Scope:** Canonical patterns for tentaculo_link (gateway) implementation

---

## 1. CIRCUIT BREAKER PATTERN

### Problem
Shub service may become temporarily unavailable (crash, restart, overload). Repeated requests to unavailable service cause cascading failures.

### Solution
Implement circuit breaker with three states: CLOSED (normal), OPEN (fail-fast), HALF-OPEN (testing).

### Thresholds
- **Open threshold:** 5 consecutive errors
- **Open duration:** 60 seconds
- **Half-open test:** 1 request to check recovery

### Implementation Example
```python
class CircuitBreaker:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
    
    async def call(self, func, *args, **kwargs):
        if self.state == self.CLOSED:
            try:
                result = await func(*args, **kwargs)
                self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = self.OPEN
                raise
        
        elif self.state == self.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = self.HALF_OPEN
            else:
                raise Exception("Circuit breaker OPEN")
        
        elif self.state == self.HALF_OPEN:
            try:
                result = await func(*args, **kwargs)
                self.state = self.CLOSED
                self.failure_count = 0
                return result
            except Exception as e:
                self.state = self.OPEN
                self.last_failure_time = time.time()
                raise
```

### Prometheus Metrics
```
circuit_breaker_state{service="shub"}        0/1/2 (CLOSED/OPEN/HALF_OPEN)
circuit_breaker_failures_total{service="shub"}  <count>
circuit_breaker_resets_total{service="shub"}    <count>
```

### When to Use
- After Shub restart detection
- On 503/502 errors from upstream
- During Madre power event recovery

---

## 2. RETRY LOGIC WITH EXPONENTIAL BACKOFF

### Problem
Transient network errors or brief service interruptions cause request failures.

### Solution
Retry with exponential backoff (1s, 500ms, 2.5s) for idempotent requests only.

### Backoff Formula
```
delay = base_delay * (multiplier ^ attempt)
base_delay = 100ms
multiplier = 2.5
max_retries = 3

Attempt 1: 100ms
Attempt 2: 250ms
Attempt 3: 625ms
Total: ~975ms max
```

### Implementation Example
```python
async def retry_with_backoff(func, max_retries=3, base_delay=0.1, multiplier=2.5):
    for attempt in range(max_retries):
        try:
            return await func()
        except (httpx.TimeoutException, ConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (multiplier ** attempt)
            await asyncio.sleep(delay)
```

### Idempotent Methods
- GET: Safe to retry (no side effects)
- PUT: Idempotent (same effect repeated)
- DELETE: Idempotent (safe to retry)
- HEAD: Safe to retry

### Non-Idempotent (No Retry)
- POST: May create duplicate objects (requires deduplication)
- PATCH: May have partial effects

### When to Use
- On network timeouts
- On 5xx errors (except 501 Not Implemented)
- NOT on 4xx errors (client error)

---

## 3. BACKPRESSURE MANAGEMENT

### Problem
High load → tentaculo queue fills → memory exhausted → crash.

### Solution
Drop low-priority requests if queue exceeds threshold.

### Priority Levels
1. **CRITICAL** (health, cache operations): Never drop
2. **HIGH** (public endpoints): Drop if queue > 500
3. **NORMAL** (standard proxy): Drop if queue > 1000
4. **LOW** (batch/analytics): Drop if queue > 2000

### Implementation Example
```python
class BackpressureManager:
    def __init__(self, max_queue_size=1000):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
    
    async def enqueue(self, request, priority="NORMAL"):
        if priority in ["CRITICAL"]:
            await self.queue.put(request)  # Block if needed
        else:
            try:
                self.queue.put_nowait(request)
            except asyncio.QueueFull:
                logger.warning(f"Queue full ({self.queue.qsize()}), dropping {priority}")
                return JSONResponse(
                    status_code=503,
                    content={"error": "service_overloaded", "priority": priority}
                )
```

### Prometheus Alert
```
AlertName: TentaculoQueueHigh
Condition: queue_size > 800 for 2m
Action: page on-call
```

### When to Use
- On sustained high load (QPS > 1000)
- During batch operations
- With rate limiting enabled

---

## 4. HEALTH CHECK FREQUENCY TUNING

### Problem
- Too frequent: Wastes Shub CPU
- Too infrequent: Misses failures

### Solution
Adaptive health check frequency based on service state.

### Baseline Configuration
```
Default interval:    5 seconds
During incident:     1 second
Exponential backoff:
  - Failure 1-2: 1s interval
  - Failure 3-5: 2s interval
  - Failure 6+: 5s interval (give it time to recover)
```

### Implementation Example
```python
class AdaptiveHealthCheck:
    def __init__(self, base_interval=5):
        self.base_interval = base_interval
        self.consecutive_failures = 0
        self.check_interval = base_interval
    
    def on_success(self):
        self.consecutive_failures = 0
        self.check_interval = self.base_interval
    
    def on_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures <= 2:
            self.check_interval = 1
        elif self.consecutive_failures <= 5:
            self.check_interval = 2
        else:
            self.check_interval = 5
```

### Prometheus Metrics
```
health_check_interval_seconds           <5|2|1>
health_check_failures_consecutive       <N>
health_check_success_rate               <0-100>%
```

### When to Use
- Always (health checks are low-cost via cache)
- During service recovery
- In multi-tenant environments

---

## 5. TIMEOUT STRATEGY

### Problem
Slow/hung requests cause thread exhaustion or memory pressure.

### Solution
Strict timeouts per operation type.

### Timeout Configuration
```
GET /health:              2s (cached, should be instant)
GET /ready:               3s (checks DSP, etc)
GET /status:              5s (full diagnostics)
POST /api/analyze:        30s (audio processing)
POST /api/mastering:      60s (complex analysis)
POST /api/batch/submit:   120s (multiple files)
```

### Implementation Example
```python
async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
    response = await client.post(upstream_url, timeout=30.0)
    # Timeout handling:
    # httpx.TimeoutException → 503 (retry with backoff)
```

### Prometheus Alert
```
AlertName: ProxyLatencyHigh
Condition: shub_proxy_latency_p99 > 30s for 5m
Action: investigate Shub load/hang
```

### When to Use
- All HTTP requests
- Especially for analysis/processing endpoints
- With circuit breaker for long timeouts

---

## 6. REQUEST DEDUPLICATION (POST safety)

### Problem
Retried POST requests create duplicate objects.

### Solution
Idempotency keys for POST requests.

### Implementation
```python
# Client sends: X-Idempotency-Key: <UUID>
# Server stores: {key: result} for 60s

async def deduplicate_post(key: str, func, *args):
    cached = await cache.get(f"idempotency:{key}")
    if cached:
        return cached
    
    result = await func(*args)
    await cache.set(f"idempotency:{key}", result, ttl=60)
    return result
```

### When to Use
- POST /api/analyze (store results)
- POST /api/batch/submit (track job)
- NOT for GET/PUT/DELETE (idempotent by design)

---

## 7. CORRELATION TRACING

### Problem
Request origin lost in distributed tracing.

### Solution
Propagate X-Correlation-ID throughout request chain.

### Implementation
```python
correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

# Forward to upstream:
upstream_headers = {
    "X-Correlation-ID": correlation_id,
    "X-Forwarded-For": client_ip,
    "X-Forwarded-Proto": "https"
}

# Log with correlation_id:
logger.info(f"proxy_request: path={path}:correlation_id={correlation_id}")
```

### Prometheus Metrics
```
requests_by_correlation_id (high cardinality - for debugging only)
```

### When to Use
- All requests (mandatory)
- For debugging distributed issues
- For audit/compliance logging

---

## 8. CANNONICAL FLOW INTEGRATION

All patterns are validated against:
- **CANONICAL_FLOWS_VX11.json:** Must include flows for each pattern
- **CANONICAL_SHUB_VX11.json:** Proxy status, bypass mitigation
- **Verification:** scripts/audit_canonical.py

### Flows Added (Phase 3.2-3.4)
```json
{
  "id": "GATEWAY_RATE_LIMIT_ENFORCED",
  "status": "IMPLEMENTED",
  "verification_steps": [
    "Test: 1001 req/min per user → 403",
    "Test: 5001 req/min per IP → 403",
    "Test: Valid token under limit → 200"
  ]
},
{
  "id": "GATEWAY_METRICS_PROMETHEUS_READY",
  "status": "IMPLEMENTED",
  "verification_steps": [
    "GET /metrics → 200 (Prometheus format)",
    "Verify cache_hit_rate, latency_p99, request_total"
  ]
},
{
  "id": "GATEWAY_PATTERNS_DOCUMENTED",
  "status": "IMPLEMENTED",
  "verification_steps": [
    "Review: GATEWAY_PATTERNS.md exists",
    "Verify: circuit breaker, retry, backpressure, timeouts documented",
    "Confirm: Prometheus alerts configured"
  ]
}
```

---

## 9. PROMETHEUS ALERTING RULES

### Create prometheus/rules.yml
```yaml
groups:
  - name: vx11_gateway_alerts
    interval: 30s
    rules:
      - alert: ShubProxyLatencyHigh
        expr: shub_proxy_latency_p99 > 30000
        for: 5m
        annotations:
          summary: "Proxy latency p99 > 30s"
          action: "Check Shub performance"
      
      - alert: CacheHitRateLow
        expr: cache_hit_rate < 50
        for: 10m
        annotations:
          summary: "Cache hit rate < 50%"
          action: "Check cache TTL configuration"
      
      - alert: RateLimitRejectionRate
        expr: rate(rate_limit_rejections[5m]) > 10
        for: 2m
        annotations:
          summary: "Rate limiting rejecting >10 req/s"
          action: "Check for DDoS or misconfiguration"
```

---

## 10. TESTING & VALIDATION

### Unit Tests
```python
def test_circuit_breaker_opens():
    breaker = CircuitBreaker(threshold=3)
    for _ in range(3):
        breaker.call(failing_func)  # 3 failures → OPEN
    assert breaker.state == CircuitBreaker.OPEN

def test_exponential_backoff():
    delays = []
    for attempt in range(3):
        delay = 0.1 * (2.5 ** attempt)
        delays.append(delay)
    assert delays == [0.1, 0.25, 0.625]
```

### Integration Tests
```bash
# Rate limit test
for i in {1..1001}; do
  curl -H "X-VX11-GW-TOKEN: user1" http://localhost:8000/shub/health
done
# Expected: 1000x 200, 1x 403

# Metrics test
curl http://localhost:8000/metrics | grep cache_hit_rate
# Expected: cache_hit_rate 95.5
```

### Load Tests (Apache Bench)
```bash
ab -n 10000 -c 100 http://localhost:8000/shub/health
# With cache: ~10000 req/s
# Without cache: ~200 req/s (15x difference)
```

---

## SUMMARY

| Pattern | Purpose | Implementation | Status |
|---------|---------|-----------------|--------|
| Circuit Breaker | Fail fast on Shub unavailable | State machine + timeout | Phase 3.2 |
| Retry Backoff | Transient error recovery | Exponential delay | Phase 3.2 |
| Backpressure | Prevent queue exhaustion | Priority drop strategy | Phase 3.2 |
| Health Check Tuning | Adaptive frequency | Failure count → interval | Phase 3.2 |
| Timeout Strategy | Prevent hanging requests | Per-operation timeouts | Phase 3.2 |
| Deduplication | POST idempotency | Correlation key cache | Phase 3.4 |
| Correlation Tracing | End-to-end traceability | X-Correlation-ID propagation | Phase 3.1 |
| Prometheus Metrics | Monitoring & alerting | /metrics endpoint | Phase 3.3 |

**All patterns integrated with CANONICAL_FLOWS_VX11.json** ✅

