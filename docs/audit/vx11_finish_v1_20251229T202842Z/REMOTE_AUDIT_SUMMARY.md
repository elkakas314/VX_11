# VX11 Remote Audit Summary (pre-change)

Timestamp (UTC): 2025-12-29T20:28:42Z

## Git
- `git remote -v`: no remotes listed in output.
- `git branch -vv`: on branch `work` at `7b9db52`.
- `git status -sb`: clean working tree.
- `git log --oneline -20`: recorded in `raw/git_log.txt`.

## Operator layout
- Operator-related directories detected:
  - `./operator`
  - `./operator_backend`
  - `./operator_ui`
  - `./docs/archive/operator`
  - `./attic/tools/operator`

## tentaculo_link routes
- `/operator/api` routes exist in `tentaculo_link/main_v7.py` with multiple endpoints and a fallback handler.
- Correlation references appear in `tentaculo_link/main_v7.py` and related routes/DB helpers.

## operator backend routes
- Operator backend defines routes under `/operator/api/*` in `operator/backend/main.py`.
- Operator frontend uses `/operator/api/*` paths and `EventSource('/operator/api/events/stream')`.

## Local OpenAPI
- `curl -sf http://localhost:8000/openapi.json | head -c 2000`: no output (service not running or unavailable).

## Evidence
- Command outputs saved in `docs/audit/vx11_finish_v1_20251229T202842Z/raw/`.
