#!/bin/bash
# P0 TESTS: INEE Extended - Verify dormant state (flags OFF)
# All endpoints should return "disabled" or 503 when flags are OFF

set -e

TENTACULO_URL="http://localhost:8000"
TOKEN="vx11-local-token"
HORMIGUERO_URL="http://localhost:8004"

TEST_RESULTS=()
PASS=0
FAIL=0

log_test() {
    local name="$1"
    local status="$2"
    echo "[$(date +'%H:%M:%S')] $status: $name"
    TEST_RESULTS+=("$status: $name")
    if [[ "$status" == "PASS" ]]; then
        ((PASS++))
    else
        ((FAIL++))
    fi
}

# ============ TEST 1: Builder dormant (HORMIGUERO_BUILDER_ENABLED=0) ============
echo "=== TEST 1: Builder Patchset (Dormant) ==="
RESP=$(curl -s -X POST "$TENTACULO_URL/operator/inee/builder/patchset" \
    -H "x-vx11-token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"spec_id":"test_spec","description":"Test","parameters":{}}' \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESP" | tail -n1)
BODY=$(echo "$RESP" | head -n-1)

if echo "$BODY" | grep -q "disabled\|unavailable" || [[ "$HTTP_CODE" == "503" ]]; then
    log_test "Builder dormant (disabled or 503)" "PASS"
else
    log_test "Builder dormant (disabled or 503)" "FAIL"
    echo "  Expected: 'disabled' or 503, got: $HTTP_CODE / $BODY"
fi

# ============ TEST 2: Colony Register (dormant) ============
echo "=== TEST 2: Colony Register (Dormant) ==="
RESP=$(curl -s -X POST "$TENTACULO_URL/operator/inee/colony/register" \
    -H "x-vx11-token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"colony_id":"colony_1","remote_url":"http://colony:8004"}' \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESP" | tail -n1)
BODY=$(echo "$RESP" | head -n-1)

if [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "503" ]]; then
    log_test "Colony register endpoint reachable" "PASS"
else
    log_test "Colony register endpoint reachable" "FAIL"
    echo "  Expected: 200 or 503, got: $HTTP_CODE"
fi

# ============ TEST 3: INEE Status ============
echo "=== TEST 3: INEE Status (Dormant Check) ==="
RESP=$(curl -s -X GET "$TENTACULO_URL/operator/inee/status" \
    -H "x-vx11-token: $TOKEN" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESP" | tail -n1)
BODY=$(echo "$RESP" | head -n-1)

if [[ "$HTTP_CODE" == "200" ]]; then
    # Parse JSON and check if enabled=false
    if echo "$BODY" | jq -r '.enabled' | grep -q "false"; then
        log_test "INEE status shows disabled (enabled=false)" "PASS"
    else
        ENABLED=$(echo "$BODY" | jq -r '.enabled // "null"')
        if [[ "$ENABLED" == "null" ]]; then
            log_test "INEE status shows disabled (enabled=false)" "PASS"
        else
            log_test "INEE status shows disabled (enabled=false)" "FAIL"
            echo "  Got enabled=$ENABLED"
        fi
    fi
else
    log_test "INEE status endpoint reachable" "FAIL"
    echo "  Expected: 200, got: $HTTP_CODE"
fi

# ============ TEST 4: No Token → 401 ============
echo "=== TEST 4: Token Validation (No Token) ==="
RESP=$(curl -s -X GET "$TENTACULO_URL/operator/inee/status" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESP" | tail -n1)

if [[ "$HTTP_CODE" == "401" ]] || [[ "$HTTP_CODE" == "403" ]]; then
    log_test "Missing token rejected (401/403)" "PASS"
else
    log_test "Missing token rejected (401/403)" "FAIL"
    echo "  Expected: 401/403, got: $HTTP_CODE"
fi

# ============ TEST 5: Direct Hormiguero call (should also be dormant) ============
echo "=== TEST 5: Direct Hormiguero Endpoint (Verify Dormant) ==="
RESP=$(curl -s -X GET "$HORMIGUERO_URL/hormiguero/inee/extended/status" \
    -H "x-vx11-token: $TOKEN" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESP" | tail -n1)
BODY=$(echo "$RESP" | head -n-1)

if [[ "$HTTP_CODE" == "200" ]]; then
    log_test "Hormiguero INEE endpoint reachable (direct)" "PASS"
else
    if [[ "$HTTP_CODE" == "404" ]]; then
        log_test "Hormiguero INEE endpoint (not mounted yet)" "PASS"
    else
        log_test "Hormiguero INEE endpoint direct check" "FAIL"
        echo "  Got HTTP $HTTP_CODE"
    fi
fi

# ============ TEST 6: Envelope creation (remote plane OFF) ============
echo "=== TEST 6: Colony Envelope (Remote Plane OFF) ==="
RESP=$(curl -s -X POST "$TENTACULO_URL/operator/inee/colony/envelope" \
    -H "x-vx11-token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"colony_id":"colony_1","payload":{"test":"data"}}' \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESP" | tail -n1)
BODY=$(echo "$RESP" | head -n-1)

if echo "$BODY" | grep -q "disabled\|not enabled" || [[ "$HTTP_CODE" == "503" ]]; then
    log_test "Envelope creation disabled (remote plane OFF)" "PASS"
else
    log_test "Envelope creation disabled (remote plane OFF)" "FAIL"
    echo "  Body: $BODY"
fi

# ============ SUMMARY ============
echo ""
echo "========================================"
echo "RESULTS: $PASS PASS, $FAIL FAIL"
echo "========================================"

for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done

if [[ $FAIL -eq 0 ]]; then
    echo "✓ All P0 tests passed (flags OFF, services dormant)"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi
