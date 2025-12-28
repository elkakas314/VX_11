#!/bin/bash
# Quick verification: INEE Integration status
# Run this to verify all deliverables are in place

set -e

echo "🔍 VX11 INEE Extended Integration Verification"
echo "=============================================="
echo ""

# Check 1: Code files
echo "✓ Checking code files..."
files=(
    "hormiguero/hormiguero/core/db/schema_inee_extended.py"
    "hormiguero/hormiguero/inee/models.py"
    "hormiguero/hormiguero/inee/builder.py"
    "hormiguero/hormiguero/inee/api/routes_extended.py"
)

for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        lines=$(wc -l < "$file")
        echo "  ✅ $file ($lines LOC)"
    else
        echo "  ❌ $file NOT FOUND"
        exit 1
    fi
done

# Check 2: Test suites
echo ""
echo "✓ Checking test suites..."
tests=(
    "tests/test_inee_p0_dormant.sh"
    "tests/test_inee_p1_builder_intent.sh"
    "tests/test_inee_db_schema.sh"
)

for test in "${tests[@]}"; do
    if [[ -f "$test" ]]; then
        lines=$(wc -l < "$test")
        echo "  ✅ $test ($lines LOC)"
    else
        echo "  ❌ $test NOT FOUND"
        exit 1
    fi
done

# Check 3: Audit documentation
echo ""
echo "✓ Checking audit documentation..."
audit_files=(
    "docs/audit/INEE_INTEGRATION_COMPLETE_20251228/INTEGRATION_SUMMARY.md"
    "docs/audit/INEE_INTEGRATION_COMPLETE_20251228/ENDPOINTS_AND_FEATURES.md"
    "docs/audit/INEE_INTEGRATION_COMPLETE_20251228/INVARIANTS_VERIFICATION.md"
    "docs/audit/INEE_INTEGRATION_COMPLETE_20251228/FINAL_DELIVERY_REPORT.md"
)

for file in "${audit_files[@]}"; do
    if [[ -f "$file" ]]; then
        lines=$(wc -l < "$file")
        echo "  ✅ $file ($lines lines)"
    else
        echo "  ❌ $file NOT FOUND"
        exit 1
    fi
done

# Check 4: Completion report
echo ""
echo "✓ Checking main completion report..."
if [[ -f "INEE_INTEGRATION_COMPLETION_REPORT.md" ]]; then
    lines=$(wc -l < "INEE_INTEGRATION_COMPLETION_REPORT.md")
    echo "  ✅ INEE_INTEGRATION_COMPLETION_REPORT.md ($lines lines)"
else
    echo "  ❌ INEE_INTEGRATION_COMPLETION_REPORT.md NOT FOUND"
    exit 1
fi

# Check 5: Git commits
echo ""
echo "✓ Checking git commits..."
commits=$(git log --oneline | grep "vx11: inee:" | wc -l)
if [[ $commits -ge 4 ]]; then
    echo "  ✅ Found $commits INEE integration commits"
    git log --oneline | grep "vx11: inee:" | head -5
else
    echo "  ❌ Expected >= 4 commits, found $commits"
    exit 1
fi

# Check 6: Proxy routes in tentaculo_link
echo ""
echo "✓ Checking proxy routes in tentaculo_link..."
proxy_count=$(grep -c "@app.post.*inee\|@app.get.*inee" tentaculo_link/main_v7.py || echo 0)
if [[ $proxy_count -gt 0 ]]; then
    echo "  ✅ Found $proxy_count proxy routes"
else
    echo "  ❌ No proxy routes found"
    exit 1
fi

# Check 7: Feature flags
echo ""
echo "✓ Checking feature flags in code..."
flags=(
    "VX11_INEE_ENABLED"
    "HORMIGUERO_BUILDER_ENABLED"
    "VX11_INEE_REMOTE_PLANE_ENABLED"
    "VX11_REWARDS_ENABLED"
)

for flag in "${flags[@]}"; do
    if grep -r "$flag" hormiguero/hormiguero/inee/ > /dev/null; then
        echo "  ✅ $flag referenced"
    else
        echo "  ⚠️  $flag not found"
    fi
done

# Check 8: Summary statistics
echo ""
echo "📊 Summary Statistics"
echo "===================="

# Count total LOC in new files
total_loc=$(wc -l hormiguero/hormiguero/inee/*.py hormiguero/hormiguero/core/db/schema_inee_extended.py 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
echo "Total new code: ~$total_loc LOC"

# Count test cases
test_cases=$(grep -c "TEST\|test_" tests/test_inee_*.sh || echo "0")
echo "Test cases: $test_cases+"

# Count DB tables
db_tables=$(grep -c "CREATE TABLE" hormiguero/hormiguero/core/db/schema_inee_extended.py || echo "0")
echo "DB tables added: $db_tables"

echo ""
echo "✅ All verification checks PASSED!"
echo ""
echo "📚 Documentation:"
echo "   - Main report: INEE_INTEGRATION_COMPLETION_REPORT.md"
echo "   - Audit docs: docs/audit/INEE_INTEGRATION_COMPLETE_20251228/"
echo ""
echo "🚀 Next steps:"
echo "   1. Run tests: bash tests/test_inee_p0_dormant.sh"
echo "   2. Verify dormant: curl -H 'x-vx11-token: vx11-local-token' http://localhost:8000/operator/inee/status"
echo "   3. Enable (optional): Set VX11_INEE_ENABLED=1 in .env"
echo ""
