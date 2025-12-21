# VX11 Canonical Audit — Generated 2025-12-15

Resumen ejecutivo:
- Runtime DB tocada: NO (solo lectura)
- Archivos generados:
  - `data/backups/vx11_CANONICAL_DISTILLED.db` (estructura resumen)
  - `data/backups/vx11_CANONICAL_STATE.json` (mapa y métricas)

Extracción:
- Tablas encontradas: 85
- Tablas vacías detectadas: 45
- Nivel de autonomía heurístico: low

Puntos clave:
- Muchas tablas `*_logs`, `*_history`, `*_events` clasificadas como HISTÓRICAS.
- Tablas con actividad operativa: `tasks`, `daughter_tasks`, `task_queue`, `operator_jobs`.
- IA/Autonomía: `ia_decisions` existe pero con bajo volumen (autonomy_level=low).

Decisiones y limpieza aplicadas:
- Se generó una BD destilada con resumen por tabla, muestras y métricas agregadas.
- Se generó JSON maestro con clasificación, relaciones implícitas, flujos y top-errors.
- No se modificó la BD runtime ni se reiniciaron servicios.

Recomendaciones futuras (documentadas, no ejecutadas):
- Revisar tablas vacías para depuración/archivado.
- Evaluar aumento de recolección en `ia_decisions` si se desea autonomía mayor.
- Plan de remediación para `sitecustomize.py` y builds (autorización requerida).

Limitaciones y fiabilidad:
- Extracción basada en conteos y muestras (limitadas a 5 por tabla).
- Algunas inferencias (roles, flujos) son heurísticas y requieren validación humana.
- Tamaño resultante muy pequeño (< 1MB), por diseño; proporciona referencia eficiente.

Archivos generados:
- `data/backups/vx11_CANONICAL_DISTILLED.db` — 86016
- `data/backups/vx11_CANONICAL_STATE.json` — 110102

Fin del informe.


CI Integration:
- El workflow `.github/workflows/ci.yml` ahora incluye un job `vx11_scan_and_map` que ejecuta `scripts/generate_canonical_v2.py` en modo solo-lectura, valida los artefactos, genera `docs/audit/VX11_CANONICAL_AUDIT.md` y sube los artefactos como artifact de CI.
- El job respeta límites de tamaño (<500MB) y realiza backups `.bak_<timestamp>` antes de reemplazar los canónicos.
