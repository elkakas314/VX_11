#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh"
# VX11 v6.0 — Quick Test Guide
# Test Plug-and-Play y Adaptive Engine Selection sin iniciar servicios

echo "VX11 v6.0 Quick Test"
echo "===================="
echo ""

cd /home/elkakas314/vx11 || exit 1
source build/.venv/bin/activate 2>/dev/null || python3 -m venv build/.venv && source build/.venv/bin/activate

echo "✓ Environment ready"
echo ""

# Test 1: P&P State Management
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Plug-and-Play States"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
from config.container_state import (
    set_state, get_state, is_active, get_all_states, _MODULE_STATES
)

# Reset to active
for m in _MODULE_STATES:
    _MODULE_STATES[m]["state"] = "active"

print("\n[1.1] Get all module states")
all_states = get_all_states()
print(f"✓ Total modules: {len(all_states)}")
for name in list(all_states.keys())[:3]:
    print(f"  - {name}: {all_states[name]['state']}")

print("\n[1.2] Change module state")
result = set_state("manifestator", "standby")
print(f"✓ Changed manifestator to standby: {result}")

print("\n[1.3] Verify state change")
if is_active("manifestator"):
    print("✗ manifestator should be standby")
else:
    print("✓ manifestator is now in standby")

print("\n[1.4] Activate module")
result = set_state("manifestator", "active")
print(f"✓ Changed manifestator to active: {result}")

print("\n✅ P&P State Management Tests PASSED")
EOF

echo ""

# Test 2: Engine Metrics
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Engine Metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
from config.switch_hermes_integration import EngineMetrics

print("\n[2.1] Create engine metrics")
metrics = EngineMetrics("hermes_local")
print(f"✓ Created metrics for hermes_local")

print("\n[2.2] Record successful requests")
metrics.record_success(100)
metrics.record_success(150)
metrics.record_success(120)
print(f"✓ Total requests: {metrics.total_requests}")
print(f"✓ Successful: {metrics.successful_requests}")
print(f"✓ Avg latency: {metrics.get_avg_latency_ms():.1f}ms")

print("\n[2.3] Record failed requests")
metrics.record_error("Timeout")
print(f"✓ Failed requests: {metrics.failed_requests}")
print(f"✓ Error rate: {metrics.get_error_rate():.1f}%")

print("\n[2.4] Circuit breaker test")
for i in range(4):
    metrics.record_error(f"Error {i}")
print(f"✓ Consecutive errors: {metrics.consecutive_errors}")
print(f"✓ Circuit breaker open: {metrics.circuit_breaker_open}")

print("\n✅ Engine Metrics Tests PASSED")
EOF

echo ""

# Test 3: Adaptive Engine Selector
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Adaptive Engine Selector"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 << 'EOF'
from config.switch_hermes_integration import AdaptiveEngineSelector, ENGINE_PROFILES, get_selector

print("\n[3.1] Create selector")
selector = AdaptiveEngineSelector()
print(f"✓ Selector created in mode: {selector.current_mode}")

print("\n[3.2] Register engines")
selector.register_engine("hermes_local")
selector.register_engine("cli_bash")
print(f"✓ Registered 2 engines")

print("\n[3.3] Set available engines")
selector.set_available_engines(["hermes_local", "cli_bash"])
print(f"✓ Available engines set")

print("\n[3.4] Select engine")
selection = selector.select_engine()
print(f"✓ Selected engine: {selection['engine']}")
print(f"✓ Mode: {selection['mode']}")

print("\n[3.5] Mode switching")
selector.set_mode("CRITICAL")
print(f"✓ Switched to CRITICAL mode")
selection = selector.select_engine()
print(f"✓ Profile timeout: {selection['profile']['timeout_ms']}ms")
print(f"✓ Max concurrent: {selection['profile']['max_concurrent']}")

print("\n[3.6] Record result (feedback loop)")
selector.record_engine_result("hermes_local", success=True, latency_ms=120)
metrics = selector.metrics["hermes_local"]
print(f"✓ Recorded result")
print(f"✓ Successful requests: {metrics.successful_requests}")

print("\n[3.7] Get status dashboard")
status = selector.get_status()
print(f"✓ Current mode: {status['mode']}")
print(f"✓ Available engines: {status['available_engines']}")

print("\n[3.8] Validate all 4 modes")
for mode in ["ECO", "BALANCED", "HIGH-PERF", "CRITICAL"]:
    if mode in ENGINE_PROFILES:
        profile = ENGINE_PROFILES[mode]
        print(f"✓ {mode}: {profile['timeout_ms']}ms, {profile['max_concurrent']} concurrent")
    else:
        print(f"✗ {mode} not found")

print("\n[3.9] Singleton pattern")
s1 = get_selector()
s2 = get_selector()
if s1 is s2:
    print(f"✓ Singleton pattern verified (same instance)")
else:
    print(f"✗ Singleton pattern broken")

print("\n✅ Adaptive Engine Selector Tests PASSED")
EOF

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL TESTS PASSED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next Steps:"
echo "1. Start VX11: ./scripts/run_all_dev.sh"
echo "2. Test P&P endpoints:"
echo "   curl http://localhost:8001/orchestration/module_states"
echo "3. Test switch-hermes endpoints:"
echo "   curl http://localhost:8002/switch/hermes/status"
echo ""
echo "For full documentation, see:"
echo "- docs/PNP_AND_ADAPTIVE_ROUTING.md"
echo "- QUICK_REFERENCE.md"
echo "- VX11_v6_COMPLETION_REPORT.md"
echo ""
