# PHASE 0 — Repo Snapshot & Map

## Snapshot
- Evidence:
  - `git status -sb`: `git_status_sb.txt`
  - `git log -10 --oneline --decorate`: `git_log_10.txt`

## Notes
- HEAD branch reported as `work` (requested `main` in prompt).

## Compose map (services, ports, profiles)
- Evidence:
  - `compose_files.txt`

### Observed entrypoints
- `docker-compose.yml` publishes `8000:8000` for `tentaculo_link`.
- `docker-compose.production.yml` publishes only `8000:8000` for `tentaculo_link`; all other services are internal-only.
- `docker-compose.prod.yml` removes host port mappings for non-gateway services.

### Profiles (observed)
- `core`: switch, hermes, hormiguero, mcp, spawner
- `audio`: shubniggurath
- `operator`: operator-backend
- `maintenance`/`disabled`: manifestator

## Evidence index (Phase 0)
- `git_status_sb.txt`
- `git_log_10.txt`
- `compose_files.txt`
