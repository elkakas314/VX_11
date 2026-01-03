#!/bin/bash
# Smoke test SSE - Simple validation
# Verify: 1) 200 status, 2) text/event-stream content, 3) No auth errors

BASE_URL="${1:-http://localhost:8000}"
TOKEN="${2:-vx11-test-token}"

echo "🔍 SSE Stream Test"
echo "   URL: $BASE_URL/operator/api/events/stream"
echo

# Combined test: single request with timeout to check status and early content
OUTPUT=$(timeout 2 curl -v "$BASE_URL/operator/api/events/stream?token=$TOKEN" 2>&1 || true)

# Test 1: Check HTTP 200
if echo "$OUTPUT" | grep -q "< HTTP/1.1 200"; then
    echo "✅ Test 1: HTTP 200"
elif echo "$OUTPUT" | grep -q "< HTTP/1.1 401"; then
    echo "❌ Test 1: HTTP 401 Unauthorized"
    exit 1
elif echo "$OUTPUT" | grep -q "< HTTP/1.1 403"; then
    echo "❌ Test 1: HTTP 403 Forbidden"
    exit 1
else
    echo "❌ Test 1: Unexpected response"
    echo "$OUTPUT" | grep "HTTP/1.1" || echo "(no HTTP response)"
    exit 1
fi

# Test 2: Check Content-Type header
if echo "$OUTPUT" | grep -iq "< content-type.*text/event-stream"; then
    echo "✅ Test 2: Content-Type: text/event-stream"
else
    echo "❌ Test 2: Content-Type not text/event-stream"
    echo "$OUTPUT" | grep -i "content-type" || echo "   (content-type header not found)"
    exit 1
fi

# Test 3: Verify no immediate auth/error in response
BODY=$(echo "$OUTPUT" | tail -20)
if echo "$BODY" | grep -iq "unauthorized\|forbidden\|auth"; then
    echo "❌ Test 3: Auth error in response"
    exit 1
else
    echo "✅ Test 3: No auth errors"
fi

echo
echo "============================================================"
echo "✅ SSE STREAM TEST PASSED"
echo "============================================================"
exit 0
