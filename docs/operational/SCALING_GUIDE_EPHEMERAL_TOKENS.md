# SCALING GUIDE: EPHEMERAL TOKEN SYSTEM

**Scope:** Single instance → Multi-instance (load-balanced)  
**Challenge:** In-memory cache not shared across instances  
**Solution:** Redis-backed ephemeral token store

---

## Problem: Single vs Multi-Instance

### Single Instance (Current)
```
Client → Load Balancer → [Operator Backend (1 instance)]
                          ├─ Memory cache: {token1, token2, ...}
                          └─ Works fine: 1 cache, 1 truth source
```

**Status:** ✅ Works for < 1000 concurrent streams

### Multi-Instance (Future)
```
Client → Load Balancer
         ├─ [Operator Backend #1] — Memory cache: {token1, token2}
         ├─ [Operator Backend #2] — Memory cache: {token3, token4}
         └─ [Operator Backend #3] — Memory cache: {token5, token6}

Problem: Client gets token from #1, LB routes SSE to #2 → 403 INVALID
```

**Status:** ❌ Fails without shared cache

---

## Solution 1: Sticky Session Routing (Simple, Limited)

### Implementation

**Nginx/Load Balancer Config:**
```nginx
upstream operator_backend {
    # Sticky session: route same client to same backend
    ip_hash;
    server backend1:8011;
    server backend2:8011;
    server backend3:8011;
}

server {
    location /operator/api/events/sse-token {
        proxy_pass http://operator_backend;
    }

    location /operator/api/events/stream {
        proxy_pass http://operator_backend;
        # MUST hit same backend as sse-token endpoint
    }
}
```

### Pros
- Simple to implement
- No external dependency (Redis)
- No network overhead

### Cons
- ❌ Uneven load distribution (some backends hot, some cold)
- ❌ Fails if backend crashes (client token orphaned)
- ❌ Difficult scaling (adding new backend rebalances existing)
- ❌ Can't do graceful rolling restarts

**Recommendation:** ⚠️ Temporary only, not production-ready

---

## Solution 2: Redis-Backed Cache (Recommended)

### Architecture

```
Client → Load Balancer → [Backend #1, #2, #3]
                         ├─ Backend #1 → Redis: SET token:uuid {...}
                         ├─ Backend #2 → Redis: GET token:uuid
                         └─ Backend #3 → Redis: DEL token:uuid (expired)
```

**All backends share ONE cache (Redis).**

### Implementation

#### Step 1: Add Redis to docker-compose

```yaml
# docker-compose.full-test.yml (already present)
redis-test:
  image: redis:7-alpine
  container_name: vx11-redis-test
  environment:
    - REDIS_APPENDONLY=yes
  volumes:
    - redis-data-test:/data
  networks:
    - vx11-test
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5
```

#### Step 2: Update Backend Code

**File:** `operator/backend/main.py`

Replace in-memory cache with Redis:

```python
import redis
import json
import os

# Initialize Redis client
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

EPHEMERAL_TOKEN_KEY_PREFIX = "vx11:ephemeral_token:"
EPHEMERAL_TOKEN_TTL_SEC = 60

def create_ephemeral_token() -> str:
    """Create and store ephemeral token in Redis."""
    ephemeral_token = str(uuid.uuid4())
    token_data = {
        "created_at": time.time(),
        "ttl_sec": EPHEMERAL_TOKEN_TTL_SEC,
    }
    
    # Store in Redis with TTL
    redis_key = f"{EPHEMERAL_TOKEN_KEY_PREFIX}{ephemeral_token}"
    redis_client.setex(
        redis_key,
        EPHEMERAL_TOKEN_TTL_SEC,
        json.dumps(token_data)
    )
    
    return ephemeral_token

def _is_ephemeral_token_valid(eph_token: str) -> bool:
    """Check if ephemeral token is valid (in Redis)."""
    redis_key = f"{EPHEMERAL_TOKEN_KEY_PREFIX}{eph_token}"
    token_data = redis_client.get(redis_key)
    
    if not token_data:
        return False
    
    # Redis TTL automatically cleans up (no manual delete needed)
    return True

@app.post("/operator/api/events/sse-token")
async def get_sse_token(
    correlation_id: str = Depends(get_correlation_id),
    _: bool = Depends(token_guard),
) -> SSETokenResponse:
    """Issue ephemeral SSE token via Redis."""
    ephemeral_token = create_ephemeral_token()
    
    return SSETokenResponse(
        sse_token=ephemeral_token,
        expires_in_sec=EPHEMERAL_TOKEN_TTL_SEC,
    )
```

#### Step 3: Environment Variables

```bash
# .env or docker-compose environment
REDIS_URL=redis://redis-test:6379
VX11_OPERATOR_REDIS_DB=0  # Separate DB from other services
```

#### Step 4: Docker Compose Update

```yaml
services:
  operator-backend:
    environment:
      - REDIS_URL=redis://redis-test:6379
      - REDIS_DB=1  # Separate namespace
    depends_on:
      redis-test:
        condition: service_healthy
```

### Deployment Steps

1. **Update code (backend):**
   ```bash
   cd operator && git pull origin feature/redis-ephemeral-cache
   ```

2. **Deploy Redis (if not present):**
   ```bash
   docker compose -f docker-compose.full-test.yml up -d redis-test
   ```

3. **Restart backends (one by one):**
   ```bash
   docker compose -f docker-compose.full-test.yml restart operator-backend
   # Repeat for each instance
   ```

