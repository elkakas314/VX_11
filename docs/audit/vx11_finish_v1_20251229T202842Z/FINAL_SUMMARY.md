# VX11 Finish v1 — Final Summary

## What changed
- Canonical API routing now lives at `/operator/api/v1/*`, with `/operator/api/*` mapped to v1 in `tentaculo_link`.
- Operator backend now exposes `/api/v1/*` plus legacy `/api/*`, with correlation IDs normalized in headers and JSON payloads.
- Added v1-required endpoints (status, health, env, topology, windows, chat, SSE, logs tail, audit, madre intents, manifestator, hormiguero, shub stubs, explorer).
- Frontend migrated to `/operator/api/v1/*` with configurable base URL and robust SSE reconnect banner.

## How to run
- Operator frontend base URL (default):
  - Dev: `http://localhost:8000`
  - Prod: `window.location.origin`
- Override base URL: `VITE_VX11_API_BASE=<base_url>`

## Operator window
- Default runtime is SOLO_MADRE. When operator is closed, API returns `OFF_BY_POLICY` (403 JSON) rather than 502.
- Ask Madre to open a window using `/operator/api/v1/chat/window/open` via the Operator UI.

## Evidence
- Raw command logs and outputs: `docs/audit/vx11_finish_v1_20251229T202842Z/raw/`
- Endpoint list: `docs/audit/vx11_finish_v1_20251229T202842Z/ENDPOINTS.md`

## Limitations observed in this environment
- Local services (tentaculo_link/madre/etc.) were not running, so curls and most pytest cases failed with connection errors.
