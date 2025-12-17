# VX11 Workflows Guide

Reference for running CI, audits, and autosync from Copilot Chat.

## Available Workflows

### 1. vx11-ci (Continuous Integration)
**Trigger:** `push` or `workflow_dispatch`

**What it does:**
- Python syntax check (compile all)
- Linting (pylint, black)
- YAML validation (docker-compose)
- Frontend build (React 18, Vite)
- Tests (pytest)

**From Copilot:**
```
@copilot run workflow: vx11-ci
```

**Manually (GitHub UI):**
- Actions → vx11-ci → Run workflow → main branch

**Expected time:** ~3–5 minutes

---

### 2. vx11-audit-static (Static Analysis)
**Trigger:** `workflow_dispatch`

**What it does:**
- File structure validation (no duplicates)
- Import cross-check (no inter-module imports)
- Drift detection (file hashing)
- Endpoint inventory (grep all /endpoints)

**From Copilot:**
```
@copilot run workflow: vx11-audit-static
```

**Expected time:** ~1–2 minutes

---

### 3. vx11-autosync (Auto-Repair)
**Trigger:** `workflow_dispatch` (gated, requires CI PASS)

**What it does:**
- Runs full validation (CI + audit)
- Detects issues (security, formatting, structure)
- Generates patches (auto-repair suggestions)
- Applies if safe (tests PASS)
- Creates PR with changes or docs if not auto-appliable

**Blockers (stops autosync if detected):**
- Secrets exposed
- node_modules or dist/ tracked
- Tests failing
- CI workflow broken
- Port conflicts

**From Copilot:**
```
@copilot run workflow: vx11-autosync
```

**⚠️ Manual approval required if changes suggested.**

**Expected time:** ~5–10 minutes

---

## Local Tasks (`.vscode/tasks.json`)

Run from VS Code Terminal or Copilot Chat:

### VX11: Status
```bash
python3 scripts/vx11_workflow_runner.py status
```
- Lists containers, health, ports
- Enforces MAX2 policy
- Time: <10 seconds

### VX11: Stop All
```bash
docker compose stop
```
- Stops ALL containers
- Safe to run before audit
- Time: ~5 seconds

### VX11: Start <module>
```bash
docker compose up -d <module>
# e.g.: tentaculo_link, madre, switch, etc.
```
- Starts only one module
- Check health: `curl http://127.0.0.1:PORT/health`
- Time: ~3–5 seconds

### VX11: Audit Runtime (Low-Power)
```bash
python3 scripts/vx11_audit_runtime_lowpower.py
```
- Enforces MAX2, runs checks, saves report
- Report: `docs/audit/AUDIT_LowPower_*.md`
- Time: ~2–5 minutes

### VX11: Enforce MAX2
```bash
# Inline bash in tasks.json
RUNNING=$(docker compose ps --services --filter "status=running" | wc -l)
if [ $RUNNING -gt 2 ]; then
  docker compose stop
fi
```
- Kills excess containers
- Time: <5 seconds

---

## Workflow Dispatch (Manual GitHub UI)

1. Go to **GitHub.com → Your Repo → Actions**
2. Select workflow (e.g., `vx11-ci`)
3. Click **Run workflow**
4. Select branch + optional inputs
5. Click **Run workflow**

---

## Artifact Downloads

After workflow completes:
1. Go to **Actions → Run Details**
2. Scroll down → **Artifacts**
3. Download (e.g., `vx11-audit-report`)
4. Unzip and review `docs/audit/` files

---

## Troubleshooting

### Workflow Fails on CI
```bash
# Run locally to debug
python -m pytest tests/ -v --tb=short
```

### MAX2 Violation Detected
```bash
# Fix: stop excess containers
docker compose stop
docker compose ps  # verify only 2 or fewer running
```

### Autosync Blocked (secrets detected)
```bash
# Check .env files
git status | grep -E "\.env|tokens"
# If exposed: rotate credentials immediately
```

### Audit Report Too Large
```bash
# Compress and upload manually
tar czf audit_report.tar.gz docs/audit/
# Reference in ticket/PR
```

---

## Best Practices

1. **Run CI before autosync:** autosync requires CI ✅
2. **Enforce MAX2 before runtime audit:** prevents resource saturation
3. **Check artifact after each workflow:** verify report quality
4. **Archive old reports monthly:** `docs/audit/archive/YYYY-MM-DD/`
5. **Never run >1 workflow simultaneously:** use concurrency policies

---

**Last Update:** 2025-12-16  
**Policy:** Low-power, MAX2 containers, concurrency=cancel-in-progress
