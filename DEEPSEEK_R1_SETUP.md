# DeepSeek R1 Configuration for VX11 (31-DEC-2025)

## Status: ✅ OPERATIONAL

### Configuration Files
- **API Key**: `.env.deepseek` (present, loaded from env)
- **SDK**: `openai` (installed, v1.14+)
- **Model**: `deepseek-reasoner` (available at api.deepseek.com)
- **Audit Trail**: `docs/audit/r1/` (auto-saving, gitignored)

### Test Results
- ✅ API connection: successful
- ✅ Model availability: deepseek-reasoner confirmed
- ✅ JSON reasoning: working (complex plan generated)
- ✅ Audit logging: plans saved with timestamps

### Available Tools

#### 1. Direct Reasoning Call
```bash
python3 deepseek_wrapper.py "<objective>" "[context]" "[task]"
```

**Example**:
```bash
python3 deepseek_wrapper.py \
  "Plan database migration" \
  "VX11: single entrypoint, solo_madre default" \
  "Migrate from SQLite to PostgreSQL"
```

#### 2. Integration with @vx11 Tasks
Copilot will automatically:
1. Detect MANDATORY R1 calls (merges, contracts, .github changes)
2. Call `deepseek_wrapper.py` with task context
3. Parse JSON output → tasks[]
4. Execute tasks in order
5. Verify against definition_of_done[]

#### 3. Environment Variables
```bash
# Already configured (read from .env.deepseek)
export DEEPSEEK_API_KEY="sk-..."
```

### Integration with Copilot Workflow

When Copilot receives a VX11 task:

```python
# Pseudo-code (actual in Copilot behavior)
if task_is_mandatory_r1_call():
    plan = run_deepseek_wrapper(objective, context, task)
    tasks = plan["tasks"]
    
    for task in tasks:
        execute_commands(task["commands"])
        verify(task["done_when"])
    
    verify_definition_of_done(plan["definition_of_done"])
    save_audit(f"docs/audit/vx11_task_{timestamp}/")
```

### Output Format (Standard JSON)

Every DeepSeek R1 call produces:

```json
{
  "tasks": [
    {
      "id": "T1",
      "description": "...",
      "files": ["..."],
      "commands": ["..."],
      "done_when": "..."
    }
  ],
  "risks": [
    {
      "risk": "...",
      "severity": "low|med|high",
      "mitigation": "..."
    }
  ],
  "tests_to_run": ["..."],
  "rollback_plan": ["..."],
  "definition_of_done": ["..."],
  "reasoning": "explanation of decisions"
}
```

### Verification
```bash
# Check if DeepSeek is ready
python3 deepseek_wrapper.py "test" "VX11" "test reasoning"

# Should output JSON with reasoning and plans
```

### Security Notes
- ✅ API key only read from `.env.deepseek` (never printed)
- ✅ All plans audit-logged in `docs/audit/r1/`
- ✅ No secrets in commit history
- ✅ Environment variables never exposed in code

### Files Modified/Created
- `test_deepseek_r1.py` — Verificación inicial (committed)
- `deepseek_wrapper.py` — Wrapper principal (committed)
- `docs/audit/r1/` — Auto-generated plans (gitignored, audit trail)
- `docs/audit/deepseek_config/test_result_*.txt` — Test logs (gitignored)

---

**Ready for VX11 tasks with DeepSeek R1 reasoning enabled.**
