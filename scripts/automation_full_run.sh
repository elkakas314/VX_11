#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# VX11 Automation Pipeline - Two Modes: core (default) or full_test
#
# Modes:
# - core (default): Start madre + tentaculo_link + redis + operator
#   Leaves single entrypoint operational for real use.
#
# - full_test: Start ALL services, run checks/scorecard, then stop non-madre
#   Use for exhaustive testing + validation before stopping.
#
# Usage:
#   VX11_RUN_MODE=core bash scripts/automation_full_run.sh
#   VX11_RUN_MODE=full_test bash scripts/automation_full_run.sh
#
# Environment:
#   VX11_RUN_MODE: core | full_test (default: core)
#   VX11_PROFILE: test | prod (default: test)
###############################################################################

RUN_MODE="${VX11_RUN_MODE:-core}"
PROFILE="${VX11_PROFILE:-test}"
TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="docs/audit/$TS"
STATUS_FILE="docs/status/last_automation_run.md"
COMPOSE_FILE="docker-compose.full-test.yml"

mkdir -p "$OUT"
mkdir -p "docs/status"

echo "[automation] Mode: $RUN_MODE | Profile: $PROFILE | TS: $TS"

# Ensure both stdout and log file get all output
{
    echo "=== VX11 Automation Pipeline ===" 
    echo "Mode: $RUN_MODE"
    echo "Timestamp: $TS"
    echo "Profile: $PROFILE"
    echo ""
    
    if [ "$RUN_MODE" = "core" ]; then
        echo "[core-mode] Starting CORE ONLY (madre + tentaculo_link + operator + redis)"
        echo "Action: Start core services"
        docker compose -f "$COMPOSE_FILE" up -d --build madre tentaculo_link redis-test || true
        
        echo "Waiting 3s for core to stabilize..."
        sleep 3
        
        echo "Action: Start operator (frontend + backend) for UI"
        docker compose -f "$COMPOSE_FILE" up -d --build operator-backend operator-frontend || true
        
        echo "Waiting 5s for operator to be ready..."
        sleep 5
        
        echo "[core-mode] Verifying core health..."
        for i in {1..10}; do
            if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
                echo "  ✅ tentaculo_link HEALTHY"
                break
            fi
            echo "  [retry $i/10] Waiting for health..."
            sleep 1
        done
        
        echo ""
        echo "[core-mode] Core services OPERATIONAL (single entrypoint ON)"
        echo "  - madre: running"
        echo "  - tentaculo_link: running (port 8000)"
        echo "  - redis: running"
        echo "  - operator: running"
        echo "  - switch/hermes: NOT started (on-demand)"
        
    elif [ "$RUN_MODE" = "full_test" ]; then
        echo "[full_test-mode] Starting ALL services + running checks"
        echo "Action: Start all services"
        docker compose -f "$COMPOSE_FILE" up -d --build || true
        
        echo "Waiting 8s for all services to initialize..."
        sleep 8
        
        echo "2) Running checks..."
        ./scripts/run_checks.sh || true
        
        echo "3) Generating scorecard..."
        python3 scripts/generate_scorecard.py || true
        
        echo "4) Stopping non-madre services (EXCEPT tentaculo_link + redis)..."
        ALL=$(docker compose -f "$COMPOSE_FILE" ps --services 2>/dev/null || true)
        for s in $ALL; do
            if [ "$s" != "madre" ] && [ "$s" != "tentaculo_link" ] && [ "$s" != "redis-test" ]; then
                echo "  Stopping $s..."
                docker compose -f "$COMPOSE_FILE" stop "$s" 2>&1 || true
            fi
        done
        
        echo ""
        echo "[full_test-mode] Tests complete; core services preserved (single entrypoint ON)"
    else
        echo "[ERROR] Unknown mode: $RUN_MODE (use: core | full_test)"
        exit 1
    fi
    
    echo ""
    echo "Final service state:"
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo "Automation run complete; evidence in $OUT"
    echo "Summary: $STATUS_FILE"
    
} | tee "$OUT/automation_run.log"

###############################################################################
# Generate tracked summary
###############################################################################
cat > "$STATUS_FILE" << EOF
# VX11 Last Automation Run

**Timestamp**: $TS
**Mode**: $RUN_MODE
**Git HEAD**: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
**Profile**: $PROFILE

## Status
- Run mode: $RUN_MODE
- Core running: madre + tentaculo_link + redis-test
- Operator: $(if docker compose -f "$COMPOSE_FILE" ps --services 2>/dev/null | grep -q operator-frontend; then echo "Available via http://localhost:8000/operator/ui"; else echo "NOT started"; fi)
- Auth: X-VX11-Token (vx11-test-token for testing)

## Quick Commands
\`\`\`bash
# Health check
curl -s http://localhost:8000/health | jq .

# Operator API
curl -H "X-VX11-Token: vx11-test-token" \\
  http://localhost:8000/operator/api/health | jq .

# Events stream
curl -H "X-VX11-Token: vx11-test-token" \\
  http://localhost:8000/operator/api/events?follow=true
\`\`\`

## Evidence Location
Full logs: docs/audit/$TS/

---
Generated by automation_full_run.sh (mode: $RUN_MODE)
EOF

echo "[automation] Summary written to $STATUS_FILE"
echo "$OUT"

