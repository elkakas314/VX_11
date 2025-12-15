# VX11 Validate Report

**Timestamp**: 2025-12-15T05:05:21.265643Z

### Syntax Python
`python3 -m py_compile scripts/vx11_*.py`
**Status**: ❌ FAIL
```

```

### Prompts
`python3 scripts/validate_prompts.py`
**Status**: ✅ OK
```
======================================================================
VALIDACIÓN: Agentes, Prompts e Instrucciones de Copilot
======================================================================

1. Validando .github/agents/*.agent.md...
  ✓ vx11.agent.md

2. Validando .github/copilot-agents/*.prompt.md...
  ✓ VX11-Inspector.prompt.md
  ✓ VX11-Operator-Lite.prompt.md
  ✓ VX11-Operator.prompt.md

3. Validando links en .github/copilot-instructions.md...
  ✓ Todos los links existen

======================================================================
✅ VALIDACIÓN OK: 0 errores detectados

```

### Git Status
`git status --short`
**Status**: ✅ OK
```
 M .github/agents/vx11.agent.md
 M .github/copilot-instructions.md
 M .github/workflows/ci.yml
 M .github/workflows/vx11-autosync.yml
 M .github/workflows/vx11-validate.yml
A  docs/audit/PLAN_A_F_COMPLETION_REPORT.md
 M docs/audit/VX11_AGENT_BOOTSTRAP_REPORT.md
 M vx11.code-workspace
?? docs/audit/VX11_AGENT_IMPLEMENTATION_REPORT.md
?? docs/audit/VX11_API_DISCOVERY.md
?? docs/audit/VX11_RUNTIME_TRUTH_REPORT.md
?? docs/audit/VX11_STATUS_REPORT.md
?? docs/audit/VX11_VALIDATE_REPORT.md
?? scripts/vx11_export_canonical_state.py
?? scripts/vx11_runtime_truth.py
?? scripts/vx11_task_router.py
?? scripts/vx11_workflow_runner.py

```

