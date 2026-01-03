#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# Start Services - Canonical Compose-Based Startup
#
# Purpose: Start specified services using full-test profile
# Usage: bash scripts/start_services.sh [service1] [service2] ...
#        bash scripts/start_services.sh  (default: tentaculo_link hermes operator-backend operator-frontend)
#
# Default services preserve madre running; start others on-demand
###############################################################################

TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="docs/audit/$TS"
mkdir -p "$OUT"

# Default services to start (omit madre; it should be already running)
# These are the services that make sense to bring up after core
SERVICES=("tentaculo_link" "hermes" "operator-backend" "operator-frontend" "switch")
if [ "$#" -gt 0 ]; then
  SERVICES=("$@")
fi

COMPOSE_FILE="docker-compose.full-test.yml"

{
    echo "=== Starting Services ==="
    echo "Timestamp: $TS"
    echo "Compose: $COMPOSE_FILE"
    echo "Services: ${SERVICES[*]}"
    echo ""
    
    echo "Starting: ${SERVICES[*]}"
    docker compose -f "$COMPOSE_FILE" up -d --build "${SERVICES[@]}" || true
    
    echo ""
    echo "Service state:"
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo "Services started (or attempted). See $OUT for logs."
} | tee "$OUT/start_services.log"

echo "$OUT"

