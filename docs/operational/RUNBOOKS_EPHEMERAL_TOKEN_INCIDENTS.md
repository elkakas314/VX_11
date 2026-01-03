# OPERATIONAL RUNBOOKS — EPHEMERAL SSE TOKEN SYSTEM

**Emergency Contact:** On-call engineer  
**Escalation:** Platform team lead  
**Last Updated:** 2026-01-03

---

## RUNBOOK 1: High Token Request Rate

**Alert:** `HighEphemeralTokenRequestRate` triggered  
**Symptom:** > 100 tokens/sec issued  
**Impact:** Memory pressure, possible DDoS or client loop

### Step 1: Assess Severity (1 min)
```bash
# Check current rate
curl -s http://localhost:9090/api/v1/query \
  'rate(vx11_operator_ephemeral_tokens_issued_total[5m])'

# Check active cache size
curl -s http://localhost:9090/api/v1/query \
  'vx11_operator_ephemeral_tokens_active'
```

**GO TO:** If cache > 1000 → **CRITICAL**, go to Step 3  
**GO TO:** If cache < 500 → **INFO**, go to Step 2

### Step 2: Investigate Root Cause (5-10 min)

**Check 1: Client error loop**
```bash
# SSH to operator-backend container
docker exec vx11-operator-backend-test tail -100 /app/logs/*.log | grep -i "error\|failed" | tail -20

# Look for: "auth_required", "invalid_token", "OFF_BY_POLICY"
# If found: clients repeatedly requesting tokens (fix client code)
```

**Check 2: Load spike**
```bash
# Monitor SSE stream count
curl -s http://localhost:9090/api/v1/query \
  'rate(vx11_operator_sse_connections_ephemeral_total[1m])'

# If spiked: likely legitimate traffic spike (scaling needed)
```

**Check 3: Monitoring alert itself**
```bash
# Verify no false positive
curl -s http://localhost:8011/operator/api/health | jq '.ephemeral_token_cache_size'

# If < 500: false positive, dismiss alert
```

### Step 3: Mitigation (Immediate)

**Option A: Increase token TTL (if legitimate spike)**
```python
# In operator/backend/main.py
EPHEMERAL_TOKEN_TTL_SEC = 120  # Increased from 60 to 120 seconds
# Reduces issuance frequency, but increases query string exposure window
# ⚠️ Use only temporarily!
```

**Option B: Enable rate limiting**
```python
# Add to operator/backend/main.py
RATE_LIMIT_TOKENS_PER_MIN = 1000  # Reject if > limit

if rate_limit_check() > RATE_LIMIT_TOKENS_PER_MIN:
    raise HTTPException(429, "rate_limit_exceeded")
```

**Option C: Restart with cache clear** (nuclear option)
```bash
docker compose -f docker-compose.full-test.yml restart operator-backend
# Clears in-memory cache, resets counters
# 30-60s downtime
```

### Step 4: Post-Incident

1. Review client logs (why requesting so many tokens?)
2. Update frontend code if needed
3. Deploy fix
4. Monitor for 30 min
5. Document incident in wiki

---

## RUNBOOK 2: Cache Size Anomaly

**Alert:** `UnusuallyHighCacheSize` triggered  
**Symptom:** > 500 active tokens in cache  
**Impact:** Possible memory leak, TTL misconfiguration, or attack

### Diagnosis

```bash
# Check cache size
curl -s http://localhost:9090/api/v1/query \
  'vx11_operator_ephemeral_tokens_active'

# Check expiry rate
curl -s http://localhost:9090/api/v1/query \
  'rate(vx11_operator_ephemeral_tokens_expired_total[5m])'

# If expiry rate low: tokens not being cleaned up (BUG)
# If expiry rate high: normal (tokens issued > tokens expired)
```

### Solution

**If TTL not working:**
```python
# Verify in operator/backend/main.py
def _is_ephemeral_token_valid(eph_token: str) -> bool:
    if eph_token not in EPHEMERAL_TOKENS_CACHE:
        return False
    token_data = EPHEMERAL_TOKENS_CACHE[eph_token]
    created_at = token_data.get("created_at", 0)
    ttl_sec = token_data.get("ttl_sec", EPHEMERAL_TOKEN_TTL_SEC)
    if time.time() - created_at > ttl_sec:
        del EPHEMERAL_TOKENS_CACHE[eph_token]  # ← This must execute
        return False
    return True
```

**If bug found:**
1. Deploy fix
2. Restart backend (clear cache)
3. Monitor for 1h

---

## RUNBOOK 3: Token Validation Failures

**Alert:** `HighTokenValidationFailureRate` triggered  
**Symptom:** > 10 validation failures/sec  
**Impact:** Clients can't connect to SSE streams, 403 errors

### Quick Diagnosis

```bash
# Check failure rate
curl -s http://localhost:9090/api/v1/query \
  'rate(vx11_operator_ephemeral_tokens_invalid_total[1m])'

# Get backend logs
docker exec vx11-operator-backend-test tail -50 /app/logs/*.log | grep "MISMATCH"
```

### Root Causes & Solutions

**Cause 1: Token not getting to backend**
```bash
# Check: Is gateway proxy enabled?
curl http://localhost:8000/operator/api/events/sse-token -H "X-VX11-Token: test" | jq .
# If response: OK
# If error: proxy disabled or backend unreachable
```

