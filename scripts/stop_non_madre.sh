#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# Stop Non-Madre Services (KEEP tentaculo_link + redis-test)
#
# Policy: solo_madre mode preserves single entrypoint + redis
# - Stop: hermes, operator-backend, operator-frontend, switch, spawner, etc.
# - Keep: madre, tentaculo_link, redis-test
#
# Exit: 0 if all services stopped cleanly
###############################################################################

TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="docs/audit/$TS"
mkdir -p "$OUT"

{
    echo "=== Stopping Non-Madre Services ==="
    echo "Timestamp: $TS"
    echo "Policy: Keep madre + tentaculo_link + redis-test (single entrypoint)"
    echo ""
    
    # Use canonical compose file (full-test is the reference)
    COMPOSE_FILE="docker-compose.full-test.yml"
    
    ALL=$(docker compose -f "$COMPOSE_FILE" ps --services 2>/dev/null || true)
    echo "All services: $ALL"
    echo ""
    
    for s in $ALL; do
        if [ "$s" != "madre" ] && [ "$s" != "tentaculo_link" ] && [ "$s" != "redis-test" ]; then
            echo "Stopping: $s"
            docker compose -f "$COMPOSE_FILE" stop "$s" 2>&1 || true
        else
            echo "Keeping: $s"
        fi
    done
    
    echo ""
    echo "Final state:"
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "Stop phase complete"
    
} | tee "$OUT/stop_non_madre.log"

# Snapshot of final state
docker compose -f "$COMPOSE_FILE" ps > "$OUT/docker_compose_ps_after_stop.txt" 2>&1 || true

echo "$OUT"
