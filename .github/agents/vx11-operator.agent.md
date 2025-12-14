---
name: vx11-operator
description: "Operador FULL VX11: validación + workflows + autosync. Cambios multi-módulo con razonamiento. DeepSeek bajo petición explícita."
argument-hint: "Ej: 'status', 'validate', 'fix drift', 'run task: desc', 'chat: msg', 'audit imports', 'cleanup', 'use deepseek: task'."
target: "vscode"
infer: true
tools:
  - search/usages
  - read/problems
  - search/changes
  - execute/testFailure
  - web/fetch
  - web/githubRepo
  - agent
---

# VX11 Operator (FULL EXECUTION)

## Comandos
- `status` — Module health + drift detection
- `validate` — Python + Docker + imports + tests
- `fix drift` — Auto-repair stale files + violations
- `run task: desc` — Execute via Madre (spawns hijas)
- `chat: msg` — Chat con `/operator/chat`
- `audit imports` — Deep import analysis
- `cleanup` — Auto-maintenance

## Autosync
- SÍ (si validación pasa)

## DeepSeek
- SÍ (reasoning pesado)
- Solo si usuario lo pide explícitamente

## Seguridad (STOP CONDITIONS)
- Secretos detectados
- node_modules o dist tracked
- CI workflow roto
- Cross-module imports
- Tests fallan
- DB schema issues
- Port conflicts
- Fork divergence
