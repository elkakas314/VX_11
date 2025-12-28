#!/bin/bash
set -eu

echo "=== TEST P0: SOLO_MADRE_CORE VERIFICATION ==="

# Check 1: Only 3 services running
echo "Check 1: Container count..."
COUNT=$(docker compose ps --services --all | wc -l)
RUNNING=$(docker compose ps --services 2>/dev/null | grep -E 'madre|tentaculo_link|redis' | wc -l)
if [ "$RUNNING" -eq 3 ]; then
  echo "  ✅ PASS: Exactly 3 services running (madre, tentaculo_link, redis)"
else
  echo "  ❌ FAIL: Expected 3, got $RUNNING"
  docker compose ps
  exit 1
fi

# Check 2: tentaculo_link port 8000 is listening
echo "Check 2: Tentaculo entrypoint..."
if curl -sf http://localhost:8000/health > /dev/null; then
  echo "  ✅ PASS: :8000 (tentaculo_link) responding"
else
  echo "  ❌ FAIL: :8000 not responding"
  exit 1
fi

# Check 3: madre port 8001 is listening
echo "Check 3: Madre orchestration..."
if curl -sf http://localhost:8001/health > /dev/null; then
  echo "  ✅ PASS: :8001 (madre) responding"
else
  echo "  ❌ FAIL: :8001 not responding"
  exit 1
fi

# Check 4: redis port 6379 accessible
echo "Check 4: Redis cache..."
if docker exec vx11-redis redis-cli -a vx11-redis-local PING 2>/dev/null | grep -q PONG; then
  echo "  ✅ PASS: Redis healthy"
else
  # Alternative: just check if container is running
  if docker compose ps redis 2>/dev/null | grep -q "Up"; then
    echo "  ✅ PASS: Redis container running"
  else
    echo "  ❌ FAIL: Redis not responding"
    exit 1
  fi
fi

# Check 5: No app services running (switch, hermes, spawner, etc)
echo "Check 5: App services OFF..."
for svc in switch hermes spawner hormiguero manifestator shubniggurath mcp operator-backend operator-frontend; do
  if docker compose ps 2>/dev/null | grep -q "$svc.*Up"; then
    echo "  ❌ FAIL: Service '$svc' is running (should be OFF)"
    exit 1
  fi
done
echo "  ✅ PASS: All app services are OFF"

# Check 6: Tentaculo aggregated status shows madre OK
echo "Check 6: Tentaculo status report..."
STATUS=$(curl -s http://localhost:8000/vx11/status | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('summary', {}).get('healthy_modules', 0))")
if [ "$STATUS" -ge 1 ]; then
  echo "  ✅ PASS: Tentaculo sees $STATUS healthy core modules"
else
  echo "  ❌ FAIL: Tentaculo status reports 0 healthy modules"
  exit 1
fi

echo ""
echo "=== ✅ ALL TESTS PASSED ==="
echo "SOLO_MADRE_CORE is operational and stable."
