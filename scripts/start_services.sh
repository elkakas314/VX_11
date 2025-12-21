#!/usr/bin/env bash
set -euo pipefail

TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="docs/audit/$TS"
mkdir -p "$OUT"

# default services to start (omit madre intentionally, Madre should stay on)
SERVICES=("tentaculo_link" "hermes" "hormiguero" "mcp" "shubniggurath" "spawner" "operator-backend" "operator-frontend")
if [ "$#" -gt 0 ]; then
  SERVICES=("$@")
fi

echo "TS=$TS" > "$OUT/start_services.log"
echo "Starting services: ${SERVICES[*]}" >> "$OUT/start_services.log"

docker compose -f docker-compose.yml -f docker-compose.override.yml up -d "${SERVICES[@]}" >> "$OUT/start_services.log" 2>&1 || true
docker compose -f docker-compose.yml -f docker-compose.override.yml ps > "$OUT/docker_compose_ps_after_start.txt" 2>&1 || true

echo "Started (or attempted). See $OUT for logs." >> "$OUT/start_services.log"
echo "$OUT"
