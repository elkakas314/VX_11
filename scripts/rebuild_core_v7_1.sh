#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh"
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[rebuild] Building switch, operator-backend, operator-frontend (no cache)..."
docker-compose build --no-cache switch operator-backend operator-frontend

echo "[rebuild] Starting core services..."
docker-compose up -d switch hermes hormiguero operator-backend operator-frontend

echo "[rebuild] Current container state:"
docker-compose ps

TOKEN_HEADER=("X-VX11-Token: vx11-local-token")

check_health() {
  local url="$1"
  echo "[rebuild] Checking $url"
  http_status=$(curl -s -o /tmp/health.out -w "%{http_code}" -H "${TOKEN_HEADER[@]}" "$url" || true)
  if [[ "$http_status" != "200" ]]; then
    echo "Healthcheck failed for $url (status $http_status)"
    cat /tmp/health.out || true
    exit 1
  fi
}

check_health "http://127.0.0.1:8000/health"
check_health "http://127.0.0.1:8002/health"
check_health "http://127.0.0.1:8011/ui/status"

echo "[rebuild] All healthchecks passed."
