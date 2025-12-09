#!/bin/bash
#
# VX11 Development Startup Script (v6.0)
# Arranca todos los servicios en orden correcto con health checks
#
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"
source build/.venv/bin/activate

# ============ LOAD CONFIG ============
echo "Loading VX11 configuration..."
eval $(python3 - <<'PY'
from config.settings import settings
print(f"TENTACULO_PORT={settings.tentaculo_link_port}")
print(f"MADRE_PORT={settings.madre_port}")
print(f"SWITCH_PORT={settings.switch_port}")
print(f"HORMIGUERO_PORT={settings.hormiguero_port}")
print(f"MANIFESTATOR_PORT={settings.manifestator_port}")
print(f"MCP_PORT={settings.mcp_port}")
print(f"SHUB_PORT={settings.shub_port}")
print(f"HERMES_PORT={settings.hermes_port}")
print(f"SPAWNER_PORT={settings.spawner_port}")
print(f"OPERATOR_PORT={getattr(settings, 'operator_port', 8011)}")
PY
)

# ============ HELPER FUNCTIONS ============

start_service() {
    local name=$1
    local module=$2
    local port=$3
    local max_retries=3
    local retry_count=0
    
    echo ""
    echo "[$(date '+%H:%M:%S')] Starting $name (port $port)..."
    
    # Try to start, with retry logic
    while [ $retry_count -lt $max_retries ]; do
        # Check if port is already in use
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "  ⚠ Port $port already in use, trying to bind anyway..."
        fi
        
        # Start service in background
        uvicorn "$module.main:app" --host 0.0.0.0 --port $port --reload > "build/artifacts/logs/${name}_dev.log" 2>&1 &
        local pid=$!
        
        # Wait for startup
        sleep 2
        
        # Check if process is still alive
        if ! kill -0 $pid 2>/dev/null; then
            echo "  ✗ Failed to start (process died immediately)"
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                echo "  → Retrying... ($retry_count/$max_retries)"
                sleep 1
                continue
            else
                echo "  ✗ Max retries reached. Check logs/${name}_dev.log"
                return 1
            fi
        fi
        
        # Wait for health endpoint
        local health_retries=10
        local health_check=0
        while [ $health_check -lt $health_retries ]; do
            if curl -s http://127.0.0.1:$port/health >/dev/null 2>&1; then
                echo "  ✓ $name started (PID $pid)"
                return 0
            fi
            sleep 0.5
            health_check=$((health_check + 1))
        done
        
        echo "  ✗ Health endpoint not responding"
        kill $pid 2>/dev/null || true
        retry_count=$((retry_count + 1))
        
        if [ $retry_count -lt $max_retries ]; then
            echo "  → Retrying... ($retry_count/$max_retries)"
            sleep 1
        fi
    done
    
    echo "  ✗ Failed to start $name after $max_retries attempts"
    return 1
}

# ============ STARTUP SEQUENCE ============

mkdir -p build/artifacts/logs

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           VX11 Development Environment (v6.0)                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Configuration:"
echo "  Tentaculo    : $TENTACULO_PORT"
echo "  Madre        : $MADRE_PORT"
echo "  Switch       : $SWITCH_PORT"
echo "  Hermes       : $HERMES_PORT"
echo "  Hormiguero   : $HORMIGUERO_PORT"
echo "  Manifestator : $MANIFESTATOR_PORT"
echo "  MCP          : $MCP_PORT"
echo "  Shubniggurath: $SHUB_PORT"
echo "  Spawner      : $SPAWNER_PORT"
echo ""
echo "Startup sequence (order matters for dependencies):"
echo ""

# Startup order: No external deps first, then others
# 1. hermes (base model registry, no deps)
# 2. switch (uses hermes, but not critical at start)
# 3. madre (core orchestration)
# 4. hormiguero (uses switch)
# 5. manifestator (independent)
# 6. mcp (conversational, depends on madre/switch)
# 7. shubniggurath (independent)
# 8. spawner (independent)
# 9. tentaculo_link (depends on all, acts as proxy)
# 10. operator-backend (frontend served separately)

FAILED=0

start_service "hermes" "switch.hermes" $HERMES_PORT || FAILED=$((FAILED + 1))
start_service "switch" "switch" $SWITCH_PORT || FAILED=$((FAILED + 1))
start_service "madre" "madre" $MADRE_PORT || FAILED=$((FAILED + 1))
start_service "hormiguero" "hormiguero" $HORMIGUERO_PORT || FAILED=$((FAILED + 1))
start_service "manifestator" "manifestator" $MANIFESTATOR_PORT || FAILED=$((FAILED + 1))
start_service "mcp" "mcp" $MCP_PORT || FAILED=$((FAILED + 1))
start_service "shubniggurath" "shubniggurath" $SHUB_PORT || FAILED=$((FAILED + 1))
start_service "spawner" "spawner" $SPAWNER_PORT || FAILED=$((FAILED + 1))
start_service "tentaculo_link" "tentaculo_link" $TENTACULO_PORT || FAILED=$((FAILED + 1))
start_service "operator-backend" "operator.main" $OPERATOR_PORT || FAILED=$((FAILED + 1))

echo ""
echo "════════════════════════════════════════════════════════════════"
if [ $FAILED -eq 0 ]; then
    echo "✓ All services started successfully!"
    echo ""
    echo "Endpoints available:"
    for port in $TENTACULO_PORT $MADRE_PORT $SWITCH_PORT $HERMES_PORT; do
        name=$([ $port -eq $TENTACULO_PORT ] && echo "Tentaculo Link" || echo "Service")
        echo "  http://127.0.0.1:$port/health"
    done
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo "════════════════════════════════════════════════════════════════"
    
    # Wait indefinitely
    wait
else
    echo "✗ $FAILED service(s) failed to start"
    echo "Check build/artifacts/logs/ for details"
    echo "════════════════════════════════════════════════════════════════"
    exit 1
fi
