#!/bin/bash
# VX11 Stability P0 Suite - Quick Validation Script
# Run this to validate the harness is working correctly

set -e

echo "════════════════════════════════════════════════════════════════"
echo "VX11 STABILITY P0 SUITE - QUICK VALIDATION"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Unit tests
echo "✅ RUNNING UNIT TESTS (no docker required)..."
echo ""
python3 -m pytest tests/test_stability_p0_runner_unit.py -v --tb=short
echo ""

# 2. Dry-run validation
echo "✅ RUNNING DRY-RUN VALIDATION..."
echo ""
python3 -c "
import sys
sys.path.insert(0, '.')
from scripts.vx11_stability_p0 import MODULE_DEPENDENCY_MAP, topological_sort, CANONICAL_MODULE_ORDER

print('[DRY-RUN] Validating harness structure...\n')

sorted_mods = topological_sort(CANONICAL_MODULE_ORDER)
print('Module order (topologically sorted):')
for i, mod in enumerate(sorted_mods, 1):
    deps = MODULE_DEPENDENCY_MAP[mod]['depends_on']
    print(f'  {i}. {mod:20} deps: {deps}')

print(f'\n✅ Total modules: {len(sorted_mods)}')
print(f'✅ Health endpoints: {sum(len(m[\"health_endpoints\"]) for m in MODULE_DEPENDENCY_MAP.values())}')
print(f'✅ Test patterns: {sum(len(m[\"test_patterns\"]) for m in MODULE_DEPENDENCY_MAP.values())}')
print(f'✅ No circular dependencies detected')
"
echo ""

# 3. Integration tests status
echo "✅ INTEGRATION TESTS STATUS..."
echo ""
python3 -m pytest tests/test_stability_p0_runner_integration.py -v --tb=short
echo ""

# 4. Script help
echo "✅ HARNESS CLI HELP..."
echo ""
python3 scripts/vx11_stability_p0.py --help | head -20
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ ALL VALIDATION CHECKS PASSED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📖 Documentation: docs/STABILITY_P0.md"
echo "🚀 Quick start: python3 scripts/vx11_stability_p0.py --help"
echo ""
