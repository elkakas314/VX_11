# INVENTARIO: Documentación en raíz — Drift Map

Comando ejecutado:
```
ls -1 /home/elkakas314/vx11/*.md
```

Resultados (2025-12-14): lista de archivos `.md` en la raíz

(Ver `ls` output en auditoría técnica)

Clasificación propuesta (borrador)

Canónico (referenciar desde `docs/`):
- `README.md` — puerta de entrada canónica
- `PRODUCTION_READY.md` — checklist deploy
- `VX11_v7_DEPLOYMENT_READY.md` — deployment notes

Legacy / Audit (mover a `docs/audit/`):
- `AUDITORIA_*` (varios)
- `OPERATOR_REPARACION_FINAL*` y `OPERATOR_COMPLETION_REPORT.md`
- `REPORTE_*`, `REMEDIATION_COMPLETION_v7.md`

Snapshots / Reports (archivar):
- `SNAPSHOT_POST_AUDITORIA_v7.md`
- `VX11_v7_1_COMPLETION_REPORT.md`

Basura / Duplicado (candidatos para `docs/archive/garbage/` tras revisión humana):
- múltiples `*_FINAL_*` o `*_COMPLETION_*` que parecen duplicar contenido

Recomendación inmediata:
- Mover todas las `AUDITORIA_*` y `*_COMPLETION_*` a `docs/archive/` o `docs/audit/` tras revisión manual.
- Mantener un índice actualizado en `docs/INDEX.md` que apunte a canónicos.

---
Fecha: 2025-12-14
