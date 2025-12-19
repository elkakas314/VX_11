# VX11 Context (canónico)

Repo: `/home/elkakas314/vx11`

## Servicios (docker-compose.yml)

Puertos y endpoints mínimos (Plug-&-Play):

- `tentaculo_link` (8000): `GET /health`
- `madre` (8001): `GET /health`
  - Mantenimiento DB: `POST /madre/power/db_retention` (`{"apply": false|true}`)
- `switch` (8002): `GET /health`
- `hermes` (8003): `GET /health`
- `hormiguero` (8004): `GET /health`
- `manifestator` (8005, profile disabled): `GET /health`
- `mcp` (8006): `GET /health`
- `shubniggurath` (8007): `GET /health`
- `spawner` (8008): `GET /health`, `POST /spawn`
- `operator-backend` (8011): `GET /health`
- `operator-frontend` (8020): `GET /` (healthcheck del compose)

## Estado de módulos (última verificación)

Reporte canónico más reciente:
- `docs/audit/codex_agent_canonical_verify_20251218T235453Z/FINAL_AGENT_AND_MODULE_CERTIFICATION_REPORT.md`

Estado runtime (tabla `module_status` en `data/runtime/vx11.db`):
- `docs/audit/codex_canonical_closure_20251218T223452Z/db/11_module_status_rows.txt`

## Docker (uso recomendado)

Este repo usa `docker-compose.yml` bloqueado. Para hacerlo PnP sin tocarlo:

- Override: `docker-compose.override.yml` (añade `build:` a servicios image-only).
- Preferir Compose v2:
  - `docker compose -f docker-compose.yml -f docker-compose.override.yml config`
  - `docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build`
  - `docker compose -f docker-compose.yml -f docker-compose.override.yml ps`

## DB (SQLite unificada)

- Ruta runtime canónica: `data/runtime/vx11.db`
- Checks:
  - `sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" "PRAGMA quick_check;"`
  - `sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" "PRAGMA integrity_check;"`
  - `sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" "PRAGMA foreign_keys=ON; PRAGMA foreign_key_check;"`
- Regenerar DB_MAP/DB_SCHEMA (canónico):
  - `PYTHONPATH=. python3 -m scripts.generate_db_map_from_db data/runtime/vx11.db`
  - Salidas: `docs/audit/DB_MAP_v7_FINAL.md`, `docs/audit/DB_SCHEMA_v7_FINAL.json`, `docs/audit/DB_MAP_v7_META.txt`

## Flujo (alto nivel)

- Operator → `operator-backend` (8011) / `operator-frontend` (8020)
- Operator → `tentaculo_link` (8000) como frontdoor (alias `gateway` por compatibilidad)
- `tentaculo_link` enruta a:
  - `madre` (8001): orquestación, PnP, mantenimiento DB (retención)
  - `switch` (8002): routing/adaptive engine selection
  - `hermes` (8003): CLI/bridge de herramientas
  - `hormiguero` (8004): paralelización/ants
  - `mcp` (8006): capa conversacional
  - `shubniggurath` (8007): pipeline IA
  - `spawner` (8008): ejecución efímera / spawn

## Retención (política por defecto)

Objetivo: frenar crecimiento sin scripts nuevos, vía Madre power endpoint.

- `incidents.detected_at`: 90 días
- `pheromone_log.created_at`: 14 días
- `routing_events.timestamp`: 30 días
- `cli_usage_stats.timestamp`: 30 días
- `system_events.timestamp`: 30 días
- `scheduler_history.timestamp`: 30 días
- `intents_log.created_at`: 30 días
- `ia_decisions.created_at`: 30 días
- `model_usage_stats.created_at`: 90 días

Índices recomendados (para deletes por fecha):

- `incidents(detected_at)`
- `pheromone_log(created_at)`
- `routing_events(timestamp)`
- `cli_usage_stats(timestamp)`
- `system_events(timestamp)`
- `scheduler_history(timestamp)`
- `intents_log(created_at)`
- `ia_decisions(created_at)`
- `model_usage_stats(created_at)`

Configuración (sin romper compatibilidad):

- Perfil:
  - `VX11_RETENTION_PROFILE=low_power` (o `ULTRA_LOW_MEMORY=true`) → logs por defecto 7 días.
- Defaults:
  - `VX11_RETENTION_LOG_DAYS` (default 30)
  - `VX11_RETENTION_LOG_DAYS_LOW_POWER` (default 7)
- Override por tabla (tiene prioridad): `VX11_RETENTION_<TABLE>_DAYS` (ej: `VX11_RETENTION_PHEROMONE_LOG_DAYS=14`).

## Backups / reversión (DB)

- Regla: no tocar `data/runtime/vx11.db` sin copia previa.
- Backup canónico SQLite: `sqlite3 data/runtime/vx11.db ".backup '.../vx11.db.backup'"`
- Validación post-cambio: `PRAGMA quick_check; integrity_check; foreign_key_check;` (+ `wal_checkpoint(TRUNCATE)` si WAL).

## Reglas de repo (operativas)

- Prohibido tocar/mover: `docker-compose.yml`, `sitecustomize.py`, `tokens.env*`, `.vscode/`, `.devcontainer/`, `*.code-workspace`.
- Prohibido nesting tipo `.github/.github`, `.vscode/.vscode`, `docs/audit/docs/audit` (si aparece: aplanar sin sobreescribir y registrar evidencia).
- Evidencia: todo output relevante siempre en `docs/audit/<TS>/`.