4. **Verify:**
   ```bash
   # Test that cache works across instances
   TOKEN=$(curl -s -X POST -H "X-VX11-Token: vx11-test-token" \
     http://backend1:8011/operator/api/events/sse-token | jq -r '.sse_token')
   
   # Verify same token works on backend2
   curl -s "http://backend2:8011/operator/api/events/stream?token=$TOKEN" | head -1
   # Should return HTTP 200, not 403
   ```

---

## Solution 3: Hybrid Approach (Advanced)

### Problem with Pure Redis

- Network latency on every token check
- Redis becomes single point of failure
- Need Redis HA/clustering for production

### Hybrid Solution

```
Local Cache (TTL: 5s)  +  Redis Backup (TTL: 60s)

Backend Instance:
1. Check local memory (fast, < 1ms)
2. If miss, check Redis (fallback, < 10ms)
3. Always write to Redis (for other instances)
```

**Benefits:**
- ✅ 90% requests served from memory (fast)
- ✅ 10% fallback to Redis (cross-instance)
- ✅ Redis failure doesn't break existing tokens

**Implementation:**

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Local TTL cache (5s)
LOCAL_CACHE = {}
LOCAL_CACHE_TTL = 5

def _is_ephemeral_token_valid(eph_token: str) -> bool:
    """Check token in: local cache → Redis → invalid."""
    
    # Check local cache first (< 1ms)
    if eph_token in LOCAL_CACHE:
        if LOCAL_CACHE[eph_token]['expires_at'] > time.time():
            return True
        else:
            del LOCAL_CACHE[eph_token]
    
    # Check Redis (fallback, < 10ms)
    redis_key = f"{EPHEMERAL_TOKEN_KEY_PREFIX}{eph_token}"
    token_data = redis_client.get(redis_key)
    
    if token_data:
        # Cache locally for 5s
        LOCAL_CACHE[eph_token] = {
            'data': json.loads(token_data),
            'expires_at': time.time() + LOCAL_CACHE_TTL
        }
        return True
    
    return False

def create_ephemeral_token() -> str:
    """Create token, store in both local and Redis."""
    ephemeral_token = str(uuid.uuid4())
    token_data = {
        "created_at": time.time(),
        "ttl_sec": EPHEMERAL_TOKEN_TTL_SEC,
    }
    
    # Store locally
    LOCAL_CACHE[ephemeral_token] = {
        'data': token_data,
        'expires_at': time.time() + LOCAL_CACHE_TTL
    }
    
    # Store in Redis (60s TTL)
    redis_key = f"{EPHEMERAL_TOKEN_KEY_PREFIX}{ephemeral_token}"
    redis_client.setex(
        redis_key,
        EPHEMERAL_TOKEN_TTL_SEC,
        json.dumps(token_data)
    )
    
    return ephemeral_token
```

---

## Capacity Planning

### Single Instance
- **Tokens/sec:** 100 (comfortable)
- **Cache size:** < 100 tokens (60s TTL, sparse usage)
- **Memory:** < 1MB
- **Concurrent SSE streams:** 1000+

### Multi-Instance (3x)
- **Total tokens/sec:** 300 (3 × 100)
- **Per-instance:** 100 tokens/sec
- **Redis memory:** < 10MB (100 tokens × 100KB each)
- **Concurrent SSE streams:** 3000+

### Multi-Instance (10x with Redis)
- **Total tokens/sec:** 1000+
- **Per-instance:** 100 tokens/sec
- **Redis memory:** < 50MB
- **Redis throughput:** < 10% utilization (easily handles)
- **Concurrent SSE streams:** 10,000+

---

## Monitoring Redis Cache

### Prometheus Queries

```promql
# Redis memory usage
redis_memory_used_bytes / (1024 * 1024)

# Redis commands/sec
rate(redis_commands_processed_total[1m])

# Ephemeral token hits (from hybrid cache)
rate(vx11_ephemeral_token_cache_local_hits[1m])

# Ephemeral token misses (fallback to Redis)
rate(vx11_ephemeral_token_cache_local_misses[1m])
```

### Alerts

```yaml
- alert: RedisDown
  expr: up{job="redis"} == 0
  for: 1m
  labels:
    severity: critical

- alert: RedisHighMemory
  expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.8
  for: 5m
  labels:
    severity: warning
```

---

## Rollback Plan

If Redis implementation has issues:

```bash
# Revert to single-instance
1. Stop scaling operations
2. Revert backend code: git revert <commit>
3. Restart backends
4. Clients will fall back to sticky session routing
5. Monitor for errors
```

---

## Production Checklist

- [ ] Redis HA configured (3+ nodes, sentinel)
- [ ] Redis backups enabled (snapshots)
- [ ] Redis monitoring (Prometheus exporter)
- [ ] Load balancer configured (round-robin)
- [ ] Sticky session removed (no longer needed)
- [ ] Health checks configured per instance
- [ ] Graceful shutdown hooks added
- [ ] Chaos engineering tests done (kill Redis, kill backend)
- [ ] Load testing (1000+ concurrent streams)
- [ ] Runbooks updated (Redis failure scenario)

---

## References

- [Redis Documentation](https://redis.io/documentation)
- [Redis Sentinel (HA)](https://redis.io/docs/management/sentinel/)
- [Docker Redis Image](https://hub.docker.com/_/redis)
- [Prometheus Redis Exporter](https://github.com/oliver006/redis_exporter)

---
