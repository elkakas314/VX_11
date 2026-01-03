# VX11 SSE Ephemeral Token — Operational Runbooks
# Created: 2025-01-03
# Version: 1.0
# Usage: Keep these nearby during deployments and incidents

---

## RUNBOOK 1: SSE Endpoint Returning 403 Forbidden

**Symptom:** Browser console shows `GET /operator/api/events/stream?token=... 403 Forbidden`

**Root Cause Analysis:**
```
[ ] Token expired (>60 seconds old)
[ ] Token never issued (client skipped sse-token endpoint)
[ ] Gateway rejecting token (validation issue)
[ ] Token cache cleaned but backend still enforced validation
```

### Diagnosis Steps

**Step 1: Verify token TTL is configured correctly**
```bash
docker exec vx11-operator grep "EPHEMERAL_TOKEN_TTL_SEC" operator/backend/main.py
# Expected: EPHEMERAL_TOKEN_TTL_SEC = 60
```

**Step 2: Check if token was recently issued**
```bash
# Get a fresh token
TOKEN=$(curl -s http://localhost:8001/operator/api/events/sse-token \
  -H "X-VX11-Token: $(cat tokens.env | grep VX11_PRINCIPAL_TOKEN | cut -d= -f2)" \
  -H "Content-Type: application/json" | jq -r .sse_token)

echo "Token: $TOKEN"

# Try immediately (should work)
curl -s "http://localhost:8000/operator/api/events/stream?token=$TOKEN" \
  -H "Accept: text/event-stream" --max-time 2
# Expected: Returns "event: message" lines (not 403)
```

**Step 3: Check if gateway is bypassing token validation for SSE**
```bash
# Review gateway logs for SSE endpoint handling
docker compose logs vx11-tentaculo-link | grep "events/stream" | tail -5

# Expected pattern: 
# "GET /operator/api/events/stream?token=*** Forwarding to operator:8001 (auth bypass)"
# OR
# "GET /operator/api/events/stream?token=*** 401 Unauthorized (gateway validation failed)"
```

**Step 4: Verify backend is accepting ephemeral tokens**
```bash
# Check if backend code has ephemeral token validation
docker exec vx11-operator grep -n "_is_ephemeral_token_valid" operator/backend/main.py | head -3
# Expected: 3+ matches (definition + calls)

# Check if decorator is applied to SSE endpoint
docker exec vx11-operator grep -B5 "events/stream" operator/backend/main.py | grep -E "check_sse_auth|Depends"
# Expected: @app.get("/operator/api/events/stream") with check_sse_auth dependency
```

### Resolution

**If token is too old (>60s):**
```bash
# Client needs to re-request token before SSE connect
# Add to client debugging:
console.log("Token age:", Date.now() - tokenIssuedAt, "ms");
if (tokenAge > 55000) { // Refresh 5s before expiry
  fetchNewToken();
}
```

**If gateway is rejecting token:**
```bash
# Verify gateway principal token matches operator
GATEWAY_TOKENS=$(docker exec vx11-tentaculo-link env | grep VALID_TOKENS)
OPERATOR_TOKEN=$(docker exec vx11-operator env | grep VX11_PRINCIPAL_TOKEN)

echo "Gateway VALID_TOKENS: $GATEWAY_TOKENS"
echo "Operator principal: $OPERATOR_TOKEN"
# Should match or at least principal should be in VALID_TOKENS
```

**If backend ephemeral validation is broken:**
```bash
# Restart operator (reloads code)
docker compose restart vx11-operator
sleep 5

# Re-test with fresh token
TOKEN=$(curl -s http://localhost:8001/operator/api/events/sse-token \
  -H "X-VX11-Token: ..." | jq -r .sse_token)
curl -s "http://localhost:8000/operator/api/events/stream?token=$TOKEN" \
  -H "Accept: text/event-stream" --max-time 2
```

**If issue persists after restart:**
```bash
# Last resort: Rollback to previous commit
cd /home/elkakas314/vx11
git reset --hard 769fcaf  # Previous working commit
docker compose restart vx11-operator vx11-tentaculo-link
curl http://localhost:8000/health  # Verify recovery

# Note: Will use long-lived tokens again (less secure)
```

---

## RUNBOOK 2: Token Cache Growing Unbounded (Memory Leak)

**Symptom:** `docker stats vx11-operator` shows memory increasing over time (e.g., 150MB → 500MB over 1 hour)

