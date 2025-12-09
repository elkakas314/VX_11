# USO RÁPIDO VX11 v6.6

## Preparación (una vez)
- Secretos por variables de entorno (tokens); `tokens.env` es legacy solo para dev local.
- Base de datos: `data/runtime/vx11.db` (no tocar manualmente).
- Anti-caos disponible: `bash scripts/run_anti_chaos_once.sh`.

## Arranque / parada
- Arrancar: `bash scripts/start_vx11_v6_6.sh`
- Parar: `bash scripts/stop_vx11_v6_6.sh`
- Health endpoints útiles:
  - Madre: http://127.0.0.1:8001/health
  - Hormiguero: http://127.0.0.1:8004/health
  - MCP: http://127.0.0.1:8006/health
  - Spawner: http://127.0.0.1:8008/health
  - Shubniggurath: http://127.0.0.1:8007/health (si expuesto)
  - Operator backend: http://127.0.0.1:8011/health

## Verificación rápida (tests)
- `bash scripts/test_vx11_v6_6.sh`
  - Ejecuta auditoría de orden, smoke Operator↔Switch/Hermes y pytest completo.

## Anti-caos / limpieza
- Auditoría de drift: `python3 scripts/auditor_orden_vx11.py`
- Ciclo anti-caos manual: `bash scripts/run_anti_chaos_once.sh`
- Patch ops de drift raíz: `python3 scripts/apply_patch_ops_vx11_v6_6.py`
  - Mueve `logs/`, `sandbox/`, `shub_sandbox/`, `forensic/` a `build/artifacts/*` con backup en `build/artifacts/backups/fs_v6_6/`.
  - No toca `data/runtime` ni modelos.
  - Revisa el JSON de salida tras ejecutar.

## Nota sobre Operator
- Smoke test: `tests/test_operator_switch_hermes_flow.py`.
- Operator se conecta a Switch/Hermes respetando `X-VX11-Token` a lo largo de la cadena.
