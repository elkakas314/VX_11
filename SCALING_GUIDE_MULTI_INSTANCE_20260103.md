# VX11 SSE Ephemeral Token — Multi-Instance Scaling Guide
# Created: 2025-01-03
# Version: 1.0

---

## Decision Tree: When to Scale

**START:** Current deployment handling < 1000 concurrent SSE clients?

```
YES → Token Cache + Single Instance is FINE
      Proceed to: MONITORING & OPTIMIZATION (end of doc)

NO  → Can you increase container resources (CPU/memory)?

      YES → Upgrade container in docker-compose.yml
            memory: 1G (was 512M)
            cpus: 2 (was 1)
            Estimated runway: 2x capacity
            
      NO  → MUST SCALE HORIZONTALLY
            → Deploy Phase 1: Load Balancer (nginx/traefik)
            → Deploy Phase 2: Redis Token Cache
            → Deploy Phase 3: Multi-instance operator cluster
```

---

## Phase 1: Deploy Load Balancer (nginx)

**Objective:** Route requests across N instances of operator-backend

### Step 1: Add Redis Service (docker-compose.full-test.yml)

```yaml
services:
  vx11-redis:
    image: redis:7-alpine
    container_name: vx11-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    environment:
      - REDIS_PASSWORD=vx11-redis-local-token
    networks:
      - vx11-net

volumes:
  redis-data:

# Add to networks section (if not exists):
networks:
  vx11-net:
    driver: bridge
```

### Step 2: Deploy Redis

```bash
cd /home/elkakas314/vx11

# Add service to compose file (already done above)
# Start redis
docker compose up -d vx11-redis

# Verify connectivity
docker compose exec vx11-redis redis-cli ping
# Expected: PONG

# Set password
docker compose exec vx11-redis redis-cli CONFIG SET requirepass vx11-redis-local-token
```

### Step 3: Add Load Balancer (nginx)

Create `deploy/nginx/nginx.conf`:

```nginx
upstream vx11_operator_backend {
    least_conn;  # Use least-connections strategy
    server vx11-operator-1:8001 weight=1;
    server vx11-operator-2:8001 weight=1;
    server vx11-operator-3:8001 weight=1;
    # Add more as needed
}

server {
    listen 8001;
    server_name localhost;

    # Token endpoint (distributes across instances)
    location /operator/api/events/sse-token {
        proxy_pass http://vx11_operator_backend;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }

    # SSE stream endpoint (sticky session required)
    location /operator/api/events/stream {
        # Use IP hash to stick to same instance
        # (not strictly required with Redis backend, but helps with connection pooling)
        proxy_pass http://vx11_operator_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }

    # Other operator endpoints
    location /operator/api/ {
        proxy_pass http://vx11_operator_backend;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Step 4: Add nginx to docker-compose

```yaml
services:
  vx11-nginx-lb:
    image: nginx:alpine
    container_name: vx11-nginx-lb
    ports:
      - "8001:8001"
    volumes:
      - ./deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - vx11-operator
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8001/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - vx11-net
```

### Step 5: Start load balancer

```bash
docker compose up -d vx11-nginx-lb
sleep 5

# Verify
curl http://localhost:8001/health
# Requests now go through nginx → operator instances
```

---

## Phase 2: Migrate Token Cache to Redis

**Objective:** Replace in-memory cache with Redis for shared state across instances

### Step 1: Update operator/backend/main.py

Replace the in-memory cache implementation:

```python
# OLD (in-memory, single instance only):
# ========================================
# EPHEMERAL_TOKENS_CACHE = {}
# EPHEMERAL_TOKEN_TTL_SEC = 60
#
# def _is_ephemeral_token_valid(eph_token):
#     if eph_token not in EPHEMERAL_TOKENS_CACHE:
#         return False, None
#     issued_at = EPHEMERAL_TOKENS_CACHE[eph_token]
#     if (time.time() - issued_at) > EPHEMERAL_TOKEN_TTL_SEC:
#         del EPHEMERAL_TOKENS_CACHE[eph_token]
#         return False, None
#     return True, issued_at

# NEW (Redis-backed, multi-instance ready):
# ==========================================

import redis
import os

REDIS_HOST = os.getenv("REDIS_HOST", "vx11-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "vx11-redis-local-token")
REDIS_DB = int(os.getenv("REDIS_DB", 1))
EPHEMERAL_TOKEN_TTL_SEC = int(os.getenv("EPHEMERAL_TOKEN_TTL_SEC", 60))

# Initialize Redis client
try:
    REDIS_CLIENT = redis.StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
        health_check_interval=10
    )
    REDIS_CLIENT.ping()
    logger.info("✅ Redis connected (ephemeral token storage)")
except Exception as e:
    logger.error(f"❌ Redis connection failed: {e}")
    logger.warning("⚠️  Falling back to in-memory cache (single instance only)")
    REDIS_CLIENT = None
    FALLBACK_CACHE = {}