**Root Cause Analysis:**
```
[ ] TTL cleanup not working (tokens stay in cache forever)
[ ] Token issuance outpaces cleanup (more issued than expired)
[ ] Cache flush command not triggered
[ ] Duplicate tokens in cache (should be unique per UUID)
```

### Diagnosis Steps

**Step 1: Check current cache size**
```bash
# If internal stats endpoint exists:
curl -s http://localhost:8001/internal/cache-stats | jq .

# Expected output:
# {
#   "cache_size": 234,
#   "avg_age_sec": 32,
#   "oldest_token_sec": 59,
#   "cleanup_runs": 1234
# }

# If not, check process memory
docker stats vx11-operator --no-stream | tail -1 | awk '{print "Memory:", $6}'
```

**Step 2: Verify TTL cleanup is working**
```bash
# Issue 3 tokens, wait 70s, check if all are gone
TOKEN1=$(curl -s http://localhost:8001/operator/api/events/sse-token \
  -H "X-VX11-Token: ..." | jq -r .sse_token)
echo "Issued at $(date +%s): $TOKEN1"

sleep 70

# Try to use expired token (should fail)
curl -s "http://localhost:8000/operator/api/events/stream?token=$TOKEN1" \
  --max-time 2 -w "\nHTTP Status: %{http_code}\n"
# Expected: HTTP Status: 403 or 401 (token expired, not in cache)
```

**Step 3: Check token issuance rate**
```bash
# Count token requests in last 5 minutes
docker compose logs vx11-operator --since 5m | grep -c "POST /operator/api/events/sse-token"
# Let's say result is N

# Compare to expected: N should be < (issuance_rate_per_sec * 300)
# Typical: 1-5 tokens/sec = 300-1500 per 5 min

# If > 3000: Potential abuse or misconfigured clients
```

**Step 4: Check for cache corruption**
```bash
# Review operator logs for cache operations
docker compose logs vx11-operator --since 1h | grep -i "cache\|ephemeral" | tail -20

# Look for:
# - "Cache size: X entries" (should go up and down)
# - "Cleanup removed Y expired tokens" (should see cleanup logs)
# - "Cache integrity check..." (any errors?)
```

### Resolution

**If TTL cleanup isn't working (tokens stay 60+ seconds):**
```bash
# Check if cleanup thread/task is running
docker exec vx11-operator ps aux | grep python  # Should see operator process
docker compose logs vx11-operator | grep -i "cleanup scheduled\|reaper\|background" | head -5

# If cleanup isn't mentioned: Code may be missing cleanup task
# Restart might help if it's a zombie process
docker compose restart vx11-operator
sleep 5

# Verify cleanup is now working
docker compose logs vx11-operator | grep -i cleanup | head -3
```

**If issuance rate is too high (potential abuse):**
```bash
# Check IP addresses of high issuers
docker compose logs vx11-operator --since 1h | grep "sse-token" | awk -F'|' '{print $NF}' | sort | uniq -c | sort -rn | head -10

# If single IP/user: Contact them to batch token requests
# If distributed: Possible attack, implement rate limiting at gateway

# Temporary mitigation: Reduce token TTL (60s → 30s)
# Edit operator/backend/main.py: EPHEMERAL_TOKEN_TTL_SEC = 30
# Restart operator: docker compose restart vx11-operator
```

**If memory doesn't decrease after restart:**
```bash
# Check if it's Python process memory or container memory
docker exec vx11-operator ps aux | grep python | grep -v grep
# Note PID, check /proc/<PID>/status

# If memory stays high (not cache): Possible other leak in operator code
# Last resort: Scale to multi-instance with Redis backend

# For now: Increase container memory limit in docker-compose.yml
# Set memory: 1G (was 512M)
docker compose up -d vx11-operator
```

**Nuclear option: Clear cache immediately**
```bash
# If cache grows to >1GB, this emergency step clears it
docker compose down vx11-operator
sleep 3
docker compose up -d vx11-operator
sleep 5

# Cache is now empty, clients will need to re-request tokens
curl http://localhost:8001/operator/api/events/sse-token ...
```

---

## RUNBOOK 3: Deployment Rollback (Emergency)

**Symptom:** New version deployed but breaking 401s, performance issues, or crashes

**Time to Decision:** 5 minutes maximum after detection

### Quick Rollback (< 2 minutes)

