# VX11 — Copilot Onboarding & Workflows Guide

**Version:** 7.1 | **Date:** 2025-12-16  
**Status:** Production-Ready | **Policy:** Low-Power (MAX2 containers)

---

## Overview

This document consolidates the complete Copilot integration setup for VX11, including custom instructions, prompt files, GitHub workflows, and local task automation. All files respect the **low-power policy** and **MAX2 container limit** to prevent resource saturation on Lenovo hardware.

---

## PART A: Custom Instructions + Path Rules

### 📋 Files Created/Updated

| File | Purpose |
|------|---------|
| `.github/copilot-instructions.md` | Global Copilot instructions (v7.1) |
| `.github/instructions/vx11-core.instructions.md` | Module-specific rules (HTTP-only, no cross-imports) |
| `.github/instructions/docs-audit.instructions.md` | Audit & documentation standards |
| `.github/instructions/workflows.instructions.md` | GitHub Actions best practices |
| `.vscode/settings.json` | Enable prompt files (`chat.promptFiles: true`) |

### 🎯 Key Rules (Absolute)

#### Zero-Coupling Policy
- ❌ **NO direct imports** between modules (tentaculo_link, madre, switch, hermes, etc.)
- ✅ **ONLY HTTP calls** via `settings.{module}_url` with auth header `X-VX11-Token`
- ✅ Single BD: `config.db_schema.get_session("vx11")` → `/data/runtime/vx11.db`

#### Database Pattern
```python
from config.db_schema import get_session, Task

db = get_session("vx11")  # Always unified DB
try:
    # ... operations ...
finally:
    db.close()  # MANDATORY to prevent memory leaks
```

#### Logging & Forensics
```python
from config.forensics import write_log

write_log("mi_modulo", "evento", level="INFO")
# Logs to: forensic/mi_modulo/logs/YYYY-MM-DD.log
```

---

## PART B: Prompt Files (for Copilot Chat)

### 📁 Location: `.github/prompts/`

Available in Copilot Chat via `chat.promptFiles: true` (enabled in settings.json).

#### 1. **VX11_Status.prompt.md**
Quick health check in low-power mode.
- Max 2 containers
- Sample health checks (ports 8000, 8001, 8002)
- Report format reference

**Usage:**
```
@copilot: use .github/prompts/VX11_Status.prompt.md
```

#### 2. **VX11_Audit_LowPower.prompt.md**
Complete audit respecting MAX2 policy.
- Enforce MAX2 before starting
- Static checks (no containers): python compile, imports, YAML
- Runtime checks (minimal): health, logs (tail-only), drift sample
- Generate timestamped report in `docs/audit/`

**Usage:**
```
@copilot: use .github/prompts/VX11_Audit_LowPower.prompt.md
```

#### 3. **VX11_DBMAP.prompt.md**
Database schema and quick-reference queries.
- Main tables (Task, IADecision, OperatorSession, etc.)
- Connect & query patterns
- Useful queries (errors, performance, health)
- Maintenance (cleanup >30d records)

**Usage:**
```
@copilot: use .github/prompts/VX11_DBMAP.prompt.md
```

#### 4. **VX11_Workflows.prompt.md**
GitHub Actions and local task reference.
- Available workflows (ci, audit-static, autosync)
- Local tasks (Status, Stop All, Audit Runtime, Enforce MAX2)
- Trigger methods (workflow_dispatch, push, manual GitHub UI)
- Best practices (CI → autosync chain, MAX2 enforcement)

**Usage:**
```
@copilot: use .github/prompts/VX11_Workflows.prompt.md
```

---

## PART C: GitHub Workflows (Adjusted)

### 📋 Files Updated/Created

| Workflow | Trigger | Purpose | Concurrency |
|----------|---------|---------|-------------|
| `ci.yml` | push, PR, dispatch | Python compile, lint, tests, frontend build | Cancel in-progress |
| `vx11-validate.yml` | PR, feature branch, dispatch | Syntax, cross-module imports, docker config | Cancel in-progress |
| `vx11-audit-static.yml` | dispatch, daily (00:00 UTC), file changes | Static analysis (no containers) | Cancel in-progress |
| `vx11-autosync.yml` | dispatch, selective push | Auto-repair (gated by CI pass) | Cancel in-progress |

