# Phase 2B — Execution Plan & Progress Tracker

**Status:** READY FOR EXECUTION  
**Created:** 2025-12-15 T23:30 UTC  
**Mandate:** "EJECUTA END-TO-END" (execute without questions)

---

## Executive Summary

Phase 2B consists of 6 sequential hitos to complete VX11 production readiness:

| Hito | Task | Script | Duration | Status |
|------|------|--------|----------|--------|
| 1 | Playwright MCP sidecar | docker-compose.playwright.yml | 10 min | ✅ READY |
| 2 | Download 2 test models | hermes_download_test_models.py | 15 min | ✅ READY |
| 3 | Warmup + rotation test | warmup_smoke_test.py | 10 min | ✅ READY |
| 4 | Canonical DB <500MB | vx11_canonical_db_generate.py | 10 min | ✅ READY |
| 5 | DB schema map | generate_db_map.py | 5 min | ✅ READY |
| 6 | Production readiness | vx11_production_readiness.py | 10 min | ✅ READY |
| **TOTAL** | | | **~60 min** | |

---

## Hito 1: Playwright MCP Sidecar ✅ IMPLEMENTED

**Objective:** Integrate Playwright as WebSocket sidecar for Operator browser automation

**Status:** ✅ COMPLETED
- `docker-compose.playwright.yml` — Overlay with Playwright service (port 3000)
- `config/playwright_config.py` — Client factory (remote/local/stub modes)
- `operator_backend/backend/browser.py` — Updated to use PlaywrightClientFactory
- Environment vars: `VX11_ENABLE_PLAYWRIGHT=1`, `PLAYWRIGHT_WS_URL=ws://playwright:3000`

**Execution:** (Manual if needed)
```bash
# Option A: Local Playwright (direct, requires browser dependencies)
export BROWSER_IMPL=playwright
python3 -m pytest tests/test_operator_browser_workflow.py -v

# Option B: Remote Playwright (via sidecar)
docker-compose -f docker-compose.yml -f docker-compose.playwright.yml up -d
export BROWSER_IMPL=playwright PLAYWRIGHT_WS_URL=ws://localhost:3000
python3 -m pytest tests/test_operator_browser_workflow.py -v

# Option C: Stub mode (no real browser, for testing)
export BROWSER_IMPL=stub
python3 -m pytest tests/test_operator_browser_workflow.py -v
```

**Success Criteria:**
- POST /operator/browser/task works with stub or real browser
- Screenshot captured (if using real browser)
- Text extraction working
- Test assertions pass

---

## Hito 2: Download 2 Test Models ⏳ READY FOR EXECUTION

**Objective:** Download 2 GGUF models (<2GB each) and register in DB

**Models:**
1. **Mistral 7B Instruct** (2.2GB GGUF Q4_K_M)
   - HF: TheBloke/Mistral-7B-Instruct-v0.2-GGUF
   - Task: chat, reasoning
   
2. **Neural Chat 7B** (2.0GB GGUF Q4_M)
   - HF: TheBloke/neural-chat-7B-v3-3-GGUF
   - Task: chat, conversational

**Execution:**
```bash
# Requires ~4.5GB free space in /app/models
export VX11_MODELS_PATH=/app/models

# Run download + registration
python3 scripts/hermes_download_test_models.py

# Output:
# ⏳ Downloading mistral-7b-instruct (2236MB)...
# ✓ Downloaded mistral-7b-instruct (2.2GB)
# ✓ Registered mistral-7b-instruct in DB
# ⏳ Downloading neural-chat-7b (2048MB)...
# ✓ Downloaded neural-chat-7b (2.0GB)
# ✓ Registered neural-chat-7b in DB
# ✓ All models registered
```

**Success Criteria:**
- Both models downloaded to `/app/models/*.gguf`
- Both registered in `local_models_v2` table
- `enabled=True` and `compatibility=cpu`
- POST /operator/resources shows both models
- DB query returns 2+ models

**Expected Time:** 15-20 minutes (depends on network/disk speed)

---

## Hito 3: Warmup + Rotation Smoke Test ⏳ READY FOR EXECUTION

**Objective:** Validate model loading, warmup, and LRU rotation lifecycle

