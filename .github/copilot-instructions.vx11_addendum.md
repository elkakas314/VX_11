### VX11 Addendum: Bootstrap, Reuse, Status Contract, Git Discipline, Post-task

Este archivo complementa `.github/copilot-instructions.md` con reglas obligatorias específicas para la estabilización del agente VX11.

A) Context Bootstrap obligatorio (refuerzo)
- Antes de cualquier `@vx11` confirmar lectura y existencia de:
  - `.github/agents/vx11.agent.md`
  - `.github/copilot-instructions.md`
  - `docs/canon/*` (archivos JSON canónicos)
  - `forensic/` (últimos items)
  - `docs/audit/DB_SCHEMA_v7_FINAL.json`, `docs/audit/DB_MAP_v7_FINAL.md`, `docs/audit/SCORECARD.json`, `docs/audit/PERCENTAGES.json` (si existen)
- Si falta cualquiera de estas rutas: emitir exactamente `BOOTSTRAP INCOMPLETE: <ruta> not found` y abortar la ejecución del comando.

B) Regla de reutilización de scripts/tests
- Antes de crear `scripts/*` o `tests/*` buscar en el repo (rg/find) artefactos equivalentes y adaptarlos.
- Si no existe nada relacionado: crear el nuevo script/test en la carpeta canónica del módulo correspondiente y acompañarlo de un `README.md` y test mínimo.

C) Contrato fijo de `@vx11 status` (verificación de salida)
- Debe devolver, en este orden: Git, Docker/systemd, Canon (lista+hash+fecha), DB (tamaño+PRAGMAs), Artefactos DB (timestamps de DB_MAP/DB_SCHEMA/SCORECARD/PERCENTAGES), Porcentajes (si existen), Bloqueos exactos.
- Si algún elemento falta, reportar `BLOCKED: <resource> not found at <path> (expected from: <source>)`.

D) Disciplina Git/Remote (refuerzo)
- Remote obligatorio: `vx_11_remote`.
- Mensajes de commit atomicos: `vx11: <module>: <action> + details`.
- `--force` solo para rollback explícito con evidencia en OUTDIR.

E) Post-task automation (cuando proceda)
- Si la tarea toca `config/canon/DB scripts/workflows` seguir el flujo: llamar a `POST /madre/power/maintenance/post_task`, capturar salida en OUTDIR, regenerar DB maps (si existe el script), ejecutar PRAGMAs (solo lectura) y guardar evidencia.

Aplicación: este addendum se añade como refuerzo y no sustituye el contenido original de `.github/copilot-instructions.md`.
