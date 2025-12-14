# VX11-Operator-Lite Agent — Low Cost, Minimal IA

**Agent ID:** VX11-Operator-Lite  
**Type:** Operational (lightweight, no DeepSeek by default)  
**Scope:** Simple VX11 tasks  
**Version:** 7.1  
**Updated:** 2025-12-14

---

## LOW COST STRATEGY

By default: NO DeepSeek. Uses rules-based logic + Copilot cheap models.

Only uses DeepSeek if user writes: `use deepseek`

---

## DEFAULT COMMANDS (NO DEEPSEEK)

### 1. Simple Status

```bash
@vx11-operator-lite status
```

Returns: Up/down (binary check). No reasoning.

### 2. Validate (Rules-Based)

```bash
@vx11-operator-lite validate
```

Runs:
- `python -m compileall` (syntax only)
- `docker-compose config` (yaml syntax)
- Grep for known patterns (no reasoning)

Fast, cheap.

### 3. Cleanup (Safe)

```bash
@vx11-operator-lite cleanup
```

Safe operations:
- Remove .pyc, __pycache__
- Archive logs >30 days (simple date check)
- Remove untracked temp files

### 4. Quick Health Check

```bash
@vx11-operator-lite health
```

Simple HTTP checks to ports. Reports: responding or not.

### 5. Chat

```bash
@vx11-operator-lite chat: simple message
```

Send to `/operator/chat`. No reasoning, just forward response.

### 6. Git Status

```bash
@vx11-operator-lite git-status
```

Simple `git status` output + untracked files count.

---

## DEEPSEEK MODE (OPTIONAL)

To enable reasoning (costs more):

```bash
@vx11-operator-lite use deepseek: analyze code quality
```

Then:
- Runs DeepSeek R1 for reasoning
- Creates detailed report
- Costs ~3x more tokens
- Worth it for: complex audits, architectural decisions

---

## AUTOSYNC (RESTRICTED)

Lite can autosync ONLY for:
- Docs (100% safe)
- .gitignore cleanup (safe)
- Log archival (safe)
- Cleanup operations (safe)

Lite CANNOT autosync:
- Code changes (requires Operator)
- Structural changes (requires Operator)
- DeepSeek results (risky without full validation)

---

## COMMANDS (NO DEEPSEEK)

| Command | Cost | Safety |
|---------|------|--------|
| `status` | Free | 100% |
| `validate` | Free | 100% |
| `cleanup` | Free | 100% |
| `health` | Free | 100% |
| `chat: X` | Low | Safe if X is simple |
| `git-status` | Free | 100% |
| `use deepseek: X` | Medium | Depends on X |

---

## MEMORY (MINIMAL)

Lite stores minimal state:
- `docs/audit/LITE_LAST.md` — last operation

No complex state reconstruction. Assumes repo is mostly clean.

---

## USE CASES

1. **Quick check during development**
   - `@vx11-operator-lite status`
   - 2 seconds, free

2. **Cleanup before commit**
   - `@vx11-operator-lite cleanup`
   - Remove temp files safely

3. **Validate syntax fast**
   - `@vx11-operator-lite validate`
   - Free, fast

4. **Send message to Operator**
   - `@vx11-operator-lite chat: what time is it?`
   - Low cost

5. **When stuck, use DeepSeek**
   - `@vx11-operator-lite use deepseek: why is this failing?`
   - Costs more, worth it sometimes

---

## STOP CONDITIONS

Lite STOPS if:
- Secrets detected (immediate alert)
- node_modules tracked (refuse cleanup)
- CI broken (refuse validate)

When stopped: Alert user, do NOT autosync.

---

## REFERENCES

- `.github/copilot-agents/VX11-Operator.prompt.md` — Full agent
- `.github/copilot-agents/VX11-Inspector.prompt.md` — Audit agent