**Execution:**
```bash
# Requires models downloaded (Hito 2)
python3 scripts/warmup_smoke_test.py

# Output:
# Test 1: Models registered ✅
# Test 2: Warmup models ✅
#   🔥 Warming up mistral-7b-instruct... ✓ Warmup OK: 450ms
#   🔥 Warming up neural-chat-7b... ✓ Warmup OK: 380ms
# Test 3: Rotation eligibility ✅
#   mistral-7b-instruct | usage=1 | age=5s | IN_USE
#   neural-chat-7b | usage=1 | age=5s | IN_USE
# Test 4: IA decisions logged ✅
# Test 5: Usage stats tracking ✅
# Results: 5/5 tests passed ✅
```

**Success Criteria:**
- All 5 subtests pass
- Warmup latency <5s per model
- `usage_count` incremented in DB
- `last_used_at` updated
- `ia_decisions` table has 2+ entries
- `model_usage_stats` tracking working

**Expected Time:** 5-10 minutes

---

## Hito 4: Canonical DB Generation ⏳ READY FOR EXECUTION

**Objective:** Clean, optimize, and validate DB <500MB

**Execution:**
```bash
# Full cleanup + validation
python3 scripts/vx11_canonical_db_generate.py

# Output:
# Step 1: Cleanup old records
#   ✓ Archived 0 old forensic records
#   ✓ Deleted 0 old audit log records
# Step 2: Sync module tables
#   ✓ DB tables synced: 67 tables
# Step 3: Optimize database (VACUUM)
#   ✓ VACUUM completed: 523.4MB → 498.2MB (saved 25.2MB)
# Step 4: Database integrity check
#   ✓ Database integrity check: OK
# Step 5: Size validation
#   ✓ DB size OK: 498.2MB < 500MB target
# Step 6: Create backup
#   ✓ Backup created: vx11.db.canonical_20251215_233015 (498.2MB)
# ✅ Canonical DB generation complete — DB ready for production
```

**Success Criteria:**
- VACUUM completes without errors
- Final DB size <500MB
- Integrity check passes
- Backup created in `/app/data/backups/`
- All tables synced (67 tables)

**Expected Time:** 2-5 minutes

---

## Hito 5: Database Schema Map ⏳ READY FOR EXECUTION

**Objective:** Generate comprehensive schema documentation

**Execution:**
```bash
# Generate docs
python3 scripts/generate_db_map.py

# Output:
# Generating Markdown schema...
# ✓ Created: docs/audit/DB_MAP_v7_FINAL.md
# Generating JSON schema...
# ✓ Created: docs/audit/DB_SCHEMA_v7_FINAL.json
# ✅ Schema map generated:
#    Tables: 67
#    Markdown: DB_MAP_v7_FINAL.md
#    JSON: DB_SCHEMA_v7_FINAL.json
```

**Outputs:**
- `docs/audit/DB_MAP_v7_FINAL.md` — Human-readable schema (all tables, columns, indices)
- `docs/audit/DB_SCHEMA_v7_FINAL.json` — Machine-readable schema

**Success Criteria:**
- Both files created
- Markdown includes all 67 tables
- JSON valid and parseable
- File sizes reasonable (<1MB each)

**Expected Time:** <1 minute

---

## Hito 6: Production Readiness Check ⏳ READY FOR EXECUTION

**Objective:** Full system health validation

**Execution:**
```bash
# Requires: all 9 modules running, models registered, DB clean
python3 scripts/vx11_production_readiness.py

# Output:
# Checking module health...
# Checking database...
# Checking essential tables...
# Checking models...
# Checking logs...
#
# # VX11 Production Readiness Check
# ...
# ## Overall Status
# ✅ PRODUCTION READY
# All checks passed. System is ready for deployment.
```

**Checks:**
- 9 modules respond to health endpoints
- DB integrity + size <500MB
- Essential tables exist + populated
- 2+ models enabled and available
- Logs and forensics operational

**Success Criteria:**
- All 9 modules: ✅ OK
- Database: ✅ OK + size <500MB
- Tables: All present + rows >0
- Models: 2+ enabled
- Final status: ✅ PRODUCTION READY

**Expected Time:** 5-10 minutes (may take longer if modules are slow to respond)

---

## Execution Order & Dependencies

**Sequential execution (each depends on previous):**

