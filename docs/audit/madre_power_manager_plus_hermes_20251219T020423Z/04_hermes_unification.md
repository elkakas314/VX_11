# 04_HERMES_UNIFICATION

Canonical Hermes:
- Service points to `switch/hermes` (compose + Dockerfile).
- Added shim module `hermes/` re-exporting `switch.hermes.main:app` to satisfy canonical folder presence.

Discovery pipeline (3-tier) update:
- Tier 1: local filesystem scan (`models/`), updates `models_local`.
- Tier 2: local catalog (`switch/hermes/models_catalog.json`), updates `model_registry`.
- Tier 3: web disabled by default; only activated with `allow_web=true`.

Endpoints:
- Added `GET /hermes/status` (intendencia state, no routing).
- Updated `POST /hermes/discover` to plan/apply with audit output.

Non-routing guarantee:
- Hermes endpoints expose inventory/discovery; routing decisions remain in Switch.
