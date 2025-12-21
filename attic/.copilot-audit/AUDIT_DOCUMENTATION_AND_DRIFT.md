# AUDIT: DOCUMENTACIÓN Y DRIFT

Objetivo: clasificar la documentación existente en canónica / legacy / basura, y proponer estructura documental definitiva.

1) Estado actual (resumen)

- Existe abundante documentación en la raíz (`README.md`, `RESUMEN_*`, `AUDITORIA_*`, `OPERATOR_*`, `VX11_v7_*`, etc.).
- También hay una carpeta `docs/` con arquitectura y guías técnicas.
- Resultado: ruido informativo; difícil saber cuál es la versión canónica.

2) Clasificación propuesta (ejemplos)

- Canónico (mover o referenciar desde `docs/`):
  - `README.md` (actualizar si necesario)
  - `docs/ARCHITECTURE.md`
  - `docs/API_REFERENCE.md`
  - `docs/DEVELOPMENT.md`

- Legacy (archivar en `docs/archive/`):
  - `AUDITORIA_*` (antiguos) — si ya están presentes versiones más recientes en `docs/audit/`.
  - `OPERATOR_REPARACION_FINAL_*` y `REPORTE_*` si son snapshots históricos.

- Basura / duplicado (recomendado mover a `docs/archive/garbage/` o eliminar tras verificación humana):
  - Archivos con nombres similares `*_FINAL_*` duplicados.
  - `build/` artefactos que no son necesarios para desarrollo.

3) Qué falta

- `docs/REPO_LAYOUT.md` — mapa canónico del repo indicando dónde vivir: backend, frontend, scripts, docs.
- `docs/CLEANUP.md` — pasos para limpieza (manual) de node_modules y dist, y cómo actualizar `.gitignore`.
- `docs/CHANGELOG.md` — unificiar cambios en lugar de dispersarlos por `*COMPLETION*`.

4) Recomendaciones inmediatas (no destructivas)

- Crear `docs/audit/` y mover allí todas las auditorías nuevas y antiguas; dejar un índice en `docs/` que apunte a la versión más reciente.
- Mantener `README.md` como única puerta de entrada; referenciar `docs/` para detalle.
- Definir política: "Solo `docs/*.md` es canónico; md en raíz deben archivarse o eliminarse".
- Añadir script `scripts/collect-docs.sh` para validar y listar documentos canónicos vs legacy.

5) Proceso propuesto para limpieza

1. Inventario: `git ls-files | grep -E 'AUDITORIA|REPORTE|COMPLETION'`.
2. Revisión humana: marcar versiones válidas.
3. Mover/archivar legacy en `docs/archive/`.
4. Actualizar `README.md` y `docs/REPO_LAYOUT.md`.

---
Fecha: 2025-12-14
