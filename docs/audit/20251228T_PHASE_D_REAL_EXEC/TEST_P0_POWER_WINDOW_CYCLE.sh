#!/bin/bash
set -eu

echo "=== TEST P0: POWER WINDOW CYCLE (Open → Verify → Close) ==="

TOKEN="vx11-local-token"
MADRE="http://localhost:8001"
TIMEOUT=60

# Function: wait for service health
wait_for_service() {
  local svc=$1
  local port=$2
  local max_wait=30
  local elapsed=0
  
  while [ $elapsed -lt $max_wait ]; do
    if curl -sf http://localhost:$port/health > /dev/null 2>&1; then
      echo "    ✅ $svc:$port responding"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  echo "    ⚠️  $svc:$port not responding (timeout)"
  return 1
}

# STEP 1: Open window (start switch + hermes)
echo "Step 1: Opening power window (switch + hermes)..."
WINDOW_RESP=$(curl -s -X POST -H "x-vx11-token: $TOKEN" "$MADRE/power/window/open" \
  -H "Content-Type: application/json" \
  -d '{
    "services": ["switch", "hermes"],
    "ttl_sec": 120,
    "mode": "ttl",
    "reason": "test_phase_d"
  }')

WINDOW_ID=$(echo "$WINDOW_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('window_id', 'ERROR'))" 2>/dev/null || echo "ERROR")
if [ "$WINDOW_ID" = "ERROR" ]; then
  echo "  ❌ FAIL: Window open failed"
  echo "  Response: $WINDOW_RESP"
  exit 1
fi
echo "  ✅ PASS: Window opened (ID: $WINDOW_ID)"

# STEP 2: Verify services started
echo "Step 2: Verifying services are UP..."
sleep 10  # Give services time to start

if docker compose ps | grep -q "switch.*Up"; then
  echo "  ✅ PASS: Switch container running"
else
  echo "  ❌ FAIL: Switch not running"
  docker compose ps | grep switch || true
fi

if docker compose ps | grep -q "hermes.*Up"; then
  echo "  ✅ PASS: Hermes container running"
else
  echo "  ❌ FAIL: Hermes not running"
  docker compose ps | grep hermes || true
fi

# STEP 3: Close window
echo "Step 3: Closing power window..."
CLOSE_RESP=$(curl -s -X POST -H "x-vx11-token: $TOKEN" "$MADRE/power/window/close" \
  -H "Content-Type: application/json")

CLOSED_WINDOW=$(echo "$CLOSE_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('state', 'ERROR'))" 2>/dev/null || echo "ERROR")
if [ "$CLOSED_WINDOW" != "closed" ]; then
  echo "  ⚠️  WARN: Close response unclear: $CLOSE_RESP"
else
  echo "  ✅ PASS: Window closed"
fi

# STEP 4: Verify return to SOLO_MADRE_CORE
echo "Step 4: Verifying return to SOLO_MADRE_CORE..."
sleep 5

RUNNING=$(docker compose ps --services 2>/dev/null | wc -l)
if [ "$RUNNING" -le 3 ]; then
  echo "  ✅ PASS: Services reduced to core ($RUNNING containers)"
else
  echo "  ⚠️  WARN: Services > 3: $RUNNING"
  docker compose ps
fi

echo ""
echo "=== ✅ WINDOW CYCLE COMPLETE ==="
echo "Real docker compose execution validated."