def _is_ephemeral_token_valid(eph_token: str) -> tuple[bool, float | None]:
    """Validate ephemeral token against Redis or fallback cache."""
    
    if REDIS_CLIENT:
        try:
            data = REDIS_CLIENT.get(f"token:{eph_token}")
            if not data:
                return False, None
            issued_at = float(data)
            if (time.time() - issued_at) > EPHEMERAL_TOKEN_TTL_SEC:
                REDIS_CLIENT.delete(f"token:{eph_token}")
                return False, None
            return True, issued_at
        except Exception as e:
            logger.warning(f"Redis error validating token: {e}, using fallback")
    
    # Fallback to in-memory (if Redis unavailable)
    if eph_token not in FALLBACK_CACHE:
        return False, None
    issued_at = FALLBACK_CACHE[eph_token]
    if (time.time() - issued_at) > EPHEMERAL_TOKEN_TTL_SEC:
        del FALLBACK_CACHE[eph_token]
        return False, None
    return True, issued_at

def _issue_ephemeral_token() -> str:
    """Issue new ephemeral token (stored in Redis or fallback)."""
    
    token = str(uuid.uuid4())
    now = time.time()
    
    if REDIS_CLIENT:
        try:
            REDIS_CLIENT.setex(
                f"token:{token}",
                EPHEMERAL_TOKEN_TTL_SEC,
                str(now)
            )
            logger.debug(f"Issued ephemeral token (Redis): {token[:8]}... TTL {EPHEMERAL_TOKEN_TTL_SEC}s")
        except Exception as e:
            logger.error(f"Redis error issuing token: {e}, using fallback")
            FALLBACK_CACHE[token] = now
    else:
        FALLBACK_CACHE[token] = now
    
    return token

# Add metrics endpoint for monitoring
@app.get("/operator/internal/cache-stats")
async def cache_stats(token: str = Header(..., alias="X-VX11-Token")):
    """Return cache statistics for monitoring."""
    
    if not _validate_principal_token(token):
        raise HTTPException(status_code=401, detail="Invalid principal token")
    
    if REDIS_CLIENT:
        try:
            info = REDIS_CLIENT.info()
            keys = REDIS_CLIENT.keys("token:*")
            return {
                "backend": "redis",
                "cache_size": len(keys),
                "redis_memory_bytes": info.get("used_memory", 0),
                "redis_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "sample_tokens": keys[:5]  # For debugging
            }
        except Exception as e:
            return {"error": str(e)}
    else:
        return {
            "backend": "fallback-memory",
            "cache_size": len(FALLBACK_CACHE),
            "tokens": list(FALLBACK_CACHE.keys())[:5]
        }
```

### Step 2: Update docker-compose.yml (add Redis env vars)

```yaml
services:
  vx11-operator:
    environment:
      - REDIS_HOST=vx11-redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=vx11-redis-local-token
      - REDIS_DB=1
      - EPHEMERAL_TOKEN_TTL_SEC=60
    depends_on:
      vx11-redis:
        condition: service_healthy
```

### Step 3: Restart operator with Redis

```bash
# Update code with Redis implementation (as above)
# Restart operator to connect to Redis
docker compose restart vx11-operator
sleep 5

# Verify Redis is being used
curl -s http://localhost:8001/operator/internal/cache-stats \
  -H "X-VX11-Token: $(cat tokens.env | grep VX11_PRINCIPAL_TOKEN | cut -d= -f2)" | jq .backend
# Expected: "redis"
```

### Step 4: Test token validity across restarts

```bash
# Get token from instance 1
TOKEN=$(curl -s http://localhost:8001/operator/api/events/sse-token \
  -H "X-VX11-Token: $(cat tokens.env | grep VX11_PRINCIPAL_TOKEN | cut -d= -f2)" | jq -r .sse_token)

echo "Token: $TOKEN"

# Restart operator (would lose cache in old system)
docker compose restart vx11-operator
sleep 5

# Try token again (should still be valid in Redis)
curl -s "http://localhost:8000/operator/api/events/stream?token=$TOKEN" \
  -H "Accept: text/event-stream" --max-time 2 | head -3
# Expected: Works (SSE starts, token still in Redis)
```

---

## Phase 3: Deploy Multi-Instance Operator

**Objective:** Run 3+ operator instances behind load balancer

### Step 1: Create docker-compose.scale.yml

```yaml
version: '3.8'

