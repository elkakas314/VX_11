# VX11 Production Hardening Report

Timestamp (UTC): 2025-12-30T03:31:33Z

## Module Map
- `tentaculo_link/` — single entrypoint gateway + operator API proxy.
- `madre/` — policy/window control + orchestration.
- `switch/` — routing/LLM switch + `switch/hermes/` catalog.
- `spawner/` — child process orchestration.
- `operator/` — frontend + backend (under `operator/backend/`).
- `hormiguero/`, `manifestator/`, `mcp/`, `shubniggurath/` — optional services (windowed).

## Compose Published Ports (Production)
See `compose_ports.txt`.
- `docker-compose.production.yml`: tentaculo_link publishes `8000:8000` only.

## OpenAPI Discovery
- No static OpenAPI JSON/YAML found in repo (see `openapi_files.txt`).
- Route decorators enumerated instead.

## Endpoints (Detected)
- `tentaculo_link` routes: see `tentaculo_link_paths.txt` (76 paths).
- `madre` routes: see `madre_paths.txt` (72 paths).

## P0/P1 Blockers (with file+line)
### P0 — Secrets tracked in repo
- `.env` line 3: `DEEPSEEK_API_KEY` present (tracked). Evidence: `secret_line_numbers.txt`.
- `.env.deepseek` line 1: `DEEPSEEK_API_KEY` present (tracked). Evidence: `secret_line_numbers.txt`.
Status: **REMOVED FROM GIT + ROTATION REQUIRED** (see `docs/audit/ROTATION.md`).

### P1 — Import-time dependency on hormiguero (tentaculo_link)
- `tentaculo_link/routes/rails.py` lines 27/63/72/82: lazy import guard + OFF_BY_POLICY/DEPENDENCY_UNAVAILABLE responses. Evidence: `rails_dependency_guard_locations.txt`.
Status: **FIXED** (tentaculo_link can boot without hormiguero package).

## Notes
- Operator frontend now defaults to relative API paths; operator backend hardens upstream error handling.
- Single-entrypoint gate updated in `docs/audit/CORE_GATES_PACK.md`.
