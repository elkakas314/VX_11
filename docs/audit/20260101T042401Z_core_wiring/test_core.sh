#!/bin/bash
# VX11 CORE WIRING TEST — 6 curls REPRODUCIBLES
# En test mode, el token es vx11-test-token (definido en docker-compose.full-test.yml)

set -e

TOKEN="vx11-test-token"
BASE_URL="http://localhost:8000"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

echo "=== VX11 Core Wiring Tests [${TIMESTAMP}] ==="
echo ""

# CURL 1: /health (sin auth)
echo "CURL 1: GET /health (sin auth)"
curl -s -w "\nHTTP %{http_code}\n" "${BASE_URL}/health"
echo ""
echo "---"
echo ""

# CURL 2: /vx11/status (con auth)
echo "CURL 2: GET /vx11/status (con auth)"
curl -s -w "\nHTTP %{http_code}\n" \
  -H "X-VX11-Token: ${TOKEN}" \
  "${BASE_URL}/vx11/status" | head -50
echo ""
echo "---"
echo ""

# CURL 3: /operator/chat SIN ventana abierta (debe responder OFF_BY_POLICY o Switch funciona)
echo "CURL 3: POST /operator/chat (sin ventana - SOLO_MADRE por defecto)"
curl -s -w "\nHTTP %{http_code}\n" \
  -H "X-VX11-Token: ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test operativo sin ventana"}' \
  "${BASE_URL}/operator/chat"
echo ""
echo "---"
echo ""

# CURL 4: /operator/power/policy/solo_madre/status (chequear policy actual)
echo "CURL 4: GET /operator/power/policy/solo_madre/status"
curl -s -w "\nHTTP %{http_code}\n" \
  -H "X-VX11-Token: ${TOKEN}" \
  "${BASE_URL}/operator/power/policy/solo_madre/status"
echo ""
echo "---"
echo ""

# CURL 5: Intenta abrir ventana temporal para Switch (si es posible)
echo "CURL 5: POST /operator/power/window/open (abre ventana 300s para switch)"
WINDOW_RESP=$(curl -s -w "\nHTTP %{http_code}\n" \
  -H "X-VX11-Token: ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"services": ["switch"], "ttl_sec": 300, "reason": "test_core_wiring"}' \
  "${BASE_URL}/operator/power/window/open" 2>/dev/null || echo "{}")
echo "$WINDOW_RESP"
echo ""

# Extrae window_id si es válido
WINDOW_ID=$(echo "$WINDOW_RESP" | grep -o '"window_id":"[^"]*' | cut -d'"' -f4 || true)
if [ -n "$WINDOW_ID" ]; then
  echo "✓ Ventana abierta: $WINDOW_ID"
  echo ""
  echo "---"
  echo ""
  
  # CURL 6: /operator/chat CON ventana abierta (debe llamar a Switch y responder 200)
  echo "CURL 6: POST /operator/chat (CON ventana abierta - debe llamar a Switch)"
  curl -s -w "\nHTTP %{http_code}\n" \
    -H "X-VX11-Token: ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"message": "Ahora con ventana: dame un análisis del core wiring"}' \
    "${BASE_URL}/operator/chat" | head -80
  echo ""
  echo "---"
  echo ""

  # CURL 7 (bonus): Cierra ventana
  echo "CURL 7: POST /operator/power/window/close (cierra ventana)"
  curl -s -w "\nHTTP %{http_code}\n" \
    -H "X-VX11-Token: ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"window_id\": \"${WINDOW_ID}\"}" \
    "${BASE_URL}/operator/power/window/close"
  echo ""
  echo "---"
  echo ""

  # CURL 8: /operator/chat SIN ventana (debe volver a OFF_BY_POLICY)
  echo "CURL 8: POST /operator/chat (ventana cerrada - debe responder OFF_BY_POLICY)"
  curl -s -w "\nHTTP %{http_code}\n" \
    -H "X-VX11-Token: ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"message": "Ya debería estar cerrado"}' \
    "${BASE_URL}/operator/chat"
  echo ""
else
  echo "⚠ No se pudo abrir ventana (endpoint puede no estar disponible)"
  echo "Saltando CURLs 6-8"
fi

echo ""
echo "=== TEST COMPLETE ==="
