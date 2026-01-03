# VX11 DEPLOYMENT QUICK REFERENCE — OPS TEAM CHEATSHEET

**Last Updated:** 2026-01-03 | **Status:** Production Ready | **Deployment Version:** P0 + P1

---

## 🚀 DEPLOYMENT IN 3 STEPS

```bash
# Step 1: Pre-flight checks (5 min)
cd /home/elkakas314/vx11
docker compose -f docker-compose.full-test.yml ps
docker compose -f docker-compose.full-test.yml logs --tail=20 tentaculo_link

# Step 2: Deploy (10 min)
docker compose -f docker-compose.full-test.yml pull
docker compose -f docker-compose.full-test.yml up -d

# Step 3: Verify (5 min)
curl -s http://localhost:8001/health | jq .
curl -s http://localhost:8000/health | jq .
```

---

## 🔍 QUICK DIAGNOSTICS

### SSE Token Endpoint Down?
```bash
# 1. Check backend health
curl -v http://localhost:8000/health
# Should return 200 OK

# 2. Check endpoint directly
curl -X POST http://localhost:8000/operator/api/events/sse-token \
  -H "X-VX11-Token: test-token"
# Should return: {"sse_token": "UUID", "expires_in_sec": 60, ...}

# 3. Check logs
docker compose -f docker-compose.full-test.yml logs operator-backend | tail -20
```

### 401 Unauthorized on SSE Stream?
```bash
# 1. Verify token is valid (< 60s old)
# 2. Check gateway proxy enabled
docker compose -f docker-compose.full-test.yml logs tentaculo_link | grep SSE
# Should show: "SSE bypass enabled" or "SSE proxy bypassed"

# 3. Verify EventSource URL has token
curl -v "http://localhost:8001/operator/api/events/stream?token=YOUR_TOKEN"
# Should get 200 and stream starts
```

### High Error Rate?
```bash
# 1. Check error logs
docker compose -f docker-compose.full-test.yml logs operator-backend | grep ERROR | tail -20

# 2. Check token cache size
curl -s http://localhost:8000/metrics | grep sse_token_cache_size

# 3. Check backend CPU/memory
docker stats vx11-operator-backend --no-stream

# 4. Restart if needed
docker compose -f docker-compose.full-test.yml restart operator-backend
```

---

## 📊 KEY MONITORING COMMANDS

```bash
# View all services
docker compose -f docker-compose.full-test.yml ps

# Real-time logs (follow)
docker compose -f docker-compose.full-test.yml logs -f --tail=50 operator-backend

# SSE token metrics
curl -s http://localhost:8000/metrics | grep sse_token

# Auth errors
docker compose -f docker-compose.full-test.yml logs operator-backend | grep -i auth | tail -10

# Performance
curl -s http://localhost:8000/metrics | grep latency
```

---

## ⚠️ INCIDENT RESPONSE FLOWCHART

```
User reports: "Can't connect to SSE events"
    ↓
[1] Check backend running?
    docker compose ps | grep operator-backend
    ✗ → docker compose restart operator-backend
    ✓ → [2]
    ↓
[2] Check token endpoint?
    curl -X POST http://localhost:8000/operator/api/events/sse-token \
      -H "X-VX11-Token: test"
    ✗ (500 error) → Restart backend + check logs
    ✗ (401 error) → Token validation issue → Check VALID_TOKENS
    ✓ → [3]
    ↓
[3] Check token is fresh (< 60s)?
    ✗ → Token expired, need new one
    ✓ → [4]
    ↓
[4] Check EventSource URL correct?
    curl -v "http://localhost:8001/operator/api/events/stream?token=TOKEN"
    ✗ (404) → Check gateway routing
    ✗ (403) → Token validation failed → Check token format
    ✓ → Works! User issue likely (browser cache, etc.)
```

---

## 🔐 SECURITY QUICK CHECKS

```bash
# 1. Verify no tokens in plaintext logs
docker compose -f docker-compose.full-test.yml logs | grep -v "token=\*\*\*" | grep "token=" | wc -l
# Should be 0 (all tokens sanitized)

# 2. Verify HTTPS only (check config)
grep -r "http://" operator/backend/main.py | grep -v "localhost"
# Should be 0 for production

# 3. Verify token TTL is 60s
grep "EPHEMERAL_TOKEN_TTL_SEC" operator/backend/main.py
# Should show: EPHEMERAL_TOKEN_TTL_SEC = 60

# 4. Check no hardcoded tokens
grep -r "token.*=" operator/ | grep -v "# " | grep -v ".env" | grep -v "test"
# Review manually
```

