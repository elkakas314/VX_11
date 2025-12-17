---
applyTo: "**/*"
---
# VX11 — reglas globales
- Respeta AGENTS.md.
- Evidencia y reportes en docs/audit/.
- No duplicados. Actualiza, no clones.
- Consulta DB_MAP/DB_SCHEMA FINAL antes de acciones que toquen BD o estructura.

- Antes de mover archivos a `attic/` o ejecutar scripts de limpieza: cargar `docs/audit/CLEANUP_EXCLUDES_CORE.txt` y aplicar hard-exclude. Si un path CORE aparece en la lista de candidatos => ABORTA y reporta en `docs/audit/`.
- Forense: `forensic/crashes` NUNCA se borra; solo se ARCHIVA en `docs/audit/archived_forensic/`.
