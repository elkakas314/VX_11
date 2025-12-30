# DeepSeek R1 Configuration for VX11 (31-DEC-2025)

## Status: ✅ OPERATIONAL

### Configuration Files
- **API Key**: `.env.deepseek` (present, loaded from env)
- **SDK**: `openai` (installed, v1.14+)
- **Model**: `deepseek-reasoner` (available at api.deepseek.com)
- **Reasoning Engine**: `.github/deepseek_r1_reasoning.py` (Copilot-only)
- **Audit Trail**: `docs/audit/r1/` (auto-saving, gitignored)

### Architecture
```
Copilot (detects MANDATORY R1 trigger)
    ↓
.github/deepseek_r1_reasoning.py (applies VX11 rails)
    ↓
DeepSeek API (deepseek-reasoner model)
    ↓
Structured JSON plan (tasks, risks, tests, rollback)
    ↓
Execution + Audit trail (docs/audit/r1/)
```

### Test Results
- ✅ API connection: successful
- ✅ Model availability: deepseek-reasoner confirmed
- ✅ JSON reasoning: working (complex plan generated)
- ✅ Rails enforcement: protecting VX11 invariants
- ✅ Audit logging: plans saved with timestamps

### Access & Permissions

| User Type | Access | Method |
|-----------|--------|--------|
| **Copilot** | ✅ Full | Automatic (MANDATORY triggers) |
| **Humans** | ⚠️ Limited | Manual: `@vx11 <task>` (not direct script) |
| **CI/CD** | ⚠️ Controlled | Via Copilot workflow only |

**Why Copilot-only?**
- Ensures safety rails are enforced
- Prevents accidental invariant violations
- Maintains audit trail consistency
- Integrates seamlessly with preflight/gate checks

### Available Tools for Copilot

#### 1. Automatic (Internal to Copilot)
```python
# Triggered automatically when condition matches
if task_requires_deepseek_reasoning():
    plan = deepseek_r1_reasoning(objective, context, task)
    for task in plan["tasks"]:
        execute_task(task)
    verify(plan["definition_of_done"])
```

#### 2. Safety Rails (Enforced)
```
✓ Preserves solo_madre runtime
✓ Protects tentaculo_link entrypoint
✓ Never touches forense/audit trails
✓ Maintains canonical specs
✓ Includes rollback procedures
✓ Specifies verification tests
```

#### 3. Output Format (Standard JSON)
```json
{
  "tasks": [
    {"id": "T1", "description": "...", "commands": [...], "done_when": "..."}
  ],
  "risks": [
    {"risk": "...", "severity": "low|med|high", "mitigation": "..."}
  ],
  "tests_to_run": ["..."],
  "rollback_plan": ["..."],
  "definition_of_done": ["..."],
  "reasoning": "explanation"
}
```

### Integration with Copilot Workflow

**Preflight** (every @vx11 task):
1. ✅ `@vx11 status`
2. ✅ Check if MANDATORY R1 trigger
3. ✅ If YES → invoke `.github/deepseek_r1_reasoning.py`

**Execution**:
1. ✅ Parse JSON plan
2. ✅ Execute tasks in order
3. ✅ Verify each done_when
4. ✅ Run tests
5. ✅ Verify definition_of_done

**Gate Final** (self-review):
1. ✅ Check no violations
2. ✅ Verify rollback readiness
3. ✅ Save audit trail
4. ✅ Commit + push

### Files Modified/Created
- `.github/deepseek_r1_reasoning.py` — Main reasoning engine (Copilot-only)
- `test_deepseek_r1.py` — Test harness (for validation)
- `.github/copilot-instructions.md` — Updated with R1 section
- `docs/audit/r1/` — Auto-generated plans (gitignored)

### Security Notes
- ✅ API key only read from `.env.deepseek` (never printed)
- ✅ Rails prevent invariant violations
- ✅ All plans audit-logged in `docs/audit/r1/`
- ✅ No secrets in commit history
- ✅ Copilot-gated to prevent misuse

---

**VX11 Ready for production with integrated DeepSeek R1 reasoning.**