---

## 🔄 ROLLBACK (< 2 minutes)

```bash
# Option 1: Docker restart (fast)
docker compose -f docker-compose.full-test.yml restart operator-backend

# Option 2: Git rollback (full)
git log --oneline | head -5
# Find pre-deployment commit (3d83b60 is current ops docs)
git reset --hard <COMMIT_BEFORE_DEPLOY>
docker compose -f docker-compose.full-test.yml up -d --force-recreate

# Verify working
curl -s http://localhost:8000/health
```

---

## 📞 ESCALATION CONTACTS

| Issue | Contact | Channel |
|-------|---------|---------|
| Backend 500 errors | Backend Team Lead | #vx11-incidents |
| Gateway issues | Gateway Owner | #vx11-incidents |
| Frontend problems | Frontend Lead | #vx11-frontend-issues |
| Database errors | DBA | #vx11-data-issues |
| Security incident | Security Team | #security-incidents |

---

## ✅ PRE-DEPLOYMENT CHECKLIST (5 min)

```bash
# [ ] All services running?
docker compose -f docker-compose.full-test.yml ps | grep "Up"

# [ ] Health checks pass?
for port in 8000 8001 8002 8003 8004 8005; do
  curl -s http://localhost:$port/health || echo "FAIL: $port"
done

# [ ] Tests pass?
cd /home/elkakas314/vx11
python3 scripts/test_sse_ephemeral_token.py

# [ ] No security issues?
# Run from DEPLOYMENT_CHECKLIST_PRODUCTION.md

# [ ] Logs clean (no errors)?
docker compose -f docker-compose.full-test.yml logs | grep ERROR | wc -l
# Should be 0 or very low
```

---

## 📈 SUCCESS METRICS (24h post-deploy)

| Metric | Target | Actual |
|--------|--------|--------|
| Error rate | < 0.1% | [ ] |
| SSE latency | < 500ms | [ ] |
| Token cache size | < 200 | [ ] |
| Adoption rate | > 80% | [ ] |
| No incidents | ✅ | [ ] |

---

## 🔧 COMMON COMMANDS

```bash
# View all docs (start here!)
cat docs/operational/INDEX_OPERATIONAL_DOCUMENTATION.md

# Full runbooks (incidents)
cat docs/operational/RUNBOOKS_EPHEMERAL_TOKEN_INCIDENTS.md

# Monitoring setup
cat docs/operational/MONITORING_EPHEMERAL_TOKENS.md

# Scaling guide
cat docs/operational/SCALING_GUIDE_EPHEMERAL_TOKENS.md

# Full deployment checklist
cat docs/operational/DEPLOYMENT_CHECKLIST_PRODUCTION.md

# Technical spec
cat docs/status/P1_SECURITY_SSE_EPHEMERAL_TOKEN_20260103.md
```

---

## 💾 BACKUP & RECOVERY

```bash
# Backup current database
cp data/runtime/vx11.db data/backups/vx11_$(date +%s).db

# Backup config
cp docker-compose.full-test.yml docker-compose.full-test.yml.bak

# Restore from backup
cp data/backups/vx11_XXXXXXX.db data/runtime/vx11.db
docker compose -f docker-compose.full-test.yml restart operator-backend
```

---

## 🚨 IF THINGS GO WRONG

1. **Don't panic** — This is why we have runbooks
2. **Stop the bleed** — `docker compose stop operator-backend` if critical
3. **Gather info** — Run diagnostics above
4. **Check runbooks** — See RUNBOOKS_EPHEMERAL_TOKEN_INCIDENTS.md
5. **Escalate if needed** — Contact Backend Lead or Platform Lead
6. **Document** — Log incident in #vx11-incidents

---

**Remember:** You have full documentation at `docs/operational/INDEX_OPERATIONAL_DOCUMENTATION.md`  
**Emergency:** Call Backend Team Lead  
**Status:** View `docker compose ps` regularly

---