### ✅ Standards Applied (All Workflows)

1. **Concurrency Policy** (NEW)
   ```yaml
   concurrency:
     group: vx11-{workflow}-${{ github.ref }}
     cancel-in-progress: true
   ```
   - Cancels previous runs if new push detected
   - Prevents resource saturation on GitHub runners

2. **Permissions (Least Privilege)** (NEW)
   ```yaml
   permissions:
     contents: read
     pull-requests: read
   ```
   - Most workflows only READ, no write/admin

3. **Artifacts (v4)** (UPGRADED)
   - Changed from `actions/upload-artifact@v3` → `@v4`
   - Added `retention-days: 30` (auto-cleanup)
   - Reports saved to `docs/audit/` with timestamps

4. **Workflow Dispatch** (NEW)
   - All workflows support manual trigger from GitHub UI
   - Example: Actions → vx11-ci → "Run workflow"

### 🔍 Static Audit Workflow (`vx11-audit-static.yml`) — NEW

**Purpose:** Run analysis without needing containers or local infrastructure.

**Checks Performed:**
- ✅ Python syntax (py_compile)
- ✅ Cross-module imports (grep pattern detection)
- ✅ Docker Compose validity
- ✅ Port conflicts
- ✅ Module directory structure
- ✅ Secrets in code (grep for tokens)
- ✅ Endpoint inventory (sample)
- ✅ YAML linting (workflows)

**Duration:** <1 min | **Resources:** Minimal

**Triggers:**
- `workflow_dispatch` (manual)
- Daily schedule (00:00 UTC)
- File changes in core modules/workflows

**Output:** `docs/audit/AUDIT_STATIC_<timestamp>.md` + artifact

---

## PART D: Local VS Code Tasks

### 🎯 Available Tasks (`.vscode/tasks.json`)

Run via: **Ctrl+Shift+P → Tasks: Run Task** or from Terminal.

#### Core Ops (LOW-POWER)

| Task | Command | Purpose | MAX2 Enforced |
|------|---------|---------|---------------|
| **VX11: Status (Low-Power)** | Docker ps + curl health | Quick system check | ✅ YES |
| **VX11: Enforce MAX2 Containers** | Stop excess, keep 2 max | Enforce policy | ✅ DIRECT |
| **VX11: Stop All Containers** | docker compose stop | Safe shutdown | ✅ Result |
| **VX11: Start Module (Select)** | Interactive module picker | Start 1 module only | ✅ Enforced |
| **VX11: Audit Runtime (Low-Power)** | Shell script (bash) | Full audit respecting MAX2 | ✅ Built-in |
| **VX11: Clean Logs (Archive Old)** | Move logs >30d | Maintenance | N/A |

#### Validation & CI

| Task | Command | Purpose |
|------|---------|---------|
| **VX11: Validate (Static)** | Python script | Python syntax, imports, docker-compose |
| **VX11: CI Pipeline** | Python script | Full CI (lint, tests, frontend) |
| **VX11: Autosync** | Python script | Auto-repair (gated) |

#### Diagnostic

| Task | Command | Purpose |
|------|---------|---------|
| **VX11: Gateway Status** | curl with jq | Query /vx11/status |
| **VX11: Manifestator Drift** | curl with jq | Query drift detection |
| **VX11: Run Tests Suite** | pytest | Full test suite, save to logs/ |

### 📝 Example Usage

```bash
# 1. Quick status
Ctrl+Shift+P → VX11: Status (Low-Power)
# Output: container count, ports 8000/8001/8002 health

# 2. Enforce MAX2 before audit
Ctrl+Shift+P → VX11: Enforce MAX2 Containers
# Output: stops excess, confirms 2 or fewer running

# 3. Run comprehensive audit
Ctrl+Shift+P → VX11: Audit Runtime (Low-Power)
# Output: health table, logs sample, drift check, report in docs/audit/

# 4. Clean up old logs
Ctrl+Shift+P → VX11: Clean Logs (Archive Old)
# Output: moves forensic logs >30 days to docs/audit/archive/YYYY-MM-DD/
```

