# VX11 LOCAL RUNBOOK
**Last Updated**: 2025-12-31  
**Validator**: GitHub Copilot (DeepSeek R1)  
**Status**: ✅ Production Ready

---

## Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/elkakas314/VX_11.git
cd VX_11
git remote add vx_11_remote https://github.com/elkakas314/VX_11.git  # If needed
```

### 2. Environment (Optional but Recommended)
```bash
# Copy example env file
cp tokens.env.example tokens.env

# Edit if you have DeepSeek API key:
export DEEPSEEK_API_KEY="your-key-here"
```

### 3. Lift Stack (Production Profile)
```bash
# Single-entrypoint architecture
docker compose -f docker-compose.production.yml up -d --build

# Verify services (should be 7/7 healthy)
docker compose -f docker-compose.production.yml ps
```

### 4. Verify Endpoints
```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"ok","module":"tentaculo_link","version":"7.0"}

# System status
curl http://localhost:8000/vx11/status
# Expected: full status with ports, module health, etc
```

---

## Running Tests

### Unit Tests
```bash
pytest tests/ -v --co  # List all tests

# Smoke tests
pytest tests/test_health.py -v

# With testing mode (mocks Hermes without real service)
VX11_TESTING_MODE=1 pytest tests/test_frontdoor_p0_core.py -v
```

### Test Suites (PR #15 additions)
```bash
# Dependency cycles check
pytest tests/test_dependency_cycles.py -v

# Canonical docs presence
pytest tests/test_docs_presence.py -v

# Full P0 core validation
VX11_TESTING_MODE=1 pytest tests/test_frontdoor_p0_core.py -v
```

### All Tests with Coverage
```bash
VX11_TESTING_MODE=1 pytest tests/ -v --cov=. --cov-report=html
open htmlcov/index.html  # View coverage
```

---

## Modules & Profiles

### Default (production.yml)
**Running by default**: `tentaculo_link`, `madre`, `redis`  
**Policy**: SOLO_MADRE (single orchestrator, internal only)

```bash
# Brings up only entrypoint + minimum infrastructure
docker compose -f docker-compose.production.yml up -d
```

### Full Test Profile (optional)
```bash
# If you need full-test profile with switch, operator, hermes
docker compose -f docker-compose.full-test.yml up -d --build
```

---

## Power Windows & Maintenance

### solo_madre (always active)
```bash
# Check current policy
curl http://localhost:8001/madre/power/policy/solo_madre/status

# Apply (already default)
curl -X POST http://localhost:8001/madre/power/policy/solo_madre/apply
```

### Post-task Maintenance
```bash
# After making changes (tests, schema, etc)
curl -X POST http://localhost:8001/madre/power/maintenance/post_task \
  -H "Content-Type: application/json" \
  -d '{"reason":"cleanup after tests"}'
```

### Check Service Status
```bash
curl http://localhost:8001/madre/power/status
```

---

## DeepSeek R1 Integration

### With API Key
```bash
export DEEPSEEK_API_KEY="sk-your-key"
docker compose -f docker-compose.production.yml up -d
# DeepSeek R1 will be active for reasoning tasks
```

### Without API Key (Testing Mode)
```bash
VX11_TESTING_MODE=1 pytest tests/ -v
# Hermes mocking is active; DeepSeek not required
```

### Fallback Behavior
- If `DEEPSEEK_API_KEY` is not set: `switch/deepseek_r1_provider.py` logs warning + returns error
- Tests skip conditionally or mock depending on env vars
- No silent failures

---

## Database Management

### Check DB Integrity
```bash
sqlite3 data/runtime/vx11.db "PRAGMA quick_check;"
sqlite3 data/runtime/vx11.db "PRAGMA integrity_check;"
sqlite3 data/runtime/vx11.db "PRAGMA foreign_key_check;"
```

### View Schema (PR #15 additions)
```bash
# New canonical tables
sqlite3 data/runtime/vx11.db ".tables" | grep -i "module_status\|canonical\|inee\|copilot"

