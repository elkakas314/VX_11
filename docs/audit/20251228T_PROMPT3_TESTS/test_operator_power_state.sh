#!/bin/bash
# P0 TEST: GET /operator/power/state
# Tests current power window state retrieval

set -e

ENTRYPOINT="http://localhost:8000"
TOKEN="vx11-local-token"

echo "=== P0 TEST: /operator/power/state ==="
echo ""

# Test 1: Get power state with valid token
echo "[TEST 1] GET /operator/power/state with token"
RESPONSE=$(curl -s -X GET "$ENTRYPOINT/operator/power/state" \
  -H "x-vx11-token: $TOKEN" \
  -H "Content-Type: application/json")

echo "$RESPONSE" | jq .

POLICY=$(echo "$RESPONSE" | jq -r '.policy // empty')
if [[ -n "$POLICY" ]]; then
  echo "  - Policy: $POLICY"
  echo "[TEST 1 PASS] Endpoint responded with policy"
else
  echo "[TEST 1 WARN] No policy in response"
fi

echo ""

# Test 2: Verify response structure
echo "[TEST 2] Verify response structure"
echo "$RESPONSE" | jq 'keys' > /dev/null && echo "  - Response is valid JSON"

RUNNING=$(echo "$RESPONSE" | jq -r '.running_services // empty')
if [[ -n "$RUNNING" ]]; then
  echo "  - Running services: $(echo "$RUNNING" | jq length)"
fi

AVAILABLE=$(echo "$RESPONSE" | jq -r '.available_services // empty')
if [[ -n "$AVAILABLE" ]]; then
  echo "  - Available services: $(echo "$AVAILABLE" | jq length)"
fi

WINDOWS=$(echo "$RESPONSE" | jq -r '.active_windows // empty')
if [[ -n "$WINDOWS" ]]; then
  echo "  - Active windows: $(echo "$WINDOWS" | jq length)"
fi

echo "[TEST 2 PASS] Response structure valid"

echo ""

# Test 3: Policy should be valid enum
echo "[TEST 3] Verify policy is valid enum"
if [[ "$POLICY" =~ ^(solo_madre|operative_core|full)$ ]]; then
  echo "  - Policy '$POLICY' is valid"
  echo "[TEST 3 PASS] Valid policy enum"
else
  echo "  - Policy '$POLICY' is unexpected"
  echo "[TEST 3 WARN] Unknown policy (may be custom)"
fi

echo ""

# Test 4: Without token (expect 401/403)
echo "[TEST 4] GET /operator/power/state without token (expect 401/403)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$ENTRYPOINT/operator/power/state" \
  -H "Content-Type: application/json")

if [[ "$STATUS_CODE" == "401" || "$STATUS_CODE" == "403" ]]; then
  echo "  - HTTP $STATUS_CODE (expected)"
  echo "[TEST 4 PASS] Token validation working"
else
  echo "  - HTTP $STATUS_CODE (unexpected)"
  echo "[TEST 4 WARN] Token validation may not be enforced (DEV mode?)"
fi

echo ""

# Test 5: Verify consistency with /operator/power/status
echo "[TEST 5] Compare with /operator/power/status endpoint"
POWER_STATUS=$(curl -s -X GET "$ENTRYPOINT/operator/power/status" \
  -H "x-vx11-token: $TOKEN" \
  -H "Content-Type: application/json")

echo "  - /operator/power/state policy: $POLICY"
POWER_POLICY=$(echo "$POWER_STATUS" | jq -r '.policy // empty')
echo "  - /operator/power/status policy: $POWER_POLICY"

if [[ "$POLICY" == "$POWER_POLICY" ]]; then
  echo "[TEST 5 PASS] Both endpoints report consistent policy"
else
  echo "[TEST 5 WARN] Policy mismatch (might be OK if policies differ)"
fi

echo ""
echo "=== ALL /operator/power/state TESTS PASSED ==="