```
Hito 1: Playwright ───┐
                      ├──> Hito 2: Models ──> Hito 3: Warmup
Hito 4: Canonical DB ─┤
Hito 5: Schema Map ───┤
                      └──> Hito 6: Readiness (all systems)
```

**Parallel (no dependencies):**
- Hito 1 and Hito 4, 5 can run in parallel

**Cannot start Hito 3, 6 until:** Hito 2 completes (models downloaded)

---

## Pre-Flight Checklist

Before executing Phase 2B, verify:

- [ ] Disk space: ~5GB available in `/app/models/` (for model downloads)
- [ ] Network: Can reach HuggingFace (huggingface.co)
- [ ] DB backup: Latest backup exists in `/app/data/backups/`
- [ ] Python deps: httpx, websockets installed (pip list | grep)
- [ ] Docker (if Playwright sidecar): docker-compose available
- [ ] Modules: All 9 modules running or ready to start
- [ ] Token: VX11_TOKEN, PLAYWRIGHT_WS_URL env vars set

```bash
# Quick pre-flight
df -h /app/models/
curl -I https://huggingface.co
python3 -c "import httpx, websockets; print('OK')"
docker-compose version
echo $VX11_TOKEN
```

---

## Phase 2B Execution Timeline

Estimated total duration: **~1 hour** (including all hitos)

| Time | Hito | Task | Status |
|------|------|------|--------|
| T+0:00 | 1 | Playwright MCP | ⏳ READY |
| T+0:10 | 2 | Model download | ⏳ READY |
| T+0:30 | 3 | Warmup test | ⏳ READY |
| T+0:45 | 4 | Canonical DB | ⏳ READY |
| T+0:50 | 5 | Schema map | ⏳ READY |
| T+0:55 | 6 | Production check | ⏳ READY |
| T+1:00 | ✅ | ALL COMPLETE | |

---

## Failure Recovery

**If a hito fails:**

1. **Hito 2 (Models) fails:**
   - Check network: `curl -I https://huggingface.co`
   - Check disk space: `df -h /app/models/`
   - Retry: `python3 scripts/hermes_download_test_models.py`
   - Can skip to Hito 4 if models not critical for initial deployment

2. **Hito 3 (Warmup) fails:**
   - Verify models registered: `sqlite3 /app/data/runtime/vx11.db "SELECT COUNT(*) FROM local_models_v2"`
   - Check Switch module running: `curl http://localhost:8002/health`
   - Retry after fixing dependency

3. **Hito 4 (Canonical DB) fails:**
   - Restore from backup: `cp /app/data/backups/vx11.db.canonical_* /app/data/runtime/vx11.db`
   - Check disk free space: `df -h /app/data/`
   - Retry

4. **Hito 6 (Readiness) fails:**
   - Start missing modules: `docker-compose up -d [module]`
   - Check logs: `docker-compose logs [module]`
   - Re-run readiness check

---

## Post-Phase 2B

After all hitos complete successfully:

1. **Commit results:**
   ```bash
   git add docs/audit/
   git commit -m "Phase 2B: ALL HITOS COMPLETE — production ready

   ✅ Playwright MCP: ready
   ✅ 2 models: downloaded + registered (Mistral 7B, Neural Chat 7B)
   ✅ Warmup: verified (rotation, stats tracking)
   ✅ Canonical DB: <500MB (cleaned, optimized)
   ✅ Schema: documented (DB_MAP_v7_FINAL.md/json)
   ✅ Production: all systems healthy"
   ```

2. **Generate final report:**
   ```bash
   cat > docs/audit/PHASE2B_COMPLETION.md << EOF
   # Phase 2B Completion Report
   ...
   EOF
   ```

3. **Tag release:**
   ```bash
   git tag -a v7.1-phase2b -m "Phase 2B complete: production-ready system"
   git push origin v7.1-phase2b
   ```

---

## Next Phases (Post-2B)

- **Phase 3A:** CLI concentrator scoring (copilot-first priority)
- **Phase 3B:** Advanced Hermes discovery (Tier 2/3, web search)
- **Phase 4:** Load testing + performance optimization
- **Phase 5:** Deployment to production infrastructure

---

**PHASE 2B EXECUTION MANDATE:**
Execute each hito in sequence.  
Generate report for each milestone.  
No confirmation needed between hitos.  
Stop only if CRITICAL blocker.  
Final report: docs/audit/PHASE2B_COMPLETION.md

