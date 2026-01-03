# PRODUCTION DEPLOYMENT CHECKLIST

**Version:** P0 + P1 SSE Ephemeral Token System  
**Date:** 2026-01-03  
**Target:** Production Environment

---

## PRE-DEPLOYMENT (2-3 days before)

### Code Review & Testing

- [ ] Code review: backend changes (backend/main.py)
- [ ] Code review: frontend changes (EventsPanel.tsx)
- [ ] Code review: gateway changes (tentaculo_link/main_v7.py)
- [ ] Tests passing: 5/5 ephemeral token tests
- [ ] Tests passing: E2E SSE stream test
- [ ] Security scan: no hardcoded tokens
- [ ] Security scan: no exposed credentials

### Documentation & Runbooks

- [ ] Monitoring guide reviewed (MONITORING_EPHEMERAL_TOKENS.md)
- [ ] Runbooks reviewed (RUNBOOKS_EPHEMERAL_TOKEN_INCIDENTS.md)
- [ ] Team trained on incident response
- [ ] On-call engineer briefed
- [ ] Escalation paths documented

### Staging Deployment

- [ ] Deploy to staging environment
- [ ] Run smoke tests (5/5 PASS)
- [ ] Load test: 100+ concurrent streams
- [ ] Monitor for 2+ hours (collect metrics)
- [ ] Verify logs: no token exposure
- [ ] Verify metrics: normal ephemeral token rate
- [ ] Test fallback: principal token still works

### Client Readiness

- [ ] Frontend code deployed to staging
- [ ] Browser testing: tokens obtained via new endpoint
- [ ] Performance baseline: SSE latency < 500ms
- [ ] Verify browser console: no errors
- [ ] Test on multiple browsers (Chrome, Firefox, Safari)

---

## DEPLOYMENT WINDOW (2-4 hours)

### Pre-Flight Checklist (15 min)

