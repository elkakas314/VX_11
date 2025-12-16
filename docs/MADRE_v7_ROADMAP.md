# Madre v7 — NEXT PHASES ROADMAP

## ✅ COMPLETED (v7.0.0)

- [x] Modular architecture (core/ with 8 modules)
- [x] Pydantic response contracts (guaranteed)
- [x] Repository pattern (MadreDB)
- [x] Risk classification + confirmation tokens
- [x] Fallback parser (works without Switch)
- [x] Async plan execution (Runner)
- [x] HTTP delegation (no spawning yet)
- [x] FastAPI endpoints (7 total)
- [x] Tests P0 (25 tests, 100% passing)
- [x] Documentation (comprehensive README)
- [x] Forensic logging integration

---

## 📋 PHASE 2: SPAWNER v1 (Deferred)

**Objective:** Implement Spawner (8008) module to execute daughter_tasks

### PR CHECKLIST

- [ ] **spawner/main.py** (FastAPI app, port 8008)
  - [ ] `GET /health` endpoint
  - [ ] `GET /spawner/jobs` (list pending/running)
  - [ ] `POST /spawner/execute/{job_id}` (pickup from daughter_tasks)
  - [ ] `POST /spawner/heartbeat/{job_id}` (update last_heartbeat)
  - [ ] `POST /spawner/complete/{job_id}` (mark done + record result)

- [ ] **spawner/executor.py**
  - [ ] `execute_daughter_task()` - main execution logic
  - [ ] Process isolation (subprocess, timeout)
  - [ ] Resource limits (memory, CPU)
  - [ ] Auto-cleanup (kill after TTL)

- [ ] **spawner/models.py**
  - [ ] `SpawnerJob` (daughter_tasks mirror)
  - [ ] `JobStatus` enum (PENDING|RUNNING|DONE|ERROR|KILLED)
  - [ ] `JobResult` (output capture)

- [ ] **Tests: tests/test_spawner.py**
  - [ ] test_job_pickup
  - [ ] test_job_execution
  - [ ] test_job_timeout
  - [ ] test_job_isolation

- [ ] **Docker**
  - [ ] spawner/Dockerfile (slim Python 3.11)
  - [ ] docker-compose.yml: add spawner service (port 8008)

- [ ] **DB Schema Check**
  - [ ] daughter_tasks: ensure status transitions work
  - [ ] daughters: if tracking individual spawns
  - [ ] daughter_attempts: retry tracking

---

## 🔄 PHASE 3: AUTONOMOUS LOOP (Madre)

**Objective:** Madre ciclo autónomo cada 30 segundos (non-blocking)

### CHECKLIST

- [ ] **madre/core/autonomous.py** (new module)
  - [ ] `AutonomousLoop` class
  - [ ] `observe()` - collect system state
  - [ ] `reason()` - use Switch to decide
  - [ ] `decide()` - choose action
  - [ ] `delegate()` - send to Spawner/Hormiguero/Manifestator
  - [ ] `report()` - log results

- [ ] **madre/main.py: integration**
  - [ ] `POST /madre/autonomous/start` endpoint
  - [ ] `POST /madre/autonomous/stop` endpoint
  - [ ] Background task manager (asyncio)

- [ ] **madre/core/metrics.py** (new module)
  - [ ] Collect CPU, memory, queue levels
  - [ ] Track module availability
  - [ ] Predict bottlenecks

- [ ] **Tests: tests/test_madre_autonomous.py**
  - [ ] test_observe_collects_state
  - [ ] test_reason_generates_plan
  - [ ] test_decide_selects_action
  - [ ] test_delegate_sends_request
  - [ ] test_non_blocking_iteration

---

## 🔗 PHASE 4: CONTEXT-7 INTEGRATION

**Objective:** Session clustering with TTL, multi-user support

### CHECKLIST

- [ ] **config/context7.py** (new module - already exists!)
  - [ ] `Context7SessionManager`
  - [ ] TTL expiry
  - [ ] Topic clustering
  - [ ] User context persistence