**Option A: Revert to previous commit**
```bash
cd /home/elkakas314/vx11

# Show last 5 commits
git log --oneline -5
# Expected:
# e1fa49c docs(final): Complete execution...
# 769fcaf vx11: P1 security SSE ephemeral token
# ...

# Revert to previous known-good
git reset --hard 769fcaf
# or git revert e1fa49c --no-edit  (creates new commit, safer)

# Restart services
docker compose down
docker compose -f docker-compose.full-test.yml up -d

# Wait for services to be ready
sleep 10
curl http://localhost:8000/health | jq .status
# Expected: "ok"
```

**Option B: Disable new feature (keep running version)**
```bash
# If rollback is too slow, disable SSE ephemeral tokens
# This allows old principal-token-only mode to work

# Edit operator/backend/main.py:
# Comment out: EPHEMERAL_TOKENS_CACHE = {}
# Modify check_sse_auth() to skip ephemeral check:
#   if False:  # Disabled: ephemeral token support
#       ...

# Restart just the operator
docker compose restart vx11-operator
sleep 5

# Old clients will still work (fallback to principal token)
# SSE without ephemeral support will fail, but can fallback
curl http://localhost:8000/operator/api/events/stream \
  -H "Authorization: Bearer <principal>" \
  -H "Accept: text/event-stream"
# Should work (old behavior)
```

### Post-Rollback Checklist

```bash
[ ] Services are all running: docker ps | grep -c "Up"  # Should be 7+
[ ] Health check passes: curl http://localhost:8000/health
[ ] No error logs: docker compose logs | grep -i "error\|failed" | wc -l  # Should be <5
[ ] Database is OK: sqlite3 data/runtime/vx11.db "PRAGMA integrity_check;"
[ ] Git is on correct commit: git rev-parse HEAD
[ ] Users are restored to service: Monitor metrics for user reconnections

[ ] Document incident: Create docs/audit/INCIDENT_20250103_<HHmm>.txt
[ ] Notify team: #vx11-incidents channel
[ ] Schedule post-mortem: Meeting within 24h
```

### Prevention: How to Avoid Rollback

**Before Deployment:**
```bash
# 1. Run full test suite
pytest scripts/test_sse_ephemeral_token.py -v

# 2. Load test on staging (simulate 100 concurrent clients)
ab -n 1000 -c 100 http://staging:8001/operator/api/events/sse-token

# 3. Review code changes
git diff 769fcaf e1fa49c --stat  # Show files changed
git diff 769fcaf e1fa49c -- operator/backend/main.py | head -50  # Show diffs

# 4. Create canary deployment (1 instance, 5% traffic)
# (Requires load balancer, skip for single-instance)
```

---

## RUNBOOK 4: Service Recovery (General)

**Symptom:** "Service x is stuck/not responding"

### Universal Recovery Steps

**Step 1: Identify the affected service**
```bash
docker compose ps | grep -v Up
# Shows any services not running

# Get details
docker compose logs <service> --tail 50
```

**Step 2: Soft restart (try first)**
```bash
# Restart the service gracefully
docker compose restart <service>
sleep 5

# Verify
docker compose ps | grep <service> | grep Up
curl http://localhost:PORT/health  # Check service-specific health
```

**Step 3: Hard restart (if soft fails)**
```bash
# Stop and remove container
docker compose stop <service>
docker compose rm <service>
sleep 2

# Restart fresh
docker compose up -d <service>
sleep 10

# Verify
curl http://localhost:PORT/health
```

**Step 4: Full restart (nuclear option)**
```bash
# Stop all, clear caches, restart all
docker compose down
docker system prune -f  # Cleanup dangling images
sleep 5

docker compose -f docker-compose.full-test.yml up -d
sleep 15

# Verify all services
docker compose ps | grep -c "Up"  # Should be 7+
curl http://localhost:8000/health
```

### Prevention

```bash
# Monitor service health regularly
watch -n 5 'docker compose ps'

# Collect metrics hourly
docker stats vx11-operator >> logs/stats.log

# Alert on service down
# (Implement in monitoring tool, see MONITORING_PROMETHEUS_CONFIG)
```

---

## RUNBOOK 5: Security Incident (Token Abuse/Attack)

**Symptom:** Abnormally high token issuance rate (>1000/min) from specific IP

### Immediate Actions (< 5 min)

