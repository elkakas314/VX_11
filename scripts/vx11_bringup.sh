#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# VX11 Bringup Script - Stable Wrapper for Auto-Installation
# 
# Purpose: Single entrypoint for reproducible core-only startup
# - Validates docker-compose config
# - Starts minimal services (madre + tentaculo_link)
# - Verifies health via tentaculo_link:8000 only
# - Leaves no background ports exposed except 8000
# 
# Usage: bash scripts/vx11_bringup.sh [--full] [--skipcheck]
###############################################################################

PROFILE="${1:-test}"
MODE="${2:-minimal}"  # minimal | full | automation
SKIP_HEALTH_CHECK="${3:-false}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export VX11_PROFILE="${PROFILE}"
export VX11_MODE="${MODE}"

cd "$REPO_ROOT"

###############################################################################
# 1. Validate compose config
###############################################################################
echo "[vx11_bringup] Validating docker-compose configuration..."
if ! docker compose -f docker-compose.full-test.yml config -q > /dev/null 2>&1; then
    echo "[ERROR] docker-compose.full-test.yml validation failed"
    exit 1
fi
echo "[OK] docker-compose valid"

###############################################################################
# 2. Show service names (discovery only, no assumptions)
###############################################################################
echo "[vx11_bringup] Available services:"
docker compose -f docker-compose.full-test.yml config --services | sed 's/^/  - /'

###############################################################################
# 3. Core startup (minimal: madre + tentaculo_link only)
###############################################################################
if [ "$MODE" = "minimal" ] || [ "$MODE" = "automation" ]; then
    echo "[vx11_bringup] Starting core services (madre + tentaculo_link)..."
    docker compose -f docker-compose.full-test.yml up -d --build madre tentaculo_link redis-test || {
        echo "[ERROR] Failed to start core services"
        exit 1
    }
    echo "[OK] Core services up"
    
    # Wait for services to be healthy
    sleep 3
    echo "[vx11_bringup] Waiting for services to be healthy..."
    docker compose -f docker-compose.full-test.yml ps
    
    if [ "$SKIP_HEALTH_CHECK" != "true" ]; then
        echo "[vx11_bringup] Health check: tentaculo_link:8000"
        for i in {1..30}; do
            if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
                echo "[OK] tentaculo_link health check passed"
                break
            fi
            echo "[retry $i/30] Waiting for tentaculo_link..."
            sleep 1
        done
    fi
fi

###############################################################################
# 4. Full profile (if requested)
###############################################################################
if [ "$MODE" = "full" ]; then
    echo "[vx11_bringup] Starting full profile (all test services)..."
    docker compose -f docker-compose.full-test.yml up -d --build || {
        echo "[ERROR] Failed to start full profile"
        exit 1
    }
    echo "[OK] Full profile up"
fi

###############################################################################
# 5. Automation mode (run checks + generate scorecard)
###############################################################################
if [ "$MODE" = "automation" ]; then
    echo "[vx11_bringup] Running automation pipeline..."
    bash scripts/automation_full_run.sh
fi

echo "[vx11_bringup] Startup complete. Access tentaculo_link at http://localhost:8000/"
exit 0