- [ ] All team members on call
- [ ] Communication channel open (#vx11-deploy)
- [ ] Incident commander assigned
- [ ] Rollback decision maker available
- [ ] Monitoring dashboard open
- [ ] Runbooks accessible (printed or tabbed)

### Deployment Steps (30-45 min)

#### Phase 1: Backend Deployment
```bash
# 1. Deploy operator/backend with new code
docker build -t vx11-operator-backend:prod .
docker push vx11-operator-backend:prod

# 2. Update Kubernetes/ECS/deployment manifest
# operator_backend_image: vx11-operator-backend:prod

# 3. Rolling update (1 instance at a time)
kubectl set image deployment/operator-backend \
  operator-backend=vx11-operator-backend:prod --record
```

**Monitoring during Phase 1:**
- [ ] Backend health check passing (GET /operator/api/health → 200)
- [ ] No error rate spike (< 0.1% 5xx errors)
- [ ] Token issuance rate normal (5-50 tokens/min)

#### Phase 2: Gateway (tentaculo_link) Deployment
```bash
# 1. Deploy new tentaculo_link with proxy bypass logic
docker build -t vx11-tentaculo-link:prod .
docker push vx11-tentaculo-link:prod

# 2. Update manifest
tentaculo_link_image: vx11-tentaculo-link:prod

# 3. Rolling update
kubectl set image deployment/tentaculo-link \
  tentaculo-link=vx11-tentaculo-link:prod --record
```

**Monitoring during Phase 2:**
- [ ] Gateway responding (GET http://8000/health → 200)
- [ ] SSE proxy working (GET /operator/api/events/stream → 200)
- [ ] Token query params sanitized in logs (token=***)

#### Phase 3: Frontend Deployment
```bash
# 1. Build and push new React frontend
npm run build
docker build -t vx11-operator-frontend:prod .
docker push vx11-operator-frontend:prod

# 2. Update manifest
operator_frontend_image: vx11-operator-frontend:prod

# 3. Rolling update
kubectl set image deployment/operator-frontend \
  operator-frontend=vx11-operator-frontend:prod --record
```

**Monitoring during Phase 3:**
- [ ] UI loading (no 5xx errors)
- [ ] EventsPanel connecting (browser console no errors)
- [ ] SSE tokens being obtained (POST /operator/api/events/sse-token → 200)

### Post-Deployment Monitoring (30+ min)

#### Immediate (0-5 min)
- [ ] No 5xx errors
- [ ] Token issuance rate normal
- [ ] User sessions active (no mass logout)
- [ ] Database queries normal

#### Short-term (5-30 min)
- [ ] Ephemeral token requests rising (new frontend hitting endpoint)
- [ ] Principal token fallback requests dropping
- [ ] SSE stream success rate > 95%
- [ ] No unusual cache size growth

#### Medium-term (30+ min)
- [ ] Monitoring all green
- [ ] No alerting firing
- [ ] Adoption rate: > 50% ephemeral token usage
- [ ] Performance metrics stable

---

## ROLLBACK CRITERIA (Trigger IF...)

**AUTOMATIC ROLLBACK TRIGGERS:**
- [ ] 5xx error rate > 1% for 2 consecutive minutes
- [ ] Token validation failure rate > 100/sec
- [ ] Cache size anomaly (> 2000 active tokens)
- [ ] Backend latency > 1s (SSE endpoint timing out)
- [ ] All 3 backend instances down

**MANUAL ROLLBACK DECISION:**
- [ ] Customer complaints about SSE not working
- [ ] Major token leak detected in logs
- [ ] Data loss or corruption in token system
- [ ] Security incident related to ephemeral tokens

### Rollback Execution

```bash
# 1. Notify all team members
echo "ROLLBACK IN PROGRESS" | Slack #vx11-deploy

# 2. Revert backend to previous version
kubectl rollout undo deployment/operator-backend

# 3. Revert gateway
kubectl rollout undo deployment/tentaculo-link

# 4. Revert frontend
kubectl rollout undo deployment/operator-frontend

# 5. Monitor for stability (5+ min)

# 6. Document incident (see: Incident Response section)
```

---

## POST-DEPLOYMENT (1-24 hours)

### Day 1: Observation Period

**First 4 hours:**
- [ ] Monitor every 30 minutes
- [ ] No escalations expected
- [ ] Token metrics stable
- [ ] No customer complaints

**4-24 hours:**
- [ ] Monitor every 2 hours
- [ ] Check adoption rate (% using ephemeral tokens)
- [ ] Review incident logs (should be none)
- [ ] Document any issues found

### Adoption Metrics

Expected timeline:
- **Hour 1-2:** 10-20% adoption (cached browsers)
- **Hour 2-4:** 40-60% adoption (browser refreshes)
- **Hour 4-24:** 80-90% adoption (steady state)
- **24-48h:** 95%+ adoption (normal)

**If adoption stalls:**
- Check frontend logs for errors
- Verify POST /operator/api/events/sse-token endpoint
- Check browser compatibility issues
- Consider forced refresh or update

### Security Verification

- [ ] Audit logs: token endpoints called appropriately
- [ ] Access logs: token query params show `***` (sanitized)
- [ ] No token leakage: grep logs for `token=[a-f0-9]`
- [ ] No hardcoded tokens in new code

### Performance Verification

- [ ] SSE latency: < 500ms (baseline)
- [ ] Token issuance: 20-100 tokens/min (normal)
- [ ] Validation failure: < 1/min (acceptable)
- [ ] Cache size: 50-200 tokens (normal)

---

## ROLLBACK + INCIDENT RESPONSE

If rollback executed:

1. **Document Timeline**
   - When deploy started
   - When rollback triggered
   - When system restored
   - Total downtime

2. **Post-Mortem (within 24h)**
   - What went wrong?
   - Why didn't we catch it in staging?
   - What's the fix?
   - How do we prevent recurrence?

3. **Fix & Re-Deploy**
   - Fix root cause
   - Test in staging again
   - Deploy on next window

---

## SUCCESS CRITERIA

Deployment is **SUCCESSFUL** if ALL met:

- [ ] Zero 5xx errors (0% error rate)
- [ ] Token system operational (> 95% success)
- [ ] User adoption > 50% by hour 4
- [ ] No security incidents
- [ ] No customer complaints
- [ ] Metrics stable and predictable
- [ ] Runbooks not needed (no incidents)

Deployment is **PARTIAL SUCCESS** if:

- [ ] Some minor issues, but < 0.1% error rate
- [ ] Adoption slower than expected (but trending up)
- [ ] No security or stability concerns
- [ ] Plan remediation for next window

Deployment is **ROLLBACK** if:

- [ ] > 1% error rate
- [ ] Major security incident
- [ ] System instability
- [ ] Customer impact

---

## Communication Template

### Pre-Deployment
```
🚀 DEPLOYMENT WINDOW: [DATE] [TIME-TIME] UTC

Change: SSE Ephemeral Token System (P0 + P1)
- Reduces token exposure in URLs from 60m → 60s
- New endpoint: POST /operator/api/events/sse-token
- Frontend auto-updated

Impacted: EventsPanel (SSE streams), authentication
Estimated downtime: 0-5 min (rolling updates)
Rollback available: Yes (automatic if needed)

Team: [names] on call
Questions? Slack #vx11-deploy
```

### During Deployment
```
✅ Phase 1 Complete: Backend deployed successfully
✅ Phase 2 Complete: Gateway updated
⏳ Phase 3 In Progress: Frontend rolling update (2/3 complete)
```

### Post-Deployment
```
🎉 DEPLOYMENT COMPLETE

Metrics:
- Error rate: 0.02% (normal)
- Token system: Operational
- Adoption rate: 60% (target: 50%+)
- No incidents: ✅

Monitoring continues for 24h.
```

---

## Contact & Escalation

- **Incident Commander:** [Name]
- **On-Call:** [Name/Slack handle]
- **Platform Lead:** [Name/Slack handle]
- **Slack Channel:** #vx11-deploy
- **Pagerduty:** vx11-incidents

---
