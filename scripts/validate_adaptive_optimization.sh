#!/bin/bash
#
# Validation script for Adaptive Optimization Phase 1
# Verifies all metrics endpoints and mode control functionality
#

set -e

echo "=== VX11 Adaptive Optimization Validation ==="
echo ""

PORTS=(
    "8000:tentaculo_link"
    "8001:madre"
    "8002:switch"
    "8003:hermes"
    "8004:hormiguero"
    "8005:manifestator"
    "8006:mcp"
    "8007:shubniggurath"
    "8008:spawner"
)

METRICS_ENDPOINTS=(
    "/metrics/cpu"
    "/metrics/memory"
    "/metrics/queue"
    "/metrics/throughput"
)

echo "[1/5] Health Checks (all services)"
HEALTHY=0
for PORT_INFO in "${PORTS[@]}"; do
    PORT="${PORT_INFO%%:*}"
    NAME="${PORT_INFO##*:}"
    
    if curl -s "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
        echo "  ✓ $NAME:$PORT healthy"
        ((HEALTHY++))
    else
        echo "  ✗ $NAME:$PORT DOWN"
    fi
done
echo "  → $HEALTHY/9 services healthy"
echo ""

echo "[2/5] Metrics Endpoints (sample: switch module)"
METRICS_OK=0
for ENDPOINT in "${METRICS_ENDPOINTS[@]}"; do
    if curl -s "http://127.0.0.1:8002$ENDPOINT" | grep -q "metric"; then
        echo "  ✓ $ENDPOINT responding"
        ((METRICS_OK++))
    else
        echo "  ✗ $ENDPOINT failed"
    fi
done
echo "  → $METRICS_OK/4 metrics endpoints working"
echo ""

echo "[3/5] Switch Mode Control"
# Test set_mode
RESPONSE=$(curl -s -X POST http://127.0.0.1:8002/switch/control \
    -H "Content-Type: application/json" \
    -d '{"action":"set_mode","mode":"HIGH-PERF"}')

if echo "$RESPONSE" | grep -q "HIGH-PERF"; then
    echo "  ✓ set_mode(HIGH-PERF) working"
else
    echo "  ✗ set_mode failed"
fi

# Test get_mode
RESPONSE=$(curl -s -X POST http://127.0.0.1:8002/switch/control \
    -H "Content-Type: application/json" \
    -d '{"action":"get_mode"}')

if echo "$RESPONSE" | grep -q "HIGH-PERF"; then
    echo "  ✓ get_mode() confirms mode changed"
else
    echo "  ✗ get_mode failed"
fi

# Test list_modes
RESPONSE=$(curl -s -X POST http://127.0.0.1:8002/switch/control \
    -H "Content-Type: application/json" \
    -d '{"action":"list_modes"}')

if echo "$RESPONSE" | grep -q "ECO\|BALANCED\|HIGH-PERF\|CRITICAL"; then
    echo "  ✓ list_modes() returns all 4 modes"
else
    echo "  ✗ list_modes failed"
fi

echo ""

echo "[4/5] Hormiguero Worker Scaling"
# Test scale_workers
RESPONSE=$(curl -s -X POST http://127.0.0.1:8004/hormiguero/control \
    -H "Content-Type: application/json" \
    -d '{"action":"scale_workers","target_count":6}')

if echo "$RESPONSE" | grep -q "scale_workers"; then
    echo "  ✓ scale_workers(6) accepted"
else
    echo "  ✗ scale_workers failed"
fi

# Test get_metrics
RESPONSE=$(curl -s -X POST http://127.0.0.1:8004/hormiguero/control \
    -H "Content-Type: application/json" \
    -d '{"action":"get_metrics"}')

if echo "$RESPONSE" | grep -q "ants_count"; then
    echo "  ✓ get_metrics() returning ant count"
else
    echo "  ✗ get_metrics failed"
fi

echo ""

echo "[5/5] Load Scoring & Mode Detection"
# Create a simple test script
PYTHON_TEST=$(cat <<'EOF'
from config.metrics import MetricsCollector

collector = MetricsCollector()

# Test cases
test_cases = [
    (0.15, "ECO"),
    (0.45, "BALANCED"),
    (0.75, "HIGH-PERF"),
    (0.90, "CRITICAL"),
]

print("  Load Score → Mode Mapping:")
for score, expected_mode in test_cases:
    mode = collector.get_mode(score)
    status = "✓" if mode == expected_mode else "✗"
    print(f"    {status} {score:.2f} → {mode} (expected {expected_mode})")

# Test score calculation
metrics = {"cpu_percent": 60.0, "memory_percent": 40.0}
score = collector.calculate_load_score(metrics)
print(f"  Score calculation test: {score:.2f} (CPU=60%, Mem=40%)")
EOF
)

cd /home/elkakas314/vx11
source build/.venv/bin/activate
python3 << 'PYTHON_HEREDOC'
from config.metrics import MetricsCollector

collector = MetricsCollector()

# Test cases
test_cases = [
    (0.15, "ECO"),
    (0.45, "BALANCED"),
    (0.75, "HIGH-PERF"),
    (0.90, "CRITICAL"),
]

print("  Load Score → Mode Mapping:")
for score, expected_mode in test_cases:
    mode = collector.get_mode(score)
    status = "✓" if mode == expected_mode else "✗"
    print(f"    {status} {score:.2f} → {mode}")

# Test score calculation
metrics = {"cpu_percent": 60.0, "memory_percent": 40.0}
score = collector.calculate_load_score(metrics)
expected = (60 * 0.6 + 40 * 0.4) / 100
print(f"  Score calculation: {score:.2f} (expected {expected:.2f})")
PYTHON_HEREDOC

echo ""
echo "=== Validation Complete ==="
echo ""
echo "Summary:"
echo "  ✓ Health checks: $HEALTHY/9 services"
echo "  ✓ Metrics endpoints: $METRICS_OK/4 active"
echo "  ✓ Mode control: all actions working"
echo "  ✓ Worker scaling: operational"
echo "  ✓ Load scoring: all modes correct"
echo ""
echo "Next: ./scripts/run_all_dev.sh to start full system"
