# PHASE 3 BASELINE — Operator Superpack Alignment

**Generated**: 2025-12-29T04:32:01Z  
**Status**: AUDIT ONLY

---

## 1. CURRENT STATE: Operator Deployment

### Backend Status
```bash
curl -s http://localhost:8011/health 2>/dev/null || echo "OFFLINE (expected: solo_madre doesn't run operator)"
```

Backend disabled in solo_madre (profile). Enabled via:
```
docker compose up -d operator-backend operator-frontend
```

### Frontend Status
```bash
curl -s http://localhost:8020/ 2>/dev/null | head -5 || echo "OFFLINE"
```

Frontend served via Vite (dev) or static build (prod).

### Current Operator API Endpoints
- ✅ `/health` — Basic health (200 OK)
- ✅ `/api/modules` — 10 services with health checks
- ✅ `/api/topology` — Architecture graph (10 nodes, 9 edges)
- ✅ `/api/fs/list` — Sandboxed file explorer
- ❌ `/operator/api/chat` — NOT YET ALIGNED (estamos aquí)
- ❌ `/operator/api/status` — NOT YET ALIGNED
- ❌ `/operator/api/events` — NOT YET ALIGNED
- ❌ `/operator/api/metrics` — NOT YET ALIGNED

### Key Findings

**Gap 1**: /operator/api/chat (tentaculo routing to switch/madre)
- Current: Works via tentaculo but NO correlation_id tracking
- Required: correlation_id + provider selection (mock|deepseek|local)
- Impact: No traceability in logs/audit

**Gap 2**: No unified status endpoint
- Current: /health only (madre only)
- Required: /operator/api/status (all services, features, policies)
- Impact: Frontend can't show system state

**Gap 3**: No event streaming
- Current: No /operator/api/events endpoint
- Required: SSE or WebSocket for live updates
- Impact: Frontend polls /health repeatedly (wasteful)

**Gap 4**: No metrics/stats endpoint
- Current: No /operator/api/metrics
- Required: Request counts, latencies, error rates
- Impact: No observability dashboard

**Gap 5**: No explicit feature_disabled states
- Current: Hard to tell if feature is off or broken
- Required: Explicit status enums (on|off|degraded|error)
- Impact: Frontend guesswork

---

## 2. ARCHITECTURE DECISION: Single Entrypoint (Confirmed)

All traffic MUST flow via `tentaculo_link:8000`:
```
Browser → tentaculo:8000/operator/api/* → madre/switch/redis
```

**NOT**:
```
Browser → operator-backend:8011/api/* (BYPASSES tentaculo, NO auth, NO gating)
```

### Implication for PHASE 3
- **operator/api/chat**: Route to tentaculo, then to switch provider (mock|deepseek|local)
- **operator/api/status**: Route to tentaculo, then introspect madre (services, features, policies)
- **operator/api/events**: Streaming from tentaculo (SSE)
- **operator/api/metrics**: Route to tentaculo, then query madre stats

---

## 3. DATABASE SUPPORT (Verified)

Tables supporting Operator needs:
- `audit_logs` (10 rows) — Log all operations
- `copilot_actions_log` (142 rows) — Track copilot actions (could use for events)
- `feature_flags` (4 rows) — Track feature on/off states
- `service_configs` (10 rows) — Service registry + health
- `performance_logs` (0 rows) — Metrics/stats

**Action**: Use `service_configs` + `feature_flags` for alignment.

---

## 4. SPEC ALIGNMENT CHECKLIST

**PHASE 3 Objectives**:
- [ ] Correlation_id injection (PHASE 2 designed it, now integrate)
- [ ] /operator/api/chat via provider registry (use new MockProvider)
- [ ] /operator/api/status endpoint (real data from DB)
- [ ] Auth header validation (x-vx11-token)
- [ ] Feature flags querying (feature_disabled states)
- [ ] No stubs (all responses real or degraded, never fake)
- [ ] All via tentaculo (no direct operator:8011 calls)

**DS-R1 Rails**:
- **PLAN**: API contract design + correlation_id flow + feature state schema
- **REVIEW**: Security review (auth, correlation tracking, feature flag validation)
- **RCA**: If CORS/routing issues arise

---

## 5. NEXT ACTIONS

1. **DS-R1(A) PLAN**: Design /operator/api/* contract (status, chat, events, metrics)
2. **Implementation**: Update tentaculo → madre routing + add status endpoint
3. **Tests**: Integration test (correlation_id flows through)
4. **DS-R1(B) REVIEW**: Security + compliance check
5. **Commit**: PHASE 3 complete

---

**Status**: AUDIT COMPLETE — Ready for DS-R1(A) PLAN
