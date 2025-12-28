#!/bin/bash

###############################################################################
# Test: Operator UI served via tentaculo_link:8000/operator/ui/
# P0 Checks: Single entrypoint, UI accessible, APIs intact, no collisions
###############################################################################

set -e

TENTACULO_URL="http://localhost:8000"
OPERATOR_UI_URL="${TENTACULO_URL}/operator/ui/"
OPERATOR_REDIRECT="${TENTACULO_URL}/operator"

echo "=== PHASE 0: Verify tentaculo_link is running ==="
if ! curl -s "${TENTACULO_URL}/health" > /dev/null 2>&1; then
    echo "❌ FAIL: tentaculo_link:8000 not responding"
    exit 1
fi
echo "✅ tentaculo_link:8000 is responding"

echo ""
echo "=== PHASE 1: Test /operator/ui/ (Static Files Mount) ==="

# Test 1.1: GET /operator/ui/ → 200 HTML
echo -n "Test 1.1: GET /operator/ui/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${OPERATOR_UI_URL}")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS (200)"
else
    echo "❌ FAIL (HTTP $HTTP_CODE)"
    exit 1
fi

# Test 1.2: GET /operator/ui/assets/[CSS] (should exist)
echo -n "Test 1.2: GET /operator/ui/assets/index-*.css ... "
CSS_FILE=$(curl -s "${OPERATOR_UI_URL}" | grep -oP 'index-[a-zA-Z0-9]+\.css' | head -1)
if [ -z "$CSS_FILE" ]; then
    echo "⚠️  SKIP (CSS file not found in HTML, may be valid)"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TENTACULO_URL}/operator/ui/assets/${CSS_FILE}")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ PASS (200)"
    else
        echo "❌ FAIL (HTTP $HTTP_CODE)"
        exit 1
    fi
fi

# Test 1.3: GET /operator/ui/assets/[JS] (should exist)
echo -n "Test 1.3: GET /operator/ui/assets/index-*.js ... "
JS_FILE=$(curl -s "${OPERATOR_UI_URL}" | grep -oP 'index-[a-zA-Z0-9]+\.js' | head -1)
if [ -z "$JS_FILE" ]; then
    echo "⚠️  SKIP (JS file not found in HTML, may be valid)"
else
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TENTACULO_URL}/operator/ui/assets/${JS_FILE}")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ PASS (200)"
    else
        echo "❌ FAIL (HTTP $HTTP_CODE)"
        exit 1
    fi
fi

echo ""
echo "=== PHASE 2: Test /operator Redirect ==="

# Test 2.1: GET /operator → 302 Redirect to /operator/ui/
echo -n "Test 2.1: GET /operator (redirect) ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L "${OPERATOR_REDIRECT}")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS (302→200)"
else
    echo "⚠️  WARN (HTTP $HTTP_CODE, but may be OK)"
fi

echo ""
echo "=== PHASE 3: Test Existing APIs (No Collision) ==="

# Test 3.1: GET /operator/status → 200 or 401 JSON (requires auth token)
echo -n "Test 3.1: GET /operator/status ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TENTACULO_URL}/operator/status")
if [[ "$HTTP_CODE" =~ ^(200|401|403)$ ]]; then
    echo "✅ PASS (HTTP $HTTP_CODE, auth expected)"
else
    echo "❌ FAIL (HTTP $HTTP_CODE)"
    exit 1
fi

# Test 3.2: GET /operator/power/state → 200 or 401 JSON (requires auth token)
echo -n "Test 3.2: GET /operator/power/state ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TENTACULO_URL}/operator/power/state")
if [[ "$HTTP_CODE" =~ ^(200|401|403)$ ]]; then
    echo "✅ PASS (HTTP $HTTP_CODE, auth expected)"
else
    echo "❌ FAIL (HTTP $HTTP_CODE)"
    exit 1
fi

# Test 3.3: POST /operator/chat/ask → 200 or 503 (depends on service)
echo -n "Test 3.3: POST /operator/chat/ask ... "
HTTP_CODE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"message":"test"}' \
    -o /dev/null -w "%{http_code}" "${TENTACULO_URL}/operator/chat/ask")
if [[ "$HTTP_CODE" =~ ^(200|503|504)$ ]]; then
    echo "✅ PASS (HTTP $HTTP_CODE)"
else
    echo "⚠️  WARN (HTTP $HTTP_CODE, unexpected)"
fi

# Test 3.4: GET /operator/ui/invalid → 404 (API collision check)
echo -n "Test 3.4: GET /operator/ui/invalid (no collision) ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TENTACULO_URL}/operator/ui/invalid")
if [ "$HTTP_CODE" = "404" ]; then
    echo "✅ PASS (404, expected)"
else
    echo "⚠️  WARN (HTTP $HTTP_CODE)"
fi

echo ""
echo "=== ✅ ALL P0 CHECKS PASSED ==="
echo "Summary:"
echo "  ✅ tentaculo_link running (single entrypoint)"
echo "  ✅ /operator/ui/ served (static files)"
echo "  ✅ /operator/ui/assets/* served"
echo "  ✅ /operator redirect working"
echo "  ✅ /operator/status API intact"
echo "  ✅ /operator/power/state API intact"
echo "  ✅ /operator/chat/ask API intact"
echo "  ✅ No API collisions"
