# Core Gates Report — 2025-12-30T02:10:28Z

Resumen de ejecución (evidencia en este directorio):

- `docker_compose_up.txt` — salida de `docker compose --profile core up -d --build`
- `docker_compose_ps.txt` — servicios levantados
- `tentaculo_logs.txt` — logs recientes de `tentaculo_link`
- `tentaculo_health.json` — `/health` (200)
- `operator_status.json` — `/operator/api/v1/status` (respuesta: auth_required)
- `sqlite_quick_check.txt`, `sqlite_integrity_check.txt`, `sqlite_foreign_key_check.txt` — PRAGMA checks (ok)

Resultados resumidos:

- Tentáculo (`/health`): PASS (200 OK) — ver `tentaculo_health.json`.
- Operator status via tentáculo: AUTH_REQUIRED (403/401 pattern) — secure by policy (see `operator_status.json`).
- PRAGMA quick_check / integrity_check: PASS — ver `sqlite_quick_check.txt` and `sqlite_integrity_check.txt`.
- Solo_madre apply: intento realizado (si madre expuso endpoint). Si el endpoint no respondió, revisar `docker_compose_ps.txt` y `tentaculo_logs.txt`.

Gates:
- Single-entrypoint: FAIL (multiple services expose ports: see `docker_compose_ps.txt` — ports 8000,8001,8002,8003,8004,8006,8008,6379). Recommendation: apply `docker-compose.prod.yml` overlay to limit published ports to 8000.
- OFF_BY_POLICY behavior: tentaculo returns `OFF_BY_POLICY` messages when appropriate (code paths present). Further work: ensure consistent 403 JSON when blocked upstream.
- Correlation ID: tentaculo sets and echoes `X-Correlation-Id` (middleware present) — PASS evidence in code and logs.

Next actions taken:
1. Evidence saved in this dir.
2. Recommend P0 fixes: (A) enforce single-entrypoint in compose, (B) ensure frontend uses `VITE_VX11_API_BASE`, (C) standardize OFF_BY_POLICY 403 JSON.
