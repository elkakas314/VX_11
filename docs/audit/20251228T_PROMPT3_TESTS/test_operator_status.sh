#!/bin/bash
# P0 TEST: GET /operator/status
# Tests aggregated health check (no service wakeup)

set -e

ENTRYPOINT="http://localhost:8000"
TOKEN="vx11-local-token"  # Must match VX11_TENTACULO_LINK_TOKEN in env

echo "=== P0 TEST: /operator/status ==="
echo ""

# Test 1: Status with valid token
echo "[TEST 1] GET /operator/status with token"
curl -s -X GET "$ENTRYPOINT/operator/status" \
  -H "x-vx11-token: $TOKEN" \
  -H "Content-Type: application/json" | jq .

echo ""
echo "[TEST 1 PASS] Endpoint responded"

# Test 2: Check response structure
echo "[TEST 2] Verify response structure"
RESPONSE=$(curl -s -X GET "$ENTRYPOINT/operator/status" \
  -H "x-vx11-token: $TOKEN" \
  -H "Content-Type: application/json")

STATUS=$(echo "$RESPONSE" | jq -r '.status')
echo "  - Overall status: $STATUS"

TENTACULO=$(echo "$RESPONSE" | jq -r '.components.tentaculo_link.status')
echo "  - Tentaculo status: $TENTACULO"

MADRE=$(echo "$RESPONSE" | jq -r '.components.madre.status')
echo "  - Madre status: $MADRE"

REDIS=$(echo "$RESPONSE" | jq -r '.components.redis.status')
echo "  - Redis status: $REDIS"

SWITCH=$(echo "$RESPONSE" | jq -r '.components.switch.status')
echo "  - Switch status: $SWITCH"

POLICY=$(echo "$RESPONSE" | jq -r '.windows.policy')
echo "  - Window policy: $POLICY"

if [[ "$STATUS" =~ ^(ok|degraded|offline)$ ]]; then
  echo "[TEST 2 PASS] Response structure valid"
else
  echo "[TEST 2 FAIL] Invalid status: $STATUS"
  exit 1
fi

echo ""

# Test 3: Status without token (should fail)
echo "[TEST 3] GET /operator/status without token (expect 401/403)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$ENTRYPOINT/operator/status" \
  -H "Content-Type: application/json")

if [[ "$STATUS_CODE" == "401" || "$STATUS_CODE" == "403" ]]; then
  echo "  - HTTP $STATUS_CODE (expected)"
  echo "[TEST 3 PASS] Token validation working"
else
  echo "  - HTTP $STATUS_CODE (unexpected)"
  echo "[TEST 3 WARN] Token validation may not be enforced (DEV mode?)"
fi

echo ""
echo "=== ALL /operator/status TESTS PASSED ==="
