#!/bin/bash

echo "=== VENTANA CONTROLADA: HERMES API & AUTH (FRONT-DOOR) ===" 
echo ""

# ============================================================================
# LOAD VX11_TOKEN (ROBUST)
# ============================================================================

TOKEN=""

# Prioridad 1: ENV variable
if [ -n "${VX11_TOKEN:-}" ]; then
    TOKEN="$VX11_TOKEN"
    echo "[TOKEN] Using VX11_TOKEN from environment"
fi

# Prioridad 2: token files (sin imprimir valores)
if [ -z "$TOKEN" ]; then
    for token_path in "/etc/vx11/tokens.env" "./tokens.env" "./.env" "./config/tokens.env"; do
        if [ -f "$token_path" ]; then
            TOKEN_FOUND=$(grep -E '^VX11_TOKEN=' "$token_path" | tail -1 | cut -d= -f2- | tr -d '\r' || true)
            if [ -n "$TOKEN_FOUND" ]; then
                TOKEN="$TOKEN_FOUND"
                echo "[TOKEN] Using VX11_TOKEN from $token_path"
                break
            fi
        fi
    done
fi

# Fallback: default local token (but warn if no proper token found)
if [ -z "$TOKEN" ]; then
    echo "[WARN] VX11_TOKEN not found in ENV or files"
    echo "[WARN] Using fallback: vx11-local-token"
    TOKEN="vx11-local-token"
fi

PASS=0
FAIL=0

# ============================================================================
# TEST HELPER: HTTP status assertion
# ============================================================================

test_http() {
    local test_name="$1"
    local method="$2"
    local url="$3"
    local body="$4"
    local with_token="$5"
    local expected_status="$6"
    local tmpfile="/tmp/test_${RANDOM}.txt"

    echo ""
    echo "[TEST] $test_name"
    echo "       Esperado: HTTP $expected_status"

    # Build curl command arguments array
    local curl_args=(-sS -o "$tmpfile" -w '%{http_code}' -X "$method" -H 'Content-Type: application/json')
    
    if [ "$with_token" = "yes" ]; then
        curl_args+=(-H "X-VX11-Token: $TOKEN")
    fi
    
    curl_args+=(-d "$body" "$url")

    # Execute curl and capture status code
    local http_code
    http_code=$(curl "${curl_args[@]}")
    local response_body=""
    
    if [ -f "$tmpfile" ]; then
        response_body=$(cat "$tmpfile")
        rm -f "$tmpfile"
    fi

    echo "       Recibido: HTTP $http_code"
    if [ "$http_code" = "$expected_status" ]; then
        echo "       ✓ PASS"
        ((PASS++))
    else
        echo "       ✗ FAIL"
        if [ -n "$response_body" ]; then
            echo "       Response: $(echo "$response_body" | head -c 100)..."
        fi
        ((FAIL++))
    fi
}

# ============================================================================
# TESTS (FRONT-DOOR ONLY: localhost:8000)
# ============================================================================

echo ""
echo "========== SUITE: 8 TESTS VIA FRONT-DOOR (8000) =========="

# TEST 1: POST /hermes/get-engine CON token → 200
test_http \
    "POST /hermes/get-engine + token" \
    "POST" \
    "http://localhost:8000/hermes/get-engine" \
    '{"engine_id":"gpt4"}' \
    "yes" \
    "200"

# TEST 2: POST /hermes/get-engine SIN token → 401
test_http \
    "POST /hermes/get-engine - token" \
    "POST" \
    "http://localhost:8000/hermes/get-engine" \
    '{"engine_id":"gpt4"}' \
    "no" \
    "401"

# TEST 3: POST /hermes/get-engine sin engine_id → 422
test_http \
    "POST /hermes/get-engine sin engine_id" \
    "POST" \
    "http://localhost:8000/hermes/get-engine" \
    '{}' \
    "yes" \
    "422"

# TEST 4: POST /hermes/execute CON token → 200
test_http \
    "POST /hermes/execute + token" \
    "POST" \
    "http://localhost:8000/hermes/execute" \
    '{"command":"test"}' \
    "yes" \
    "200"

# TEST 5: POST /hermes/execute SIN token → 401
test_http \
    "POST /hermes/execute - token" \
    "POST" \
    "http://localhost:8000/hermes/execute" \
    '{"command":"test"}' \
    "no" \
    "401"

# TEST 6: Health checks (tentaculo_link must be OK)
echo ""
echo "[TEST] GET /health (tentaculo_link)"
tmpfile="/tmp/health_${RANDOM}.txt"
http_code=$(curl -sS -o "$tmpfile" -w "%{http_code}" http://localhost:8000/health)
health_status=$(cat "$tmpfile" | jq -r '.status' 2>/dev/null || echo "ERROR")
rm -f "$tmpfile"
if [ "$http_code" = "200" ] && [ "$health_status" = "ok" ]; then
    echo "       ✓ PASS (HTTP 200, status=ok)"
    ((PASS++))
else
    echo "       ✗ FAIL (HTTP $http_code, status=$health_status)"
    ((FAIL++))
fi

# TEST 7: OpenAPI spec (must exist and be valid JSON)
echo ""
echo "[TEST] GET /openapi.json"
tmpfile="/tmp/openapi_${RANDOM}.txt"
http_code=$(curl -sS -o "$tmpfile" -w "%{http_code}" http://localhost:8000/openapi.json)
path_count=$(cat "$tmpfile" | jq '.paths | keys | length' 2>/dev/null || echo "0")
rm -f "$tmpfile"
if [ "$http_code" = "200" ] && [ "$path_count" -gt "0" ]; then
    echo "       ✓ PASS (HTTP 200, $path_count paths)"
    ((PASS++))
else
    echo "       ✗ FAIL (HTTP $http_code, paths=$path_count)"
    ((FAIL++))
fi

# TEST 8: Logs check (no unexpected errors in recent logs)
echo ""
echo "[TEST] Docker logs: check for recent unexpected errors"
log_errors=$(docker compose logs hermes --tail=100 2>&1 | grep -i "fatal\|traceback\|internal.*error" | grep -v "500 Internal Server Error" | wc -l || echo "0")
if [ "$log_errors" = "0" ]; then
    echo "       ✓ PASS (no fatal errors in recent logs)"
    ((PASS++))
else
    echo "       ✗ FAIL ($log_errors error lines found)"
    ((FAIL++))
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "========== RESUMEN =========="
echo "PASS: $PASS/8"
echo "FAIL: $FAIL/8"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "✓ TODOS LOS TESTS PASARON"
    exit 0
else
    echo "✗ $FAIL TESTS FALLARON"
    exit 1
fi