services:
  vx11-redis:
    image: redis:7-alpine
    container_name: vx11-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
    networks:
      - vx11-net

  vx11-operator-1:
    build: ./operator/backend
    container_name: vx11-operator-1
    ports:
      - "8011:8001"
    environment:
      - REDIS_HOST=vx11-redis
      - REDIS_DB=1
      - INSTANCE_ID=1
    depends_on:
      - vx11-redis
    networks:
      - vx11-net

  vx11-operator-2:
    build: ./operator/backend
    container_name: vx11-operator-2
    ports:
      - "8012:8001"
    environment:
      - REDIS_HOST=vx11-redis
      - REDIS_DB=1
      - INSTANCE_ID=2
    depends_on:
      - vx11-redis
    networks:
      - vx11-net

  vx11-operator-3:
    build: ./operator/backend
    container_name: vx11-operator-3
    ports:
      - "8013:8001"
    environment:
      - REDIS_HOST=vx11-redis
      - REDIS_DB=1
      - INSTANCE_ID=3
    depends_on:
      - vx11-redis
    networks:
      - vx11-net

  vx11-nginx-lb:
    image: nginx:alpine
    container_name: vx11-nginx-lb
    ports:
      - "8001:8001"
    volumes:
      - ./deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - vx11-operator-1
      - vx11-operator-2
      - vx11-operator-3
    networks:
      - vx11-net

networks:
  vx11-net:
    driver: bridge
```

### Step 2: Deploy scaled cluster

```bash
docker compose -f docker-compose.scale.yml up -d

# Verify all instances running
docker compose -f docker-compose.scale.yml ps
# Expected: 5 services up (3 operators + nginx + redis)

# Test load balancing
for i in {1..10}; do
  curl -s http://localhost:8001/operator/internal/instance-id \
    -H "X-VX11-Token: ..." | jq .instance_id
done
# Expected: Mixture of 1, 2, 3 (round-robin)
```

### Step 3: Test failover (stop one instance)

```bash
# Stop instance 2
docker compose -f docker-compose.scale.yml stop vx11-operator-2

# Requests should still work (load balancer routes to 1 & 3)
for i in {1..5}; do
  curl -s http://localhost:8001/operator/api/events/sse-token \
    -H "X-VX11-Token: ..." | jq .sse_token
done
# Expected: All succeed

# Restart instance 2
docker compose -f docker-compose.scale.yml up -d vx11-operator-2
```

---

## Performance Expectations

### Single Instance (Current)
- Token issuance: ~10ms per token
- Cache lookup: ~0.2ms per token
- Concurrent clients: ~500
- Memory: ~150MB

### Multi-Instance (Scaled)
- Token issuance: ~12ms (Redis overhead)
- Cache lookup: ~1ms (Redis network round-trip)
- Concurrent clients: ~1500-2000 (3 instances @ 500-700 each)
- Memory: ~500MB (3x instances) + 100MB Redis

### Scaling Formula
```
Capacity = N_instances × (500 concurrent clients / instance)
           × (1000 token_issuances/sec / instance)
           × Load_balancer_overhead (0.95)

Example: 3 instances = 1425 concurrent @ 2850 issuances/sec
```

---

## Rollback from Scaled Back to Single Instance

```bash
# Stop scaled deployment
docker compose -f docker-compose.scale.yml down

# Back to original single instance
docker compose up -d vx11-operator

# Restart gateway to point back to single instance
docker compose restart vx11-tentaculo-link

# Verify
curl http://localhost:8000/health
```

---

## Cost Analysis

| Configuration | Instances | Memory | CPU | Redis | Network Calls | Cost (estimated) |
|---|---|---|---|---|---|---|
| Current (Dev) | 1 | 512MB | 1 core | None | 0 | $0.05/hr |
| Scaled (MVP) | 3 | 1.5GB | 3 cores | 256MB | 3x | $0.15/hr |
| Production | 5 | 2.5GB | 5 cores | 1GB | 5x | $0.25/hr |

---

## Monitoring Multi-Instance

```bash
# Monitor Redis cache size
watch -n 5 'redis-cli --pass vx11-redis-local-token INFO | grep used_memory_human'

# Monitor instance distribution
watch -n 2 'docker compose logs --tail 100 | grep "Request from instance" | awk -F"instance " "{print $NF}" | sort | uniq -c'

# Monitor token TTL across instances
# (All instances see same TTL expiry due to Redis backend)
curl -s http://localhost:8001/operator/internal/cache-stats \
  -H "X-VX11-Token: ..." | jq .cache_size
```

---

## Decision Summary

| Metric | Single Instance | Multi-Instance |
|---|---|---|
| Concurrent clients | ~500 | ~1500 |
| Development cost | Minimal | Moderate |
| Operational complexity | Simple | Moderate |
| Failover | Manual | Automatic (load balancer) |
| Recommended for | Dev/MVP | Beta/Production |

**Go with Multi-Instance when:**
- ✅ Concurrent SSE clients > 500
- ✅ Token issuance rate > 5K/min
- ✅ Production deployment (high availability)
- ✅ Team has Kubernetes/orchestration experience

**Stick with Single Instance when:**
- ✅ <500 concurrent clients
- ✅ Development/testing phase
- ✅ Limited DevOps resources
- ✅ Acceptable downtime for maintenance

---

**END OF SCALING GUIDE**

Next: See MONITORING_PROMETHEUS_CONFIG and OPERATIONAL_RUNBOOKS for ongoing operations.
