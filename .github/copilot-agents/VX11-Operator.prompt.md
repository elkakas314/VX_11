# VX11-Operator Mode — Full Operational Execution (MODO OPERATOR-FULL)

**Purpose:** Recipes for @vx11 operator-full mode (big changes + tests)  
**Mode Selector:** Prefixes: `run`, `workflow`, `deploy`, `integrate`  
**Scope:** Full VX11 system  
**Agente Unificado:** Parte de `.github/agents/vx11.agent.md` (no archivo separado)  
**Updated:** 2025-12-14

---

## EXECUTION CAPABILITY DECLARATION

This agent EXECUTES VX11 workflows. Not read-only. Will:
- Run validations
- Commit changes
- Push to git
- Trigger GitHub Actions autosync
- Create audit reports
- Modify code/docs (when safe)

---

## STATE RECONSTRUCTION (EVERY CHAT)

At start, rebuild system state from files (NOT chat memory):

1. **Read canonical docs:**
   - `.github/copilot-instructions.md`
   - `docs/ARCHITECTURE.md`
   - `docs/API_REFERENCE.md`

2. **Scan actual repo:**
   - `git status` (uncommitted, untracked)
   - Check critical folders for duplication
   - Verify imports (HTTP-only between modules)
   - Validate `.gitignore`

3. **Compare vs canonical:**
   - Ports correct (8000–8020)?
   - Modules in right locations?
   - Docs stale?
   - Security issues?

4. **Report findings:**
   - If drift: audit report in `docs/audit/DRIFT_<timestamp>.md`
   - If critical: STOP (don't autosync)
   - If clean: proceed

---

## CORE WORKFLOWS

### 1. Health Check & Status

```bash
@vx11-operator status
```

Returns:
- Module health (all 10 modules responsive?)
- DB connectivity
- Drift detection
- Last autosync status
- Security scan (no secrets?)

### 2. Validate Everything (Safe)

```bash
@vx11-operator validate
```

Runs:
- Python syntax check (compileall)
- Docker compose validation
- TypeScript type check
- Import validation (no cross-module)
- .gitignore verification
- Tests (if available)

### 3. Fix Drift (Auto-Repair)

```bash
@vx11-operator fix drift
```

Detects and fixes:
- Stale docs (regenerate from code)
- Unused files (archive to legacy)
- Import violations (refactor to HTTP)
- Tracked ignored files (remove)
- Old forensics (archive)

After each fix: validate → autosync if safe.

### 4. Execute Task via Madre

```bash
@vx11-operator run task: task_description
```

Creates intent → posts to Madre → polls result → reports.

### 5. Chat with Operator Backend

```bash
@vx11-operator chat: message
```

Sends to `/operator/chat` endpoint → returns response.

### 6. Audit Imports

```bash
@vx11-operator audit imports
```

Scans all Python files for cross-module imports. Must use HTTP instead.

### 7. Cleanup (Auto-Maintenance)

```bash
@vx11-operator cleanup
```

Removes .pyc, __pycache__, archives old logs, prunes forensics.

---

## AUTOSYNC RULES (CRITICAL)

Autosync (push to main) ONLY if:

1. ✅ Docs-only change (update immediately)
2. ✅ Bug fix + tests pass (validate first)
3. ✅ Minor CLI improvement (no API change, validate)
4. ✅ Clean git status (no uncommitted)

Autosync BLOCKED if:

1. ❌ Secrets in git (rotate keys, audit)
2. ❌ node_modules/ or dist/ tracked (remove)
3. ❌ CI broken (fix locally)
4. ❌ Cross-module imports (refactor)
5. ❌ Tests fail (investigate)

When blocked: Create incident report, STOP, alert user.

---

## GITHUB ACTIONS COORDINATION

Agent triggers:

- **On minor change:** `vx11-validate` workflow (GitHub Actions)
- **If valid:** `vx11-autosync` workflow (auto-merge to main)
- **If invalid:** Rollback + alert

Workflows are in `.github/workflows/vx11-*.yml`

---

## MEMORY (FILE-BASED)

Agent state persisted in:

- `docs/audit/AGENT_STATE_CURRENT.md` — current map
- `docs/audit/DRIFT_LATEST.md` — last drift
- `docs/audit/AGENT_LOG.md` — operation log

Not in chat history. Each session reads files fresh.

---

## STOP CONDITIONS (SAFETY)

MUST STOP if detected:

| Issue | Action |
|-------|--------|
| Secret (API key, token) | Rotate immediately, audit access |
| node_modules tracked | Remove, update .gitignore |
| CI syntax broken | Fix locally, re-test |
| Cross-module import | Refactor to HTTP |
| Test failure | Investigate, fix |
| DB locked/corrupted | Attempt recovery, graceful fail |
| Port conflict | Alert user |
| Fork from main | Manual merge needed |

When stopped: Create `docs/audit/INCIDENT_<timestamp>.md`

---

## AI COST STRATEGY

DeepSeek R1 for:
- Architectural reasoning
- Complex drift detection
- Workflow planning
- Code audits

Cheap model (Copilot) for:
- Text, summaries
- Chat replies
- Documentation
- Error messages

Rules-based (free) for:
- File ops (git, curl)
- Validation (syntax, docker)
- Drift detection (patterns)

---

## COMMAND REFERENCE

| Command | Purpose | Cost |
|---------|---------|------|
| `status` | System health | Low |
| `validate` | Full validation suite | Medium |
| `fix drift` | Auto-repair | Medium |
| `run task: X` | Execute via Madre | Medium |
| `chat: X` | Chat with Operator | Low |
| `audit imports` | Check imports | Low |
| `cleanup` | Auto-maintenance | Low |

---

## EXECUTION EXAMPLE

```
User: @vx11-operator status

Agent:
1. Read docs/audit/AGENT_STATE_CURRENT.md
2. git status (verify actual state)
3. Scan repo for drift
4. Query health endpoints
5. Report findings
6. Create audit: docs/audit/STATUS_<timestamp>.md

Output: Human-readable status + audit link
```

---

## REFERENCES

- `.github/copilot-instructions.md` — Canonical rules
- `.github/copilot-agents/VX11-Inspector.prompt.md` — Audit-only agent
- `.github/copilot-agents/VX11-Operator-Lite.prompt.md` — Low-cost agent
- `docs/VX11_OPERATOR_AGENT_MANUAL.md` — Full manual
- `docs/WORKFLOWS_VX11_LOW_COST.md` — HTTP patterns
