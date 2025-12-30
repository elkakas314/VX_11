# PHASE 2 — Operator (Frontend + Backend wiring)

## Scope discovery
- Operator frontend: `operator/frontend`
- Operator backend: `operator/backend` (optional profile)
- Tentáculo routing: `tentaculo_link/main_v7.py` + `tentaculo_link/routes/*`

## Routes adjusted/added (tentaculo_link)
- `GET /operator/api/events?follow=true` emits `snapshot` SSE (events + power window state).
- `GET /operator/api/audit/runs` returns audit run list from `docs/audit` (fallback when DB not present).
- `GET /operator/api/audit/{run_id}` returns file listing.
- `GET /operator/api/audit/{run_id}/download` zips audit outdir.
- `GET /operator/api/hormiguero/status` + `POST /operator/api/hormiguero/scan/once` (dependency-safe).
- `GET /operator/api/switch/provider` (read-only provider context + explainability).
- `GET /operator/api/window/status` used for power window status.

## Frontend wiring
- UI now consumes `/operator/api/*` endpoints (no direct module calls).
- Hormiguero view includes status + “scan once”.
- Overview includes core services + dormant profiles + switch provider + recent audit runs.
- Audit view lists `docs/audit` outdirs with detail + download.

## Files touched
- `config/settings.py`
- `tentaculo_link/main_v7.py`
- `tentaculo_link/routes/__init__.py`
- `tentaculo_link/routes/audit.py`
- `tentaculo_link/routes/hormiguero.py`
- `tentaculo_link/routes/switch.py`
- `operator/frontend/src/App.tsx`
- `operator/frontend/src/App.css`
- `operator/frontend/src/services/api.ts`
- `operator/frontend/src/views/OverviewView.tsx`
- `operator/frontend/src/views/AuditView.tsx`
- `operator/frontend/src/views/HormigueroView.tsx`
- `operator/frontend/src/views/ChatView.tsx`
- `operator/frontend/src/views/CoDevView.tsx`
- `operator/frontend/src/components/OverviewPanel.tsx`
- `operator/frontend/src/components/MetricsPanel.tsx`
- `operator/frontend/src/components/RailsPanel.tsx`
- `operator/frontend/src/components/EventsPanel.tsx`
- `operator/frontend/src/components/P0ChecksPanel.tsx`

## How to run (typical)
- Backend gateway: `docker compose -f docker-compose.production.yml up -d --build`
- Frontend build (served by tentaculo_link):
  - `cd operator/frontend`
  - `npm install`
  - `npm run build`

## Notes
- `/operator/api/*` proxy to operator-backend is now gated by `VX11_OPERATOR_API_PROXY_ENABLED` (default off).
- `/operator/api/v1/*` requests are rewritten to `/operator/api/*` when proxy is disabled.
- Operator backend remains optional and does not break single-entrypoint invariant.