- [ ] **madre/core/context_manager.py** (new module)
  - [ ] Integrate Context-7 into Madre
  - [ ] Context inheritance between intents
  - [ ] Session cleanup

- [ ] **madre/models.py: update**
  - [ ] Add `user_id` field to intents
  - [ ] Add `context_topics` list

- [ ] **DB Schema Check**
  - [ ] context_7_sessions table (if not exists)
  - [ ] Ensure TTL column

- [ ] **Tests: tests/test_context7_madre.py**
  - [ ] test_session_creation
  - [ ] test_context_inheritance
  - [ ] test_ttl_expiry

---

## 📡 PHASE 5: SWITCH STREAMING

**Objective:** Support streaming responses from Switch/CLI providers

### CHECKLIST

- [ ] **madre/core/streaming.py** (new module)
  - [ ] `StreamHandler` class
  - [ ] HTTP chunks processing
  - [ ] WebSocket real-time updates

- [ ] **madre/main.py: WebSocket endpoint**
  - [ ] `WebSocket /ws/{session_id}`
  - [ ] Streaming plan execution
  - [ ] Real-time step updates

- [ ] **madre/core/runner.py: update**
  - [ ] Support streaming steps
  - [ ] Async iterators for long-running tasks

- [ ] **Tests: tests/test_madre_streaming.py**
  - [ ] test_stream_response
  - [ ] test_websocket_connection
  - [ ] test_real_time_updates

---

## 👥 PHASE 6: MULTI-TENANCY

**Objective:** Role-based access control, per-user isolation

### CHECKLIST

- [ ] **madre/core/rbac.py** (new module)
  - [ ] Role definitions (user, admin, system)
  - [ ] Permission checks
  - [ ] Audit trail per user

- [ ] **madre/models.py: update**
  - [ ] Add `user_id`, `role`, `permissions` fields

- [ ] **madre/core/db.py: update**
  - [ ] Add user_id filter to queries
  - [ ] Enforce isolation

- [ ] **Endpoints: update**
  - [ ] Validate user permissions on each endpoint
  - [ ] Return 403 if unauthorized

- [ ] **Tests: tests/test_madre_rbac.py**
  - [ ] test_user_isolation
  - [ ] test_permission_checks
  - [ ] test_admin_override

---

## 🚀 PHASE 7: PERFORMANCE & SCALING

**Objective:** Optimize for high throughput, low latency

### CHECKLIST

- [ ] **Benchmarks: scripts/bench_madre.py**
  - [ ] Measure latency per endpoint
  - [ ] Throughput (RPS)
  - [ ] Memory usage

- [ ] **Caching: madre/core/cache.py**
  - [ ] LRU cache for parsed intents
  - [ ] TTL-based invalidation
  - [ ] Cache metrics

- [ ] **Connection pooling**
  - [ ] httpx connection reuse
  - [ ] DB connection pool optimization

- [ ] **Load testing**
  - [ ] K6 or locust scripts
  - [ ] Identify bottlenecks
  - [ ] Document max throughput

---

## 🔐 PHASE 8: SECURITY HARDENING

**Objective:** Production-grade security posture

### CHECKLIST

- [ ] **Rate limiting**
  - [ ] Add slowapi (FastAPI rate limiter)
  - [ ] Per-user rate limits

- [ ] **Input validation**
  - [ ] SQL injection prevention (already using ORM)
  - [ ] XSS prevention (JSON responses, no HTML)
  - [ ] Command injection (no shell=True)

- [ ] **Secrets management**
  - [ ] Rotate VX11_TOKEN annually
  - [ ] Environment-based config
  - [ ] No hardcoded secrets

- [ ] **Audit logging**
  - [ ] Log all sensitive operations
  - [ ] Retention policy (90 days)
  - [ ] Immutable audit trail

- [ ] **Security tests: tests/test_security.py**
  - [ ] test_unauthorized_access
  - [ ] test_rate_limiting
  - [ ] test_token_validation

