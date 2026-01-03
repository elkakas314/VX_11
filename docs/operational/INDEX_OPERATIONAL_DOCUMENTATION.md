# VX11 EPHEMERAL SSE TOKEN SYSTEM — OPERATIONAL DOCUMENTATION INDEX

**Version:** Production (P0 + P1)  
**Date:** 2026-01-03  
**Status:** 🟢 Ready for Deployment

---

## Quick Links

### For Developers
- [Implementation Details](../status/P1_SECURITY_SSE_EPHEMERAL_TOKEN_20260103.md) — Complete technical spec
- [Code Changes Summary](../status/FULL_EXECUTION_SUMMARY_20260103.md) — What was modified
- [Scaling Guide](SCALING_GUIDE_EPHEMERAL_TOKENS.md) — Multi-instance architecture

### For Operations
- [Monitoring Guide](MONITORING_EPHEMERAL_TOKENS.md) — Prometheus/Grafana setup
- [Runbooks](RUNBOOKS_EPHEMERAL_TOKEN_INCIDENTS.md) — Incident troubleshooting
- [Deployment Checklist](DEPLOYMENT_CHECKLIST_PRODUCTION.md) — Go-live procedures

### For Architects
- [Full Execution Summary](../status/FULL_EXECUTION_SUMMARY_20260103.md) — End-to-end overview
- [Forensic Baseline](../audit/fase_0_5_20260103_185540/) — Pre-deployment state

---

## Documentation Map

### 📊 Implementation & Design

| Document | Purpose | Audience |
|----------|---------|----------|
| [P1_SECURITY_SSE_EPHEMERAL_TOKEN](../status/P1_SECURITY_SSE_EPHEMERAL_TOKEN_20260103.md) | Technical spec, implementation details | Developers, Architects |
| [FULL_EXECUTION_SUMMARY](../status/FULL_EXECUTION_SUMMARY_20260103.md) | Executive summary, what changed | Everyone |
| [Forensic Baseline](../audit/fase_0_5_20260103_185540/) | Pre-deployment state, OpenAPI specs | Architects, QA |

### 🔧 Operational Runbooks

| Document | Purpose | When to Use |
|----------|---------|------------|
| [MONITORING_EPHEMERAL_TOKENS](MONITORING_EPHEMERAL_TOKENS.md) | Prometheus/Grafana setup, metrics, alerts | Ops setup |
| [RUNBOOKS_EPHEMERAL_TOKEN_INCIDENTS](RUNBOOKS_EPHEMERAL_TOKEN_INCIDENTS.md) | Incident response procedures | On-call engineer |
| [DEPLOYMENT_CHECKLIST_PRODUCTION](DEPLOYMENT_CHECKLIST_PRODUCTION.md) | Step-by-step deployment procedure | Release manager |

### 📈 Scaling & Performance

| Document | Purpose | Scenario |
|----------|---------|----------|
| [SCALING_GUIDE_EPHEMERAL_TOKENS](SCALING_GUIDE_EPHEMERAL_TOKENS.md) | Redis, load balancing, capacity planning | Multi-instance setup |

---

## Key Metrics & Targets

### Performance SLOs
- Token issuance latency: < 50ms (alert: > 100ms)
- SSE stream latency: < 500ms (alert: > 1s)
- Token validation success: > 99% (alert: < 98%)

### Capacity
- Single instance: 100 tokens/sec, < 100 tokens in cache
- Multi-instance (3x): 300 tokens/sec, Redis-backed
- Multi-instance (10x): 1000+ tokens/sec, Redis + local cache

### Alerts to Monitor
1. `HighEphemeralTokenRequestRate` — Rate > 100/sec
2. `UnusuallyHighCacheSize` — Cache > 500 tokens
3. `HighTokenValidationFailureRate` — Failures > 10/sec
4. `HighPrincipalTokenUsageInSSE` — Fallback > 10%

---

## Pre-Deployment Checklist

- [ ] All code reviewed ✅
- [ ] All tests passing (5/5) ✅
- [ ] Staging deployed and verified ✅
- [ ] Monitoring configured (Prometheus/Grafana)
- [ ] Runbooks reviewed with on-call
- [ ] Rollback plan documented
- [ ] Communication templates ready

---

## Deployment Phases

### Phase 1: Backend Deployment (15 min)
- Deploy operator/backend with new code
- Verify health check passing
- Monitor error rate (should stay < 0.1%)

### Phase 2: Gateway Deployment (15 min)
- Deploy tentaculo_link with proxy bypass
- Verify SSE proxy working
- Confirm token sanitization in logs

