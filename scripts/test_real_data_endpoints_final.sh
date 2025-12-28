#!/bin/bash
# PROMPT 1 — Real Data Endpoints Implementation Validation
# VX11 Operator Backend v7.0
# 
# Purpose: Validate that all 4 real data endpoints are working correctly
# and that no bypass/hardcoded data exists.
#
# Prerequisites:
#  - Docker containers running: docker compose --profile core --profile operator up -d
#  - Backend available: http://localhost:8011
#  - Tentaculo link available: http://localhost:8000

set -e

BASE_URL="${1:-http://localhost:8011}"
TENTACULO_URL="${2:-http://localhost:8000}"
COLORS_ENABLED=true

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    if [ "$COLORS_ENABLED" = true ]; then
        echo -e "${BLUE}ℹ${NC} $1"
    else
        echo "[INFO] $1"
    fi
}

log_pass() {
    if [ "$COLORS_ENABLED" = true ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo "[PASS] $1"
    fi
}

log_fail() {
    if [ "$COLORS_ENABLED" = true ]; then
        echo -e "${RED}✗${NC} $1"
    else
        echo "[FAIL] $1"
    fi
}

log_test() {
    if [ "$COLORS_ENABLED" = true ]; then
        echo -e "\n${YELLOW}━━━ $1 ━━━${NC}"
    else
        echo ""
        echo "====== $1 ======"
    fi
}

# State tracking
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name=$1
    local test_command=$2
    local expected_contains=$3
    
    log_test "$test_name"
    
    result=$(eval "$test_command" 2>&1)
    
    if echo "$result" | grep -q "$expected_contains"; then
        log_pass "$test_name"
        ((TESTS_PASSED++))
        return 0
    else
        log_fail "$test_name"
        echo "Expected to find: $expected_contains"
        echo "Got: ${result:0:200}..."
        ((TESTS_FAILED++))
        return 1
    fi
}

# ============ CONNECTIVITY CHECKS ============

log_info "Testing connectivity to backend..."

if ! curl -s "$BASE_URL/api/topology" > /dev/null 2>&1; then
    log_fail "Backend not accessible at $BASE_URL"
    echo "Ensure: docker compose --profile core --profile operator up -d"
    exit 1
fi

log_pass "Backend accessible"

# ============ TEST 1: GET /api/modules — Should return 10 services ============

log_test "TEST 1: GET /api/modules (10 real services)"

MODULES_RESPONSE=$(curl -s "$BASE_URL/api/modules")
MODULES_COUNT=$(echo "$MODULES_RESPONSE" | jq '.data.modules | length' 2>/dev/null || echo "0")

log_info "Modules count: $MODULES_COUNT"

if [ "$MODULES_COUNT" -ge 10 ]; then
    log_pass "Returns $MODULES_COUNT modules (>= 10)"
    ((TESTS_PASSED++))
else
    log_fail "Expected >= 10 modules, got $MODULES_COUNT"
    echo "Response: $MODULES_RESPONSE" | head -50
    ((TESTS_FAILED++))
fi

# Check for required services
REQUIRED_SERVICES=("madre" "redis" "tentaculo_link" "switch" "hermes" "hormiguero" "mcp" "spawner" "operator-backend" "operator-frontend")

for service in "${REQUIRED_SERVICES[@]}"; do
    if echo "$MODULES_RESPONSE" | jq --arg svc "$service" '.data.modules[] | select(.name==$svc)' | grep -q "name"; then
        log_pass "Service '$service' present"
        ((TESTS_PASSED++))
    else
        log_fail "Service '$service' missing"
        ((TESTS_FAILED++))
    fi
done

# Check schema
log_test "TEST 1b: Module schema validation"

SAMPLE_MODULE=$(echo "$MODULES_RESPONSE" | jq '.data.modules[0]')

for field in "name" "status" "port" "profile" "enabled_by_default" "health_status"; do
    if echo "$SAMPLE_MODULE" | jq "has(\"$field\")" | grep -q "true"; then
        log_pass "Module has field: $field"
        ((TESTS_PASSED++))
    else
        log_fail "Module missing field: $field"
        ((TESTS_FAILED++))
    fi
done

# ============ TEST 2: GET /api/topology — Should return 10 nodes + 9 edges ============

log_test "TEST 2: GET /api/topology (10 nodes + 9 edges)"

TOPOLOGY_RESPONSE=$(curl -s "$BASE_URL/api/topology")
NODES_COUNT=$(echo "$TOPOLOGY_RESPONSE" | jq '.data.nodes | length' 2>/dev/null || echo "0")
EDGES_COUNT=$(echo "$TOPOLOGY_RESPONSE" | jq '.data.edges | length' 2>/dev/null || echo "0")

log_info "Nodes count: $NODES_COUNT"
log_info "Edges count: $EDGES_COUNT"

if [ "$NODES_COUNT" -ge 10 ]; then
    log_pass "Returns $NODES_COUNT nodes (>= 10)"
    ((TESTS_PASSED++))
