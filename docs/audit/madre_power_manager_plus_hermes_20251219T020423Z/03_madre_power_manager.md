# 03_MADRE_POWER_MANAGER

Changes applied:
- Added `madre/power_manager.py` with allowlisted plan/apply power actions and triple lock (key + token TTL + confirm string).
- Registered new endpoints in `madre/main.py` without breaking legacy `/madre/power/db_retention`.
- Removed `shell=True` usage in `madre/main.py` power status snapshot.

New endpoints:
- `GET /madre/power/services`
- `GET /madre/power/token`
- `POST /madre/power/service/{name}/start`
- `POST /madre/power/service/{name}/stop`
- `POST /madre/power/service/{name}/restart`
- `POST /madre/power/mode/idle_min`
- `POST /madre/power/mode/hard_off`

Guards:
- Plan-only by default (`apply=false`).
- Apply true requires `X-VX11-POWER-KEY`, `X-VX11-POWER-TOKEN` (TTL 60s), and confirm string.
- Rate limit: 6/min/IP, hard_off stricter (1 per 5 min).
- Docker perms missing -> plan-only with evidence in `plan_only_reason.txt`.

Evidence:
- Each request writes plan/result under `docs/audit/madre_power_*` (per action).
- Apply true adds pre/post snapshots (`ss`, `ps`, `free`).
