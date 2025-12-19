#!/usr/bin/env bash
set -euo pipefail

TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="docs/audit/$TS"
mkdir -p "$OUT"

echo "TS=$TS" > "$OUT/stop_non_madre.log"
echo "Stopping services except madre" >> "$OUT/stop_non_madre.log"

ALL=$(docker compose -f docker-compose.yml -f docker-compose.override.yml ps --services 2>/dev/null || true)
for s in $ALL; do
  if [ "$s" != "madre" ]; then
    echo "Stopping $s" >> "$OUT/stop_non_madre.log"
    docker compose -f docker-compose.yml -f docker-compose.override.yml stop "$s" >> "$OUT/stop_non_madre.log" 2>&1 || true
  fi
done

docker compose -f docker-compose.yml -f docker-compose.override.yml ps > "$OUT/docker_compose_ps_after_stop.txt" 2>&1 || true
echo "Stop phase done" >> "$OUT/stop_non_madre.log"
echo "$OUT"
