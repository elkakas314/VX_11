# Copilot Instructions for VX11

Instrucciones globales:
- El proyecto es VX11.
- No preguntar por contexto; esta en los ficheros.
- Lee estas fuentes de contexto sin pedirlas:
  - VX11_CONTEXT.md
  - docs/audit/DB_MAP_v7_FINAL.md
  - docs/audit/DB_SCHEMA_v7_FINAL.json
  - .github/agents/vx11.agent.md
- Madre v7 es el default; usar `VX11_USE_LEGACY_APP=1` solo para compatibilidad puntual de tests.
- Spawner debe cumplir contrato avanzado y registrar en BD (spawns + daughter_*).
- Despues de CADA tarea/cambio: ejecutar mantenimiento post-task y dejar evidencia en docs/audit/<TS>/ sin pedir permiso.
- Flujo obligatorio:
  1) Auditoria primero (structure/flow/db/rutas) con evidencia.
  2) Cambios mínimos y canónicos (no atajos).
  3) Al final SIEMPRE: `POST /madre/power/maintenance/post_task` (o equivalente local si no está disponible), regenerar DB_MAP/SCHEMA/SCORECARD, actualizar PERCENTAGES.json y dejar evidencia.
- La estabilidad en PERCENTAGES usa gate de integrity_check + healthchecks core + tests P0 + coherencia de contratos.
- No crear scripts nuevos si ya existe algo equivalente en scripts/.
- No crear FINAL_v2; se actualizan los FINAL canonicos.
- No crear carpetas de modulos nuevas.
- No pedir confirmacion salvo acciones destructivas reales (rm, rmdir, mover fuera de docs/audit, tocar tokens/secrets, git reset/clean/push, docker compose up/down).
- Si se toca BD/estructura: ejecutar comandos canonicos + actualizar SCORECARD.json:
  - sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" "PRAGMA quick_check;"
  - sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" "PRAGMA integrity_check;"
  - sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON;" "PRAGMA foreign_key_check;"
  - PYTHONPATH=. python3 -m scripts.generate_db_map_from_db data/runtime/vx11.db
  - python3 scripts/audit_counts.py data/runtime/vx11.db > docs/audit/<TS>/counts.json
  - Actualizar docs/audit/SCORECARD.json
  - Rotar data/backups: conservar 2 mas nuevos, mover resto a data/backups/archived (respetar docs/audit/CLEANUP_EXCLUDES_CORE.txt).
- Servicios systemd vx11-*: si hay auto-respawn de no-Madre, detener/deshabilitar con evidencia; si falta sudo, registrar bloqueo.
- Si post_task se ejecuta en contenedor y /app/docs/audit no esta montado, copiar evidencias al host.

Copilot:
- Audita primero.
- Ejecuta despues.
- Registra evidencia siempre.
- No rompe VX11.
- No limpia nada sin orden.