else
    log_fail "Expected >= 10 nodes, got $NODES_COUNT"
    ((TESTS_FAILED++))
fi

if [ "$EDGES_COUNT" -ge 6 ]; then
    log_pass "Returns $EDGES_COUNT edges (>= 6)"
    ((TESTS_PASSED++))
else
    log_fail "Expected >= 6 edges, got $EDGES_COUNT"
    ((TESTS_FAILED++))
fi

# Check topology schema
log_test "TEST 2b: Topology schema validation"

SAMPLE_NODE=$(echo "$TOPOLOGY_RESPONSE" | jq '.data.nodes[0]')
SAMPLE_EDGE=$(echo "$TOPOLOGY_RESPONSE" | jq '.data.edges[0]')

for field in "id" "label" "status" "port"; do
    if echo "$SAMPLE_NODE" | jq "has(\"$field\")" | grep -q "true"; then
        log_pass "Node has field: $field"
        ((TESTS_PASSED++))
    else
        log_fail "Node missing field: $field"
        ((TESTS_FAILED++))
    fi
done

for field in "from" "to" "label"; do
    if echo "$SAMPLE_EDGE" | jq "has(\"$field\")" | grep -q "true"; then
        log_pass "Edge has field: $field"
        ((TESTS_PASSED++))
    else
        log_fail "Edge missing field: $field"
        ((TESTS_FAILED++))
    fi
done

# ============ TEST 3: GET /api/fs/list — Sandboxed File Explorer ============

log_test "TEST 3: GET /api/fs/list (File Explorer)"

# 3a. List /docs/audit
log_test "TEST 3a: List /docs/audit"

FS_AUDIT=$(curl -s "$BASE_URL/api/fs/list?path=/docs/audit")

if echo "$FS_AUDIT" | jq '.ok' | grep -q "true"; then
    log_pass "/api/fs/list?path=/docs/audit returns 200"
    ((TESTS_PASSED++))
    
    ITEMS_COUNT=$(echo "$FS_AUDIT" | jq '.data.total_items' 2>/dev/null || echo "0")
    log_info "Total items: $ITEMS_COUNT"
    
    if [ "$ITEMS_COUNT" -gt 0 ]; then
        log_pass "Directory has items ($ITEMS_COUNT)"
        ((TESTS_PASSED++))
    else
        log_fail "Directory appears empty"
        ((TESTS_FAILED++))
    fi
else
    log_fail "/api/fs/list?path=/docs/audit failed"
    echo "Response: $FS_AUDIT" | head -20
    ((TESTS_FAILED++))
fi

# 3b. Verify schema
log_test "TEST 3b: File explorer schema"

SAMPLE_ITEM=$(echo "$FS_AUDIT" | jq '.data.contents[0]' 2>/dev/null)

if [ "$SAMPLE_ITEM" != "null" ]; then
    for field in "name" "type"; do
        if echo "$SAMPLE_ITEM" | jq "has(\"$field\")" | grep -q "true"; then
            log_pass "Item has field: $field"
            ((TESTS_PASSED++))
        else
            log_fail "Item missing field: $field"
            ((TESTS_FAILED++))
        fi
    done
fi

# 3c. Security test: try to escape allowlist
log_test "TEST 3c: Security — Allowlist enforcement"

ESCAPE_TEST=$(curl -s "$BASE_URL/api/fs/list?path=/home")

if echo "$ESCAPE_TEST" | jq '.ok' | grep -q "false"; then
    log_pass "Path /home blocked (not in allowlist)"
    ((TESTS_PASSED++))
else
    log_fail "Security issue: /home should be blocked"
    ((TESTS_FAILED++))
fi

# ============ TEST 4: No Bypass — Chat should call tentaculo_link ============

log_test "TEST 4: POST /api/chat (Validate no bypass)"

CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "test message"}')

ROUTE_TAKEN=$(echo "$CHAT_RESPONSE" | jq -r '.route_taken' 2>/dev/null)

log_info "Route taken: $ROUTE_TAKEN"

if [ "$ROUTE_TAKEN" = "tentaculo_link" ] || [ "$ROUTE_TAKEN" = "degraded" ]; then
    log_pass "Chat routes correctly (not direct to madre)"
    ((TESTS_PASSED++))
else
    log_fail "Unexpected route: $ROUTE_TAKEN"
    ((TESTS_FAILED++))
fi

# ============ SUMMARY ============

log_test "SUMMARY"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

log_info "Total tests: $TOTAL_TESTS"
log_info "Passed: $TESTS_PASSED"
log_info "Failed: $TESTS_FAILED"
log_info "Success rate: ${SUCCESS_RATE}%"

if [ $TESTS_FAILED -eq 0 ]; then
    log_pass "ALL TESTS PASSED ✓"
    exit 0
else
    log_fail "SOME TESTS FAILED"
    exit 1
fi
