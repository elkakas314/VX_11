# CLEANUP EXECUTION PLAN (Plan en seco)

Este documento describe el plan paso-a-paso para ejecutar la limpieza controlada cuando se autorice.

Pre-requisitos

- `docs/REPO_LAYOUT.md` y `docs/CLEANUP_RULES.md` aprobados
- Inventarios generados y revisados (`docs/audit/*`)
- Backup del repo (tag y branch)
- CI pipeline actualizado para builds reproducibles

Fase A — Preparación (manual)
1. Revisar inventarios `docs/audit/*` y marcar archivos a limpiar.
2. Crear branch `cleanup/prepare` y commit con solo `docs/` nuevos.
3. Publicar PR con la lista de archivos propuestos para mover/archivar.

Fase B — Ejecución (ordenada)
1. Añadir a `.gitignore` las reglas definidas en `docs/CLEANUP_RULES.md`.
2. Ejecutar `git rm --cached` solo en artefactos que no deben estar versionados (pre-aprobado).
3. Commit por cada tipo de limpieza (node_modules, dist, docs archive) con mensajes claros.
4. Ejecutar CI y esperar build green.

Fase C — Validación
1. Levantar stack en entorno de staging: `docker-compose up -d`.
2. Validar checklist (ver abajo).
3. Mantener PR en revisión 48h y recolectar feedback.

Checklist de validación

- [ ] `docker-compose up` arranca sin errores
- [ ] `/operator` UI carga en dev (si procede)
- [ ] Operator backend `/health` responde (8011)
- [ ] Chat fallback funciona (modo local)
- [ ] Tests relevantes pasan (pytest frontend build e2e)

Rollback

- Si falla, revertir PR y restaurar branch de backup.

---
Fecha: 2025-12-14