### Phase 3: Frontend Deployment (15 min)
- Deploy EventsPanel with ephemeral token support
- Verify no browser errors
- Monitor adoption rate (target: 50%+ by hour 4)

---

## Post-Deployment Monitoring (24h)

### Hour 0-2: Critical
- Error rate should be < 0.5%
- Token issuance rate: 20-100 tokens/min
- Adoption rate: 10-30%

### Hour 2-4: Important
- Error rate should be < 0.1%
- Adoption rate should reach 40-60%
- Cache size should stabilize (100-200 tokens)

### Hour 4-24: Observation
- Continue monitoring every 2 hours
- Adoption should trend toward 90%+
- No incidents or escalations expected

---

## Incident Response Matrix

| Symptom | Root Cause | Action |
|---------|-----------|--------|
| 401 Unauthorized errors | Token endpoint unreachable | Check gateway proxy, backend health |
| 403 Forbidden (invalid_token) | Token cache issue (single vs multi) | Check Redis (if multi-instance), restart backend |
| High cache size growth | Token leak or TTL misconfiguration | Check TTL setting, monitor expiry rate |
| Fallback token usage > 10% | Clients not using new endpoint | Check frontend code, browser cache |
| Load spike > 200 tokens/sec | Legitimate traffic or client loop | Monitor, scale if needed, check logs |

---

## Rollback Procedure

**Automatic triggers:**
- Error rate > 1% for 2 min
- Token validation failures > 100/sec
- Backend latency > 1s

**Manual triggers:**
- Customer complaint
- Security incident
- Data loss/corruption

**Steps:**
```bash
kubectl rollout undo deployment/operator-backend
kubectl rollout undo deployment/tentaculo-link
kubectl rollout undo deployment/operator-frontend
# Monitor for 5+ minutes
```

---

## Adoption Tracking

**Expected timeline:**
- **Hours 1-2:** 10-20% (browser cache)
- **Hours 2-4:** 40-60% (first refresh)
- **Hours 4-24:** 80-95% (steady state)
- **24-48h:** 95%+ (complete)

**Metric to track:**
```promql
vx11_operator_sse_connections_ephemeral_total / 
(vx11_operator_sse_connections_ephemeral_total + vx11_operator_sse_connections_principal_total)
```

**If adoption stalls below 80% at hour 24:**
1. Check frontend error logs
2. Verify POST /operator/api/events/sse-token working
3. Consider forced browser refresh or update

---

## Security Verification Checklist

- [ ] No hardcoded tokens in code
- [ ] Logs sanitized (token=***)
- [ ] No tokens in browser localStorage
- [ ] No tokens in query params logged
- [ ] HTTPS required (not HTTP)
- [ ] Token TTL enforced (60s max)
- [ ] No token reuse (UUIDs unique)

---

## Performance Baseline

**Before Deployment (single instance):**
- SSE latency: ~300ms
- Token issuance: N/A (new feature)
- Error rate: 0.01%

**After Deployment (single instance, expected):**
- SSE latency: 400-500ms (initial token fetch adds 100-200ms)
- Token issuance: 20-50 tokens/min (normal usage)
- Error rate: < 0.1% (no regression)

**After 24h (adoption complete):**
- Latency should stabilize at 300-400ms (browsers cache)
- Token issuance: 50-100 tokens/min (more sessions active)
- Error rate: < 0.05% (improvement from cache hit rate)

---

## Team Contacts

- **Incident Commander:** [Assign before deploy]
- **On-Call Engineer:** [Assign before deploy]
- **Platform Lead:** [Escalation contact]
- **Slack:** #vx11-deploy, #vx11-incidents

---

## Success Criteria

Deployment is **SUCCESSFUL** if:
- ✅ Zero major incidents (no page)
- ✅ Error rate < 0.1% all 24h
- ✅ Adoption > 80% by hour 24
- ✅ No security concerns
- ✅ Runbooks not needed

---

## References

**Architecture:**
- [Ephemeral Token Pattern](https://auth0.com/blog/refresh-tokens-what-are-they-and-when-to-use-them/) — Authentication best practices
- [EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource) — Browser limitation (no custom headers)

**Operations:**
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/)

**Deployment:**
- [Kubernetes Rolling Update](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)
- [Blue-Green Deployment Pattern](https://martinfowler.com/blueGreenDeployment.html)

---

## Document Versions

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-03 | Initial operational guide |

---

**Last Updated:** 2026-01-03  
**Status:** Ready for Production Deployment  
**Reviewed By:** [Engineer name]  
**Approved By:** [Manager name]

---
