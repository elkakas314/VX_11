#!/bin/bash

# VX11 CORE MVP Test Script
# Verifica 6 endpoints críticos via :8000 single entrypoint
# Token: vx11-test-token (extraído de docker-compose.full-test.yml)

set -e

TOKEN="vx11-test-token"
HOST="http://localhost:8000"
RESULTS_FILE="core_mvp_test_results.log"

echo "=== VX11 CORE MVP Test Suite ===" | tee -a "$RESULTS_FILE"
echo "Host: $HOST" | tee -a "$RESULTS_FILE"
echo "Token: $TOKEN" | tee -a "$RESULTS_FILE"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# CURL 1: GET /health (no token required)
echo "--- CURL 1: GET /health ---" | tee -a "$RESULTS_FILE"
curl -s -X GET \
  "$HOST/health" \
  -H "Accept: application/json" | jq . | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# CURL 2: GET /vx11/status (token required)
echo "--- CURL 2: GET /vx11/status ---" | tee -a "$RESULTS_FILE"
curl -s -X GET \
  "$HOST/vx11/status" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Accept: application/json" | jq . | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# CURL 3: POST /vx11/intent (require.switch=false, should execute)
echo "--- CURL 3: POST /vx11/intent (require.switch=false) ---" | tee -a "$RESULTS_FILE"
INTENT_3_RESPONSE=$(curl -s -X POST \
  "$HOST/vx11/intent" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "intent_type": "chat",
    "text": "Analizar el estado del core",
    "require": {"switch": false, "spawner": false},
    "priority": "P0"
  }')
echo "$INTENT_3_RESPONSE" | jq . | tee -a "$RESULTS_FILE"
CORR_ID_3=$(echo "$INTENT_3_RESPONSE" | jq -r '.correlation_id' 2>/dev/null || echo "unknown")
echo "correlation_id: $CORR_ID_3" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# CURL 4: POST /vx11/intent (require.switch=true, should OFF_BY_POLICY)
echo "--- CURL 4: POST /vx11/intent (require.switch=true) ---" | tee -a "$RESULTS_FILE"
INTENT_4_RESPONSE=$(curl -s -X POST \
  "$HOST/vx11/intent" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "intent_type": "exec",
    "text": "Ejecutar via switch",
    "require": {"switch": true, "spawner": false},
    "priority": "P1"
  }')
echo "$INTENT_4_RESPONSE" | jq . | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# CURL 5: POST /vx11/intent (require.spawner=true, should QUEUED)
echo "--- CURL 5: POST /vx11/intent (require.spawner=true) ---" | tee -a "$RESULTS_FILE"
INTENT_5_RESPONSE=$(curl -s -X POST \
  "$HOST/vx11/intent" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "intent_type": "spawn",
    "text": "Spawn a new task",
    "require": {"switch": false, "spawner": true},
    "priority": "P1",
    "payload": {"task_name": "test_spawn", "duration": 60}
  }')
echo "$INTENT_5_RESPONSE" | jq . | tee -a "$RESULTS_FILE"
CORR_ID_5=$(echo "$INTENT_5_RESPONSE" | jq -r '.correlation_id' 2>/dev/null || echo "unknown")
echo "correlation_id: $CORR_ID_5" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# CURL 6: GET /vx11/result/{correlation_id} (from CURL 5)
echo "--- CURL 6: GET /vx11/result/$CORR_ID_5 ---" | tee -a "$RESULTS_FILE"
curl -s -X GET \
  "$HOST/vx11/result/$CORR_ID_5" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Accept: application/json" | jq . | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

echo "=== Test Suite Complete ===" | tee -a "$RESULTS_FILE"
echo "Results logged to: $RESULTS_FILE" | tee -a "$RESULTS_FILE"
