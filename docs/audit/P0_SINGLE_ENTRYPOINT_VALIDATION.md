# P0 Single-Entrypoint Validation Pack

**Goal**: Validate production single-entrypoint (only `tentaculo_link` publishes 8000) without running Docker here.

## Runbook (Copilot local)

```bash
set -euo pipefail
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="docs/audit/${TS}_p0_single_entrypoint_fix"
mkdir -p "$OUT"

# sync ff-only
git checkout main
git fetch --all --prune
git pull --ff-only

docker compose -f docker-compose.production.yml up -d --build

docker compose -f docker-compose.production.yml ps | tee "$OUT/prod_ps.txt"

docker ps --format 'table {{.Names}}\t{{.Ports}}' | tee "$OUT/prod_ports_table.txt"

curl -i http://127.0.0.1:8000/health | tee "$OUT/health_8000.txt"

# DB checks sqlite PRAGMAs
sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" \
  "PRAGMA quick_check;" \
  | tee "$OUT/sqlite_quick.txt"

sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" \
  "PRAGMA integrity_check;" \
  | tee "$OUT/sqlite_integrity.txt"

sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON;" \
  "PRAGMA foreign_key_check;" \
  | tee "$OUT/sqlite_fk.txt"
```

## Notes
- All evidence must be saved under `docs/audit/<UTC_TS>_p0_single_entrypoint_fix/`.
- Do not publish any ports other than `8000:8000` on `vx11-tentaculo-link`.
- If any additional port is published, SINGLE-ENTRYPOINT = FAIL.