---

## PART E: Integration Guide (For Copilot)

### 🤖 How Copilot Interacts

1. **Via Chat Prompts**
   ```
   @copilot: use .github/prompts/VX11_Status.prompt.md to check health
   ```
   - Copilot reads prompt file
   - Follows instructions (max 2 containers, tail-only logs, etc.)
   - Auto-approves safe commands (curl, docker ps, python)

2. **Via Custom Instructions**
   ```
   Copilot reads .github/copilot-instructions.md (global)
     + .github/instructions/vx11-core.instructions.md (if in modules/)
     + .github/instructions/docs-audit.instructions.md (if in docs/)
     + .github/instructions/workflows.instructions.md (if in .github/workflows/)
   ```
   - Context-aware rules applied automatically
   - No need to repeat "don't cross-import" — it's built in

3. **Via Settings.json**
   ```json
   "chat.promptFiles": true,
   "chat.tools.terminal.autoApprove": {
     "/^curl\\b.*localhost/": true,
     "/^docker\\s+compose\\s+(ps|logs)/": true,
     ...
   }
   ```
   - Auto-approves safe read-only commands
   - Denies dangerous ops (rm, git reset, docker compose down)

### 🔐 Auto-Approval Rules (Settings.json)

**Auto-Approved (Safe, Read-Only):**
- `git status`, `git diff`, `git log`
- `curl` (localhost only)
- `docker compose ps`, `docker compose logs`
- `head`, `tail`, `grep`, `find`, `ls`, `wc`
- `python3 scripts/vx11_*.py`
- `python -m py_compile`

**Denied (Destructive):**
- `rm`, `mv`
- `sudo`, `chmod`, `chown`
- `docker compose down`
- `git reset --hard`, `git clean -fd`
- `git push`
- Anything accessing `tokens.env`

---

## Low-Power Policy & MAX2 Explanation

### Why MAX2?

VX11 modules consume ~512MB RAM each (ultra-low-memory mode). Lenovo hardware limits:
- Running 3+ containers → memory pressure, slowdown
- Running 2 containers → normal performance
- Running 1 container → optimal audit experience

### Enforcement Points

1. **Copilot Chat Prompts** — automatically enforce MAX2 before ops
2. **Local Tasks** — `VX11: Enforce MAX2 Containers` task stops excess
3. **GitHub Workflows** — concurrency policy prevents simultaneous runs

### What Happens if >2 Running?

1. Auto-detected by audit tasks
2. Excess containers stopped (not killed)
3. Reports warn if MAX2 policy violated
4. Autosync blocked until compliance

---

## Maintenance Schedule

### Weekly
- Run `VX11: Status (Low-Power)` to confirm all ports healthy
- Review `docs/audit/` for any warnings

### Monthly
- Run `VX11: Clean Logs (Archive Old)` to archive forensics >30d
- Compress old `docs/audit/archive/YYYY-MM-DD/` folders if >10 exist

### Per-Release (Before CI)
1. Enforce MAX2: `VX11: Enforce MAX2 Containers`
2. Static audit: GitHub Actions → vx11-audit-static
3. Run CI: GitHub Actions → ci (or local `VX11: CI Pipeline`)
4. Autosync (if needed): `VX11: Autosync`

---

## Troubleshooting

### Prompt Files Not Showing in Chat?
- ✅ Confirm `"chat.promptFiles": true` in `.vscode/settings.json`
- ✅ Reload VS Code: Ctrl+Shift+P → Developer: Reload Window
- ✅ Files must be in `.github/prompts/` with `.prompt.md` extension

### Workflow Fails with "Too many containers"?
- ✅ Run task: `VX11: Enforce MAX2 Containers`
- ✅ Then re-run workflow from GitHub UI

