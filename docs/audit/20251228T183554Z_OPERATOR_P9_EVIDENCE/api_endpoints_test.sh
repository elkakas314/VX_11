#!/bin/bash

echo "=== Testing P0 API Endpoints ===" >> /tmp/api_test_results.txt
echo "" >> /tmp/api_test_results.txt

# Status endpoint
echo "[1/6] Testing /operator/api/status" >> /tmp/api_test_results.txt
curl -s -w "\nHTTP Status: %{http_code}\n" -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/status | jq .policy >> /tmp/api_test_results.txt 2>&1
echo "" >> /tmp/api_test_results.txt

# Modules endpoint
echo "[2/6] Testing /operator/api/modules" >> /tmp/api_test_results.txt
curl -s -w "\nHTTP Status: %{http_code}\n" -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/modules | jq ".modules | length" >> /tmp/api_test_results.txt 2>&1
echo "" >> /tmp/api_test_results.txt

# Chat endpoint
echo "[3/6] Testing /operator/api/chat" >> /tmp/api_test_results.txt
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST -H "x-vx11-token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}' \
  http://localhost:8000/operator/api/chat | jq .route_taken >> /tmp/api_test_results.txt 2>&1
echo "" >> /tmp/api_test_results.txt

# Events endpoint
echo "[4/6] Testing /operator/api/events" >> /tmp/api_test_results.txt
curl -s -w "\nHTTP Status: %{http_code}\n" -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/events | jq .total >> /tmp/api_test_results.txt 2>&1
echo "" >> /tmp/api_test_results.txt

# Scorecard endpoint
echo "[5/6] Testing /operator/api/scorecard" >> /tmp/api_test_results.txt
curl -s -w "\nHTTP Status: %{http_code}\n" -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/scorecard | jq .files_found >> /tmp/api_test_results.txt 2>&1
echo "" >> /tmp/api_test_results.txt

# Topology endpoint
echo "[6/6] Testing /operator/api/topology" >> /tmp/api_test_results.txt
curl -s -w "\nHTTP Status: %{http_code}\n" -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/topology | jq .policy >> /tmp/api_test_results.txt 2>&1
echo "" >> /tmp/api_test_results.txt

cat /tmp/api_test_results.txt
