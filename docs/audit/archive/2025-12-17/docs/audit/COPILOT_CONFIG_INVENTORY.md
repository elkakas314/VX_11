# COPILOT CONFIG INVENTORY

Listado de archivos relacionados con agentes, prompts e instrucciones de Copilot en el repo (ruta + función en 1 línea):

- **.github/agents/vx11.agent.md**: Agent principal `vx11` (modo cirujano) — contrato operativo único para VX11.
- **.github/agents/vx11_builder.agent.md**: Plantilla `VX11 Builder` (referencia mental/plantilla, no el agente final).
- **.github/copilot-agents/** (ARCHIVADO → see docs/audit/archived_copilot): directorio con prompts de agentes legacy (Operator/Inspector/Operator-Lite) — ahora archivados.

- **.github/prompts/vx11_dbmap.prompt.md**: Prompt para ejecutar el flujo DBMAP (runner canonical).
- **.github/prompts/vx11_cleanup.prompt.md**: Prompt para limpieza canónica del repo.
- **.github/prompts/VX11_Workflows.prompt.md**: Guía de workflows y comandos recomendados.
- **.github/prompts/VX11_Status.prompt.md**: Snippets para chequeo rápido /health y MAX2.
- **.github/prompts/VX11_DBMAP.prompt.md**: DBMAP quick reference y queries útiles.
- **.github/prompts/VX11_Audit_LowPower.prompt.md**: Prompt para auditoría en modo low-power (MAX2).

- **.github/instructions/vx11_global.instructions.md**: Reglas globales aplicadas a todo el repo (antes de editar).
- **.github/instructions/docs-audit.instructions.md**: Instrucciones para docs/audit y formato de reportes.
- **.github/instructions/vx11_workflows.instructions.md**: Instrucciones para workflows y jobs (dbmap guard).
- **.github/instructions/workflows.instructions.md**: Reglas YAML/CI para workflows (concurrency, artifacts).
- **.github/instructions/vx11-core.instructions.md**: Políticas y reglas por módulo (imports, BD, logs).

- **.github/copilot-instructions.md**: Copilot canonical instructions (actualizado al contrato VX11 minimal).
- **.vscode/settings.json**: Workspace settings para auto-approve de comandos seguros (pwd, ls, git status, pytest, etc.).
- **vx11.code-workspace**: Workspace file (referencia para VS Code workspace settings).

Nota: Los prompts de los agentes `VX11-Operator`, `VX11-Inspector`, `VX11-Operator-Lite` han sido archivados en `docs/audit/archived_copilot/.github/copilot-agents/`.