---

## 📦 DEPLOYMENT CHECKLIST

Before deploying v7.0 to production:

- [ ] **Code review**
  - [ ] PR review by maintainers
  - [ ] Architecture review
  - [ ] Security review

- [ ] **Tests**
  - [ ] 25 unit tests passing ✅
  - [ ] Integration tests (with real Switch, Spawner)
  - [ ] Smoke tests (all 7 endpoints)
  - [ ] Load tests (100 RPS)

- [ ] **Docker**
  - [ ] Build madre image: `docker build -t vx11-madre:7.0 .`
  - [ ] Test locally: `docker run -p 8001:8001 vx11-madre:7.0`
  - [ ] Push to registry

- [ ] **Documentation**
  - [ ] README updated ✅
  - [ ] API docs generated (Swagger)
  - [ ] Troubleshooting guide
  - [ ] Migration guide (v6 → v7)

- [ ] **Monitoring**
  - [ ] Health endpoint monitored
  - [ ] Error rate threshold (< 0.1%)
  - [ ] Latency SLO (p99 < 2s)
  - [ ] Memory limit alerts (> 400MB)

- [ ] **Rollback plan**
  - [ ] Easy revert to v6 (if needed)
  - [ ] DB migration plan (reversible)
  - [ ] Notification channels (Slack, email)

---

## 📊 SUCCESS METRICS (v7.0 LAUNCH)

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Test coverage | >85% | ~85% | ✅ |
| Endpoint latency (p99) | <2s | TBD | ⏳ |
| Error rate | <0.1% | TBD | ⏳ |
| Uptime | >99.5% | TBD | ⏳ |
| Code complexity | <10 avg | ~7 | ✅ |
| Documentation completeness | 100% | ~95% | ✅ |

---

## 🎯 Timeline Estimate

| Phase | Effort | Timeline |
|-------|--------|----------|
| Phase 2 (Spawner) | 2-3 weeks | Week 2-3 Jan |
| Phase 3 (Autonomous) | 1-2 weeks | Week 4 Jan |
| Phase 4 (Context-7) | 1 week | Week 1-2 Feb |
| Phase 5 (Streaming) | 2-3 weeks | Week 2-3 Feb |
| Phase 6 (Multi-tenancy) | 2-3 weeks | Week 4 Feb |
| Phase 7 (Performance) | 1-2 weeks | Week 1 Mar |
| Phase 8 (Security) | 1-2 weeks | Week 2 Mar |
| **Total** | **11-15 weeks** | **Jan-Mar 2025** |

---

## 🔗 Key Files to Update

### Per Phase
- **Phase 2 (Spawner):** Create `spawner/` directory
- **Phase 3 (Autonomous):** Update `madre/core/autonomous.py` + `metrics.py`
- **Phase 4 (Context-7):** Update `config/context7.py` + `madre/core/context_manager.py`
- **Phase 5 (Streaming):** Update `madre/main.py` + `madre/core/runner.py`
- **Phase 6 (Multi-tenancy):** Update `madre/core/rbac.py` + `madre/models.py`
- **Phase 7 (Performance):** Create `scripts/bench_madre.py`
- **Phase 8 (Security):** Create `tests/test_security.py`

### Always Update
- `tests/` (add phase-specific tests)
- `docs/` (update ARCHITECTURE.md, add new phase docs)
- `docker-compose.yml` (add new services)
- `README.md` (update status, timeline)

---

## 💡 NOTES

1. **Backward compatibility:** All phases maintain v7.0 API contract
2. **Feature flags:** Use `config.settings` to enable/disable phases
3. **DB migrations:** Use reversible migrations (Alembic pattern)
4. **Monitoring:** Set up alerts for each phase before launch
5. **Documentation:** Update docs/ARCHITECTURE.md for each phase

---

**Generated:** 2025-01-08  
**Next Review:** Before Phase 2 Kickoff