### Autosync Blocked (Secrets Detected)?
- ✅ Check: `git status | grep -E "\.env|tokens"`
- ✅ If exposed: rotate credentials immediately
- ✅ Fix: remove from `.gitignore` violations, re-commit

### Audit Report Too Large?
- ✅ Check: `wc -l docs/audit/AUDIT_*.md`
- ✅ If >1000 lines: verify no full log dumps (use head/tail)
- ✅ Compress & move to archive: `tar czf audit.tar.gz docs/audit/AUDIT_*.md`

---

## Files Touched (Audit)

### Created
- ✅ `.github/instructions/vx11-core.instructions.md`
- ✅ `.github/instructions/docs-audit.instructions.md`
- ✅ `.github/instructions/workflows.instructions.md`
- ✅ `.github/prompts/VX11_Status.prompt.md`
- ✅ `.github/prompts/VX11_Audit_LowPower.prompt.md`
- ✅ `.github/prompts/VX11_DBMAP.prompt.md`
- ✅ `.github/prompts/VX11_Workflows.prompt.md`
- ✅ `.github/scripts/audit_runtime_lowpower.sh`
- ✅ `.github/workflows/vx11-audit-static.yml`

### Updated
- ✅ `.vscode/settings.json` — added `"chat.promptFiles": true`
- ✅ `.vscode/tasks.json` — expanded with 10 low-power tasks
- ✅ `.github/workflows/ci.yml` — added concurrency, permissions, v4 artifacts
- ✅ `.github/workflows/vx11-validate.yml` — added concurrency, permissions
- ✅ `.github/workflows/vx11-autosync.yml` — added concurrency, permissions

### Not Modified (Already Compliant)
- ✅ `.github/copilot-instructions.md` — v7.1 complete

---

## Validation Checklist

Before committing:

- [ ] `git diff .github/ | head -50` — no secrets in diff
- [ ] `git diff .vscode/ | head -50` — reasonable size
- [ ] `yamllint .github/workflows/*.yml` — all YAML valid
- [ ] `.github/prompts/*.md` — all readable, no code inside
- [ ] `.github/scripts/audit_runtime_lowpower.sh` — is executable (`chmod +x`)
- [ ] Settings.json — valid JSON (can parse)
- [ ] Tasks.json — valid JSON (can parse)
- [ ] No files outside `.github/`, `.vscode/`, or `docs/audit/` created

---

## Next Steps for Operators

1. **First time?**
   - Read this doc: `docs/audit/VX11_COPILOT_ONBOARDING_AND_WORKFLOWS.md` (this file)
   - Run: `VX11: Status (Low-Power)` from VS Code tasks
   - Review outputs

2. **Daily workflow?**
   - Enforce MAX2: `VX11: Enforce MAX2 Containers`
   - Quick audit: `VX11: Audit Runtime (Low-Power)`
   - Check report: `docs/audit/AUDIT_RUNTIME_*.md`

3. **Before push to main?**
   - Static validate: `VX11: Validate (Static)`
   - Run CI: `VX11: CI Pipeline` or GitHub Actions
   - Autosync (if needed): `VX11: Autosync`

4. **Monthly maintenance?**
   - Clean logs: `VX11: Clean Logs (Archive Old)`
   - Archive old reports: compress & move to `docs/audit/archive/`
   - Review forensics: `forensic/*/logs/` should be <100MB total

---

## Support & Escalation

**Questions?** Refer to:
- Copilot instructions: `.github/copilot-instructions.md`
- Module rules: `.github/instructions/vx11-core.instructions.md`
- Workflow reference: `.github/prompts/VX11_Workflows.prompt.md`
- DB queries: `.github/prompts/VX11_DBMAP.prompt.md`

**Blocked?**
- Secrets exposed → see `Troubleshooting` section above
- Workflow failing → check concurrency + permissions in `.yml`
- MAX2 enforced → run `VX11: Enforce MAX2 Containers`

---

**VX11 v7.1 — Copilot-Ready, Low-Power, Secure, Maintainable**

Generated: 2025-12-16  
Policy: MAX2 containers, concurrency cancel-in-progress, artifact v4, least-privilege perms
