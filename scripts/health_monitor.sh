#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh"
# VX11 Continuous Health Monitor
# Ejecutar con: ./scripts/health_monitor.sh (cron job cada 5 minutos)

PORTS=(8000 8001 8002 8003 8004 8005 8006 8007 8008)
MODULES=(tentaculo_link madre switch hermes hormiguero manifestator mcp shubniggurath spawner)
LOG_FILE="build/artifacts/logs/health_monitor.log"
ALERT_FILE="build/artifacts/logs/alerts.log"

timestamp() {
    date -u +'%Y-%m-%dT%H:%M:%SZ'
}

log() {
    echo "[$(timestamp)] $1" >> "$LOG_FILE"
}

alert() {
    echo "[$(timestamp)] ALERT: $1" >> "$ALERT_FILE"
    echo "[$(timestamp)] ALERT: $1"
}

log "Health check cycle started"

failed_count=0
for i in "${!PORTS[@]}"; do
    port=${PORTS[$i]}
    module=${MODULES[$i]}
    
    if curl -sS --max-time 2 "http://127.0.0.1:${port}/health" > /dev/null 2>&1; then
        log "  ✓ $module:$port"
    else
        log "  ✗ $module:$port"
        alert "$module:$port is not responding"
        ((failed_count++))
    fi
done

if [ $failed_count -eq 0 ]; then
    log "Health check PASSED: All 9/9 services responding"
else
    alert "Health check FAILED: $failed_count/$((${#PORTS[@]})) services not responding"
fi

log "Health check cycle completed"
