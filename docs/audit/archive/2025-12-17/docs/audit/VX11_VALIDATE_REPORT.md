# VX11 Validate Report

**Timestamp**: 2025-12-16T23:33:30.968338Z

### Syntax Python
`python3 -m py_compile scripts/vx11_*.py`
**Status**: ✅ OK
```

```

### Prompts
`python3 scripts/validate_prompts.py`
**Status**: ❌ FAIL
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
❌ ERRORES ENCONTRADOS (1):

  ⚠ vx11_builder.agent.md: Tool OBSOLETA 'terminal' (migrar a válida)

```

### Git Status
`git status --short`
**Status**: ✅ OK
```
 M .github/copilot-instructions.md
 M .github/workflows/ci.yml
 M config/container_state.py
 M config/db_schema.py
 M docs/audit/VX11_AGENT_BOOTSTRAP_REPORT.md
 D forensic/crashes/CRASH_20251216T032116Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T032116Z/main.py
 D forensic/crashes/CRASH_20251216T032117Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T032117Z/main.py
 D forensic/crashes/CRASH_20251216T033751Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T033751Z/main.py
 D forensic/crashes/CRASH_20251216T033803Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T033803Z/main.py
 M madre/main.py
 M mcp/main.py
 M mcp/tools_wrapper.py
 M vx11.code-workspace
?? .github/agents/vx11_builder.agent.md
?? .github/instructions/vx11_global.instructions.md
?? .github/instructions/vx11_workflows.instructions.md
?? .github/prompts/vx11_cleanup.prompt.md
?? AGENTS.md
?? docs/audit/ULTRA_AUDIT_2025-12-16/
?? docs/audit/VX11_AUTOSYNC_REPORT.md
?? docs/audit/archive/
?? forensic/crashes/CRASH_20251216T231822Z/
?? forensic/crashes/CRASH_20251216T231830Z/
?? forensic/crashes/CRASH_20251216T231832Z/
?? forensic/crashes/CRASH_20251216T231833Z/
?? forensic/crashes/CRASH_20251216T231834Z/

```

