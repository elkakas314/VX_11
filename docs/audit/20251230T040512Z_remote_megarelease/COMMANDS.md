# VX11 Validation Commands (20251230T040512Z)

> Copy/paste friendly. Produces evidence under docs/audit/<ts>.

```bash
set -euo pipefail
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="docs/audit/${TS}_core_validation"
mkdir -p "$OUT"

# Single entrypoint (production compose)
docker compose -f docker-compose.production.yml up -d --build

docker compose -f docker-compose.production.yml ps | tee "$OUT/prod_ps.txt"
docker ps --format 'table {{.Names}}\t{{.Ports}}' | tee "$OUT/prod_ports_table.txt"

# Gate: only tentaculo_link publishes ports
EXTRA_PORTS=$(docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E '\->' | grep -v 'vx11-tentaculo-link.*8000' | wc -l)
if [[ $EXTRA_PORTS -gt 0 ]]; then
  echo "FAIL: Found $EXTRA_PORTS containers with published ports outside vx11-tentaculo-link:8000" | tee "$OUT/single_entrypoint_check.txt"
  docker ps --format '{{.Names}}\t{{.Ports}}' | grep -E '\->' | grep -v 'vx11-tentaculo-link.*8000' | tee -a "$OUT/single_entrypoint_check.txt"
  exit 1
else
  echo "PASS: Only vx11-tentaculo-link publishes ports (8000)" | tee "$OUT/single_entrypoint_check.txt"
fi

# Health via entrypoint
curl -sS -i http://127.0.0.1:8000/health | tee "$OUT/health_8000.txt"

# Auth gate (no token)
curl -sS -i http://127.0.0.1:8000/operator/api/status | tee "$OUT/operator_status_no_token.txt"

# Auth gate (token)
export VX11_TOKEN="${VX11_TOKEN:-<set-real-token>}"
curl -sS -i -H "X-VX11-Token: $VX11_TOKEN" http://127.0.0.1:8000/operator/api/status | tee "$OUT/operator_status_with_token.txt"

# Solo madre policy
curl -sS http://127.0.0.1:8000/operator/power/policy/solo_madre/status | tee "$OUT/solo_madre_status.txt"

# DB integrity checks
sqlite3 data/runtime/vx11.db "PRAGMA quick_check;" | tee "$OUT/sqlite_quick.txt"
sqlite3 data/runtime/vx11.db "PRAGMA integrity_check;" | tee "$OUT/sqlite_integrity.txt"
sqlite3 data/runtime/vx11.db "PRAGMA foreign_key_check;" | tee "$OUT/sqlite_fk.txt"

# Operator frontend build (if applicable)
cd operator/frontend
npm install
npm run build | tee "../../$OUT/operator_frontend_build.txt"
cd -
```