**Cause 2: Token cache not synchronized (multi-instance)**
```bash
# If multi-instance, need shared cache
# Solution: Use Redis
# See: docs/operational/SCALING_GUIDE.md
```

**Cause 3: Token endpoint not found**
```bash
# Verify endpoint exists
curl -s http://localhost:8011/operator/api/events/sse-token \
  -H "X-VX11-Token: vx11-test-token" | jq '.'

# If 404: backend not updated, redeploy
```

### Emergency Response

**Temporary fix (1h max):**
```python
# Disable ephemeral token requirement (revert to principal)
# In operator/backend/main.py

def check_sse_auth(...):
    if settings.enable_auth:
        provided_token = x_vx11_token or token
        # TEMPORARY: Accept ANY token for debugging
        if provided_token:
            return True  # ← Bypass validation for emergency
        raise HTTPException(401, "auth_required")
```

Then:
1. Deploy emergency fix
2. Monitor success rate
3. Investigate real cause
4. Deploy permanent fix
5. Revert emergency code

---

## RUNBOOK 4: Principal Token Fallback Usage

**Alert:** `HighPrincipalTokenUsageInSSE` triggered  
**Symptom:** Clients using principal tokens (old path) instead of ephemeral  
**Impact:** Increased security exposure, clients not upgraded

### Investigation

```bash
# Check split
curl -s http://localhost:9090/api/v1/query \
  'vx11_operator_sse_connections_principal_total'
curl -s http://localhost:9090/api/v1/query \
  'vx11_operator_sse_connections_ephemeral_total'

# Calculate ratio
ephemeral_pct = ephemeral / (ephemeral + principal) * 100
```

### Check Client Readiness

**Browser Console (for web clients):**
```javascript
// In browser DevTools console
// Check if EventsPanel is using new endpoint

// OLD (should NOT see)
new EventSource('/operator/api/events/stream?token=vx11-test-token')

// NEW (should see)
fetch('/operator/api/events/sse-token', ...)  // ← Get ephemeral token
new EventSource('/operator/api/events/stream?token=<ephemeral>')
```

### Action Plan

1. **Check deployment:** Was new frontend code deployed?
   ```bash
   git log --oneline | head -5  # Check latest commits
   docker ps | grep frontend  # Check image version
   ```

2. **Monitor adoption:** Give 24h for clients to reconnect
   ```bash
   # Run daily check
   watch -n 3600 'curl http://localhost:9090/api/v1/query \
     "vx11_operator_sse_connections_ephemeral_total"'
   ```

3. **If still low after 24h:** Force client refresh
   ```bash
   # Option A: Invalidate old token in auth system
   # Option B: Deploy to browser (service worker update)
   # Option C: Send push notification to users
   ```

---

## RUNBOOK 5: SSE Stream Connection Failures

**Symptom:** Clients see "401 Unauthorized" or "403 Forbidden"  
**Impact:** EventsPanel shows "Connection lost" error

### Debugging

**Step 1: Verify endpoint is accessible**
```bash
# Test ephemeral token endpoint
curl -i -X POST \
  -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/events/sse-token

# Expected: 200 OK + {"sse_token": "..."}
```

**Step 2: Test SSE stream with ephemeral token**
```bash
# Get ephemeral token
TOKEN=$(curl -s -X POST \
  -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/events/sse-token | jq -r '.sse_token')

# Try SSE stream
timeout 2 curl -v \
  "http://localhost:8000/operator/api/events/stream?token=$TOKEN&follow=true" \
  2>&1 | grep -E "(HTTP|event:|data:|retry:)" | head -20

# Expected: HTTP/1.1 200 OK + event markers
```

**Step 3: Check gateway logs**
```bash
docker logs vx11-tentaculo-link-test | tail -50 | grep -E "(STREAM_PROXY|error)"
```

### Common Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Proxy disabled | 404 Not Found | Set `VX11_OPERATOR_PROXY_ENABLED=1` |
| Backend down | Connection refused | `docker restart vx11-operator-backend-test` |
| Token expired (> 60s) | 403 invalid_token | Request fresh token (auto-handled by frontend) |
| Gateway not forwarding token | 401 auth_required | Check middleware code |

---

## ESCALATION PATH

```
Incident Severity Assessment
├─ P3 (Info): Alert fires but < 5% impact
│  └─ Action: Monitor, no immediate response needed
├─ P2 (Warning): > 5% but < 50% impact
│  └─ Action: Run runbook, notify team
└─ P1 (Critical): > 50% impact or service down
   └─ Action: PAGE ON-CALL, run runbook, escalate to platform lead
```

---

## Quick Commands Reference

```bash
# Check system health
curl http://localhost:8000/health
curl http://localhost:8011/operator/api/health

# Test flow (E2E)
TOKEN=$(curl -s -X POST -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/events/sse-token | jq -r '.sse_token')
timeout 2 curl http://localhost:8000/operator/api/events/stream?token=$TOKEN 2>&1 | head -10

# View metrics
curl http://localhost:9090/api/v1/query?query=up

# Container restart
docker compose -f docker-compose.full-test.yml restart operator-backend

# View backend logs
docker logs -f vx11-operator-backend-test | grep "SSE\|ephemeral"
```

---

## Contact & Escalation

- **On-call:** Slack #vx11-incidents
- **Platform Lead:** Internal Slack or email
- **Docs:** https://wiki.internal/vx11/ephemeral-tokens
- **Code:** https://github.com/elkakas314/VX_11

---