**Step 1: Block the attacker**
```bash
# Identify source IP
docker compose logs vx11-tentaculo-link | grep "sse-token" | grep -oP '\d+\.\d+\.\d+\.\d+' | sort | uniq -c | sort -rn | head

# Block at firewall (if available)
iptables -A INPUT -s <ATTACKER_IP> -j DROP  # or firewall rules

# Or block at nginx/gateway level (add to tentaculo_link/main_v7.py):
# BLOCKED_IPS = {'<ATTACKER_IP>', ...}
# if request.client.host in BLOCKED_IPS: return 403
```

**Step 2: Reduce token TTL (temporary)**
```bash
# Make tokens expire faster (e.g., 60s → 10s)
# Edit operator/backend/main.py:
# EPHEMERAL_TOKEN_TTL_SEC = 10

docker compose restart vx11-operator
```

**Step 3: Enable verbose logging**
```bash
# Capture all token requests for forensics
docker compose logs vx11-operator --follow | grep "sse-token" > /tmp/token-audit.log &

# Let run for 5 minutes to capture attack patterns
sleep 300
kill %1
```

### Investigation (Next 30 min)

```bash
# 1. Extract patterns from audit log
grep "sse-token" /tmp/token-audit.log | awk '{print $1, $NF}' | sort | uniq -c | sort -rn

# 2. Check if it's automated or manual
cat /tmp/token-audit.log | grep "User-Agent:" | sort | uniq -c

# 3. Document incident
cat > docs/audit/SECURITY_INCIDENT_20250103_<HHmm>.txt << EOF
  Time: $(date)
  Attack: Excessive token issuance (1000+/min)
  Source: <ATTACKER_IP>
  Pattern: <description>
  Actions taken: <block IP, reduce TTL, etc>
  Tokens valid during attack: 0 (expired too fast)
EOF
```

### Recovery

```bash
[ ] Restore normal TTL: EPHEMERAL_TOKEN_TTL_SEC = 60
[ ] Remove IP block (if false positive): iptables -D INPUT ...
[ ] Review token validation code for bypass
[ ] Deploy patch if vulnerability found
[ ] Notify security team
```

---

## RUNBOOK 6: Performance Degradation

**Symptom:** "SSE endpoint is slow (>500ms response time)"

### Diagnosis

```bash
# 1. Check if token endpoint is slow
time curl -s http://localhost:8001/operator/api/events/sse-token \
  -H "X-VX11-Token: ..." > /dev/null

# 2. Check system resources
docker stats vx11-operator --no-stream

# 3. Check database
sqlite3 data/runtime/vx11.db "PRAGMA quick_check;" 
# Expected: "ok" (should be instant)

# 4. Check for slow queries
docker compose logs vx11-operator | grep "duration=" | tail -10
```

### Mitigation

**If CPU is high (>80%):**
```bash
# Check what's running
docker top vx11-operator  # Show processes

# Possible causes:
# - Token validation loop (unlikely, <1ms per token)
# - Other endpoints under load
# - Garbage collection

# Solution: Scale to multi-instance or upgrade container resources
```

**If memory is high (>1GB):**
```bash
# Follow RUNBOOK 2 (Cache Memory Leak)
```

**If database is slow:**
```bash
# Run integrity check
sqlite3 data/runtime/vx11.db "PRAGMA integrity_check;"

# If fragmented, vacuum
sqlite3 data/runtime/vx11.db "VACUUM;"

# Restart operator to refresh connections
docker compose restart vx11-operator
```

---

## Quick Reference: Common Commands

```bash
# Health check all services
for svc in vx11-tentaculo-link vx11-operator vx11-operator-frontend; do
  echo -n "$svc: "
  curl -s http://localhost:8000/health 2>&1 | jq -r .status || echo "DOWN"
done

# Get fresh token
curl -s http://localhost:8001/operator/api/events/sse-token \
  -H "X-VX11-Token: $(grep VX11_PRINCIPAL_TOKEN tokens.env | cut -d= -f2)" | jq .sse_token

# Test SSE stream
curl -s "http://localhost:8000/operator/api/events/stream?token=<token>" \
  -H "Accept: text/event-stream" --max-time 5

# View real-time logs
docker compose logs -f vx11-operator | grep -E "token|auth|error|403"

# Restart all services
docker compose restart

# Emergency: Full reset
docker compose down && docker compose up -d

# View git history
git log --oneline -10

# Rollback to previous version
git reset --hard HEAD~1
```

---

**END OF RUNBOOKS**

Last updated: 2025-01-03
Maintained by: DevOps/SRE Team
Escalation: vx11-oncall@company.com