# INEE schema example
sqlite3 data/runtime/vx11.db ".schema inee_colonies"
```

### Backup DB
```bash
cp data/runtime/vx11.db data/backups/vx11_$(date +%Y%m%d_%H%M%S).db
```

---

## Single-Entrypoint Architecture

### ✅ Correct Access Pattern
```bash
# All clients go through tentaculo_link (port 8000)
curl http://localhost:8000/hermes/get-engine
curl http://localhost:8000/vx11/status
curl http://localhost:8000/operator/*
```

### ❌ Never Use
```bash
# These are INTERNAL ONLY (not exposed)
curl http://localhost:8001/...  # madre (internal)
curl http://localhost:8002/...  # switch (internal)
curl http://localhost:8011/...  # operator-backend (internal)
```

### Frontend E2E
```bash
# Operator UI uses correct entrypoint
curl http://localhost:8000/ui
# UI backend requests go to: http://localhost:8000 (tentaculo_link proxy)
```

---

## Debugging Tips

### See Container Logs
```bash
# Tentaculo link
docker compose -f docker-compose.production.yml logs tentaculo_link -f

# Madre
docker compose -f docker-compose.production.yml logs madre -f

# All
docker compose -f docker-compose.production.yml logs -f
```

### Restart Service
```bash
docker compose -f docker-compose.production.yml restart tentaculo_link
```

### Interactive Shell in Container
```bash
docker compose -f docker-compose.production.yml exec tentaculo_link bash
```

---

## Common Issues & Fixes

### "Port 8000 already in use"
```bash
# Find & kill process
lsof -i :8000
kill -9 <PID>

# Or use different port (requires config change)
```

### "DEEPSEEK_API_KEY not configured" (expected warning)
- This is OK in testing mode
- Set `DEEPSEEK_API_KEY` in env to enable live reasoning
- Tests work fine without it (use `VX11_TESTING_MODE=1`)

### Database locked error
```bash
# Rebuild DB (all data will be lost)
rm data/runtime/vx11.db
docker compose -f docker-compose.production.yml up -d
```

---

## CI/CD Integration

### Pre-commit Checks
```bash
# Run before pushing
VX11_TESTING_MODE=1 pytest tests/test_frontdoor_p0_core.py -v
pytest tests/test_dependency_cycles.py -v
pytest tests/test_docs_presence.py -v
```

### GitHub Actions (if configured)
- PR #15 added `.github/workflows/` stubs
- Ensure `VX11_TESTING_MODE=1` in CI env

---

## Validation Checklist

Before marking as "production ready" locally:

- [ ] `docker compose ps` shows all 7/7 healthy
- [ ] `curl http://localhost:8000/health` returns ok
- [ ] `VX11_TESTING_MODE=1 pytest tests/ -v` shows >= 13 passed
- [ ] No hardcoded `:8001`, `:8002`, etc in frontend code
- [ ] `git status` is clean
- [ ] `git log` shows recent commits
- [ ] No exposed secrets in logs

---

## Invariants (Hard Rules)

| Invariant | Enforced By | Verify With |
|-----------|------------|------------|
| Single entrypoint (8000 only) | tentaculo_link router | `docker compose ps` |
| No internal port exposure | docker-compose.yml | `grep -r ":8001\|:8011"` |
| Token guards on proxies | tentaculo_link/main_v7.py | Tests: `test_frontdoor_p0_core.py` |
| Default solo_madre | madre/Dockerfile env | `curl /madre/power/status` |
| No secrets in repo | .gitignore + env vars | `grep -r "DEEPSEEK_API_KEY" src/` (should be 0) |
| DB integrity | PRAGMA checks | `sqlite3 .../vx11.db "PRAGMA quick_check;"` |

---

## Support & Escalation

- **Issues**: See [AGENTS.md](../AGENTS.md)
- **DeepSeek R1 defaults**: See [.github/copilot-instructions.md](../.github/copilot-instructions.md)
- **Architecture**: See [VX11_CONTEXT.md](../VX11_CONTEXT.md)
- **Latest audit**: See [docs/audit/](./audit/)

---

**Last validated**: 2025-12-31 02:35Z  
**PR #15 merge**: Commit 33f2e3f  
**Status**: ✅ PRODUCTION READY
