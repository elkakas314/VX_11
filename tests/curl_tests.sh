#!/bin/bash
# tests/curl_tests.sh - End-to-end curl validation tests
# Run this to validate all major endpoints work correctly

set -e

BASE_URL="${VX11_BASE_URL:-http://localhost:8000}"
TOKEN="${VX11_TOKEN:-test-token-valid}"
RESULTS="docs/audit/$(date +%Y%m%dT%H%M%SZ)_CURL_RESULTS.txt"

mkdir -p "$(dirname "$RESULTS")"

echo "=== VX11 Core MVP E2E Curl Tests ===" | tee "$RESULTS"
echo "Base URL: $BASE_URL" | tee -a "$RESULTS"
echo "Timestamp: $(date)" | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

# Test 1: GET /vx11/status (no auth required for this test)
echo "TEST 1: GET /vx11/status" | tee -a "$RESULTS"
curl -s -w "\nStatus: %{http_code}\n" "$BASE_URL/vx11/status" | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

# Test 2: POST /vx11/window/open spawner
echo "TEST 2: POST /vx11/window/open (spawner)" | tee -a "$RESULTS"
curl -s -w "\nStatus: %{http_code}\n" \
  -X POST "$BASE_URL/vx11/window/open" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target":"spawner","ttl_seconds":300}' | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

# Test 3: GET /vx11/window/status/spawner
echo "TEST 3: GET /vx11/window/status/spawner" | tee -a "$RESULTS"
curl -s -w "\nStatus: %{http_code}\n" \
  "$BASE_URL/vx11/window/status/spawner" \
  -H "X-VX11-Token: $TOKEN" | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

# Test 4: POST /vx11/intent (no window required)
echo "TEST 4: POST /vx11/intent (basic, no window required)" | tee -a "$RESULTS"
curl -s -w "\nStatus: %{http_code}\n" \
  -X POST "$BASE_URL/vx11/intent" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"intent_type":"chat","text":"system status check"}' | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

# Test 5: POST /vx11/spawn (with window open)
echo "TEST 5: POST /vx11/spawn (spawner window open)" | tee -a "$RESULTS"
curl -s -w "\nStatus: %{http_code}\n" \
  -X POST "$BASE_URL/vx11/spawn" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_type":"python","code":"print(\"hello\")","ttl_seconds":60}' | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

# Test 6: POST /vx11/window/close spawner
echo "TEST 6: POST /vx11/window/close (spawner)" | tee -a "$RESULTS"
curl -s -w "\nStatus: %{http_code}\n" \
  -X POST "$BASE_URL/vx11/window/close" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target":"spawner","reason":"test complete"}' | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

# Test 7: GET /metrics
echo "TEST 7: GET /metrics (prometheus format)" | tee -a "$RESULTS"
curl -s -w "\nStatus: %{http_code}\n" \
  "$BASE_URL/metrics" \
  -H "X-VX11-Token: $TOKEN" | head -20 | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

# Test 8: POST /madre/callback/spawn (webhook from spawner)
echo "TEST 8: POST /madre/callback/spawn (simulated webhook)" | tee -a "$RESULTS"
curl -s -w "\nStatus: %{http_code}\n" \
  -X POST "http://localhost:8001/madre/callback/spawn" \
  -H "X-VX11-Token: test-madre-token" \
  -H "Content-Type: application/json" \
  -d '{
    "spawn_id":"spawn-test-001",
    "correlation_id":"corr-test-001",
    "status":"DONE",
    "result":{"output":"test result"},
    "error":null
  }' | tee -a "$RESULTS"
echo "" | tee -a "$RESULTS"

echo "=== Tests Complete ===" | tee -a "$RESULTS"
echo "Results saved to: $RESULTS"
