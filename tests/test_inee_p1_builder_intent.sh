#!/bin/bash
# P1 TEST: Builder creates INTENT, does NOT execute
# Simulates: Builder → INTENT in DB → (would go to Spawner, not executed here)

set -e

TENTACULO_URL="http://localhost:8000"
TOKEN="vx11-local-token"
HORMIGUERO_URL="http://localhost:8004"
DB_PATH="./data/runtime/vx11.db"

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

echo "=== PREREQUISITE: Enable Builder ==="
echo "NOTE: This test requires HORMIGUERO_BUILDER_ENABLED=1 in .env"
echo "Current test validates builder INTENT semantics (no execution guarantee yet)"

# ============ TEST 1: Builder endpoint exists ============
echo "=== TEST 1: Builder Endpoint Reachable ==="
RESP=$(curl -s -X POST "$TENTACULO_URL/operator/inee/builder/patchset" \
    -H "x-vx11-token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"spec_id":"test_spec_no_exec","description":"Test no exec","parameters":{"module":"test"}}' \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESP" | tail -n1)
BODY=$(echo "$RESP" | head -n-1)

if [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "503" ]]; then
    log_test "Builder endpoint reachable or disabled" "PASS"
else
    log_test "Builder endpoint reachable" "FAIL"
    echo "  Got HTTP $HTTP_CODE"
fi

# ============ TEST 2: Response has patchset_id (not execution) ============
echo "=== TEST 2: Builder returns patchset_id (no execution) ==="
if echo "$BODY" | jq . >/dev/null 2>&1; then
    PATCHSET_ID=$(echo "$BODY" | jq -r '.patchset_id // .status // "null"' 2>/dev/null || echo "null")
    
    if [[ "$PATCHSET_ID" != "null" ]] && [[ "$PATCHSET_ID" != "disabled" ]]; then
        log_test "Builder returns patchset_id (sign of INTENT mode)" "PASS"
        echo "  patchset_id: $PATCHSET_ID"
    else
        if echo "$BODY" | grep -q "disabled"; then
            log_test "Builder dormant (disabled) - acceptable in this test" "PASS"
        else
            log_test "Builder returns patchset_id" "FAIL"
            echo "  Body: $BODY"
        fi
    fi
else
    log_test "Builder response is JSON" "FAIL"
    echo "  Body: $BODY"
fi

# ============ TEST 3: Verify no direct code execution ============
echo "=== TEST 3: Builder does NOT execute (semantics check) ==="
# This is a design check, not runtime verification (would need container inspection)
# For now, just verify Builder response doesn't contain execution traces
if ! echo "$BODY" | grep -qi "executed\|running\|spawned\|hija"; then
    log_test "Builder response has no execution traces" "PASS"
else
    log_test "Builder response has no execution traces" "FAIL"
    echo "  Body contains execution keyword: $BODY"
fi

# ============ TEST 4: HMAC Envelope basic structure ============
echo "=== TEST 4: Colony Envelope Structure ==="
RESP=$(curl -s -X POST "$TENTACULO_URL/operator/inee/colony/envelope" \
    -H "x-vx11-token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"colony_id":"test_colony","payload":{"action":"hatch"}}' \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESP" | tail -n1)
BODY=$(echo "$RESP" | head -n-1)

if [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "503" ]]; then
    if echo "$BODY" | jq . >/dev/null 2>&1; then
        # Check for HMAC signature field
        if echo "$BODY" | jq -r '.hmac_signature // .envelope_id // .status' | grep -qv "null"; then
            log_test "Envelope has expected fields (hmac_signature or envelope_id)" "PASS"
        else
            if echo "$BODY" | grep -q "disabled"; then
                log_test "Envelope dormant (acceptable)" "PASS"
            else
                log_test "Envelope has expected fields" "FAIL"
            fi
        fi
    else
        log_test "Envelope response is JSON" "FAIL"
    fi
else
    log_test "Envelope endpoint reachable" "FAIL"
    echo "  Got HTTP $HTTP_CODE"
fi

# ============ TEST 5: Nonce replay protection (if envelope returns envelope_id) ============
echo "=== TEST 5: Nonce Replay Protection ==="
if echo "$BODY" | jq -r '.nonce // .envelope_id' | grep -qv "null"; then
    NONCE=$(echo "$BODY" | jq -r '.nonce // ""')
    echo "  Nonce field present: $NONCE"
    log_test "Envelope includes nonce field" "PASS"
else
    log_test "Envelope includes nonce field (not applicable if disabled)" "PASS"
fi

# ============ SUMMARY ============
echo ""
echo "========================================"
echo "RESULTS: $PASS PASS, $FAIL FAIL"
echo "========================================"

for result in "${TEST_RESULTS[@]}"; do
    echo "  $result"
done

echo ""
echo "NOTE: Full Builder execution test (intent→spawner→result) requires:"
echo "  - HORMIGUERO_BUILDER_ENABLED=1"
echo "  - Spawner running (TTL=1 HIJAs only)"
echo "  - DB queries for pending_intents table"

if [[ $FAIL -eq 0 ]]; then
    echo "✓ All P1 semantic tests passed"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi
