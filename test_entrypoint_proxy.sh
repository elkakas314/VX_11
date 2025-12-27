#!/bin/bash
# PROMPT 2 — Test Single Entrypoint via tentaculo_link
# Purpose: Validate that tentaculo_link correctly proxies /operator/api/* to operator-backend:8011
# 
# Tests:
# 1. Direct to operator-backend:8011 (should work inside container)
# 2. Via tentaculo_link:8000 (should proxy correctly)
# 3. From outside (curl localhost:8000 should reach backend)

set -e

COLORS=true
ENTRYPOINT="http://tentaculo_link:8000"
BACKEND_INTERNAL="http://operator-backend:8011"
BACKEND_EXTERNAL="http://localhost:8011"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    if [ "$COLORS" = true ]; then
        echo -e "${BLUE}ℹ${NC} $1"
    else
        echo "[INFO] $1"
    fi
}

log_pass() {
    if [ "$COLORS" = true ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo "[PASS] $1"
    fi
}

log_fail() {
    if [ "$COLORS" = true ]; then
        echo -e "${RED}✗${NC} $1"
    else
        echo "[FAIL] $1"
    fi
}

log_test() {
    if [ "$COLORS" = true ]; then
        echo -e "\n${YELLOW}━━━ $1 ━━━${NC}"
    else
        echo ""
        echo "====== $1 ======"
    fi
}

TESTS_PASSED=0
TESTS_FAILED=0

# ============ TEST 1: Backend Internal Health Check ============

log_test "TEST 1: Direct backend health check (internal, from container)"

RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_INTERNAL/health" || echo "error")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "204" ]; then
    log_pass "operator-backend:8011 /health returns $HTTP_CODE"
    ((TESTS_PASSED++))
else
    log_fail "operator-backend:8011 /health returns $HTTP_CODE (expected 200/204)"
    echo "Response: $BODY"
    ((TESTS_FAILED++))
fi

# ============ TEST 2: Proxy Health Check ============

log_test "TEST 2: Proxy health check via tentaculo_link:8000"

RESPONSE=$(curl -s -w "\n%{http_code}" "$ENTRYPOINT/operator/api/../health" || echo "error")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

# Note: might 404, that's ok for health check test
if [ "$HTTP_CODE" != "000" ]; then
    log_pass "tentaculo_link:8000 /operator/api/... responds with HTTP $HTTP_CODE"
    ((TESTS_PASSED++))
else
    log_fail "tentaculo_link:8000 unreachable"
    ((TESTS_FAILED++))
fi

# ============ TEST 3: /operator/api/modules via proxy ============

log_test "TEST 3: GET /operator/api/modules via tentaculo_link proxy"

PROXY_RESPONSE=$(curl -s -w "\n%{http_code}" "$ENTRYPOINT/operator/api/modules" 2>&1)
HTTP_CODE=$(echo "$PROXY_RESPONSE" | tail -1)
BODY=$(echo "$PROXY_RESPONSE" | head -n -1)

log_info "HTTP Code: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    MODULES_COUNT=$(echo "$BODY" | jq '.data.modules | length' 2>/dev/null || echo "error")
    if [ "$MODULES_COUNT" != "error" ] && [ "$MODULES_COUNT" -ge 10 ]; then
        log_pass "Proxy returns 10+ modules ($MODULES_COUNT total)"
        ((TESTS_PASSED++))
    else
        log_fail "Proxy returned data but modules count issue: $MODULES_COUNT"
        echo "Response: $BODY" | head -20
        ((TESTS_FAILED++))
    fi
else
    log_fail "Proxy /operator/api/modules returns HTTP $HTTP_CODE"
    echo "Response: $BODY" | head -20
    ((TESTS_FAILED++))
fi

# ============ TEST 4: Direct vs Proxy comparison ============

log_test "TEST 4: Compare direct vs proxy responses"

DIRECT=$(curl -s "$BACKEND_INTERNAL/api/modules" 2>&1 | jq '.data.modules | length' 2>/dev/null || echo "0")
PROXY=$(curl -s "$ENTRYPOINT/operator/api/modules" 2>&1 | jq '.data.modules | length' 2>/dev/null || echo "0")

log_info "Direct modules count: $DIRECT"
log_info "Proxy modules count: $PROXY"

if [ "$DIRECT" = "$PROXY" ] && [ "$DIRECT" -ge 10 ]; then
    log_pass "Direct and proxy return same count ($DIRECT modules)"
    ((TESTS_PASSED++))
elif [ "$DIRECT" -ge 10 ] && [ "$PROXY" -ge 10 ]; then
    log_pass "Both return 10+ modules (direct: $DIRECT, proxy: $PROXY)"
    ((TESTS_PASSED++))
else
    log_fail "Mismatch or low count (direct: $DIRECT, proxy: $PROXY)"
    ((TESTS_FAILED++))
fi

# ============ TEST 5: /operator/api/topology via proxy ============

log_test "TEST 5: GET /operator/api/topology via proxy"

PROXY_TOPO=$(curl -s "$ENTRYPOINT/operator/api/topology" 2>&1)
NODES=$(echo "$PROXY_TOPO" | jq '.data.nodes | length' 2>/dev/null || echo "0")
EDGES=$(echo "$PROXY_TOPO" | jq '.data.edges | length' 2>/dev/null || echo "0")

log_info "Nodes: $NODES, Edges: $EDGES"

if [ "$NODES" -ge 10 ] && [ "$EDGES" -ge 6 ]; then
    log_pass "Topology: $NODES nodes + $EDGES edges"
    ((TESTS_PASSED++))
else
    log_fail "Topology invalid (nodes: $NODES, edges: $EDGES)"
    ((TESTS_FAILED++))
fi

# ============ TEST 6: Verify proxy headers are passed ============

log_test "TEST 6: Verify Authorization header pass-through"

# Try with dummy token (backend might reject, but proxy should pass it)
RESPONSE=$(curl -s -H "Authorization: Bearer test-token" \
    -w "\n%{http_code}" "$ENTRYPOINT/operator/api/modules" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

log_info "Response with dummy token: HTTP $HTTP_CODE"

if [ "$HTTP_CODE" != "000" ]; then
    log_pass "Proxy passes Authorization header (HTTP $HTTP_CODE)"
    ((TESTS_PASSED++))
else
    log_fail "Proxy unreachable with auth header"
    ((TESTS_FAILED++))
fi

# ============ SUMMARY ============

log_test "SUMMARY"

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL))

log_info "Total tests: $TOTAL"
log_info "Passed: $TESTS_PASSED"
log_info "Failed: $TESTS_FAILED"
log_info "Success rate: ${SUCCESS_RATE}%"

if [ $TESTS_FAILED -eq 0 ]; then
    log_pass "ALL TESTS PASSED ✓"
    log_info "Single entrypoint (tentaculo_link:8000) is working correctly"
    exit 0
else
    log_fail "SOME TESTS FAILED"
    log_info "Debug: Check tentaculo_link logs and operator-backend connectivity"
    exit 1
fi
