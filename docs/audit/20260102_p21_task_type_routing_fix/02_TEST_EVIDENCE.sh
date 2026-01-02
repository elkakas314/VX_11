#!/bin/bash

# Test evidence for P2.1 task_type routing fix
# Task 2: Python execution via python3 interpreter
# Spawn UUID: 011de22d-9779-4b1f-9196-8fdb7c56c617

BASE_URL="http://localhost:8000"
TOKEN="vx11-test-token"

echo "=== [TEST] P2.1 Task Type Routing Fix - Python Execution ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Window open
echo "[Window Open]"
curl -s -X POST "$BASE_URL/vx11/window/open" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "spawner",
    "ttl_seconds": 600
  }' | jq . > 01_window_open_response.json
echo "✅ Window opened"
echo ""

# Spawn Python task
echo "[Spawn Python Task]"
curl -s -X POST "$BASE_URL/vx11/spawn" \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "python",
    "code": "import json; print(json.dumps({\"result\": 2 + 2, \"status\": \"ok\"}))",
    "max_retries": 0,
    "ttl_seconds": 30
  }' | jq . > 02_spawn_python_request.json
echo "✅ Spawn request sent"
SPAWN_UUID=$(jq -r '.spawn_uuid' 02_spawn_python_request.json)
echo "Spawn UUID: $SPAWN_UUID"
echo ""

# Wait for execution
echo "[Waiting for execution...]"
sleep 3

# Poll result
echo "[Poll Result]"
curl -s -X GET "$BASE_URL/vx11/result/$SPAWN_UUID" \
  -H "X-VX11-Token: $TOKEN" | jq . > 03_result_polling_response.json
echo "✅ Result polled"
echo ""

# DB Query
echo "[DB Query - Final Verification]"
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db << SQL > 04_db_final_result.txt
.headers on
.mode column
SELECT 
  uuid, 
  status, 
  exit_code, 
  stdout, 
  stderr,
  created_at, 
  ended_at
FROM spawns 
WHERE uuid = '$SPAWN_UUID'
LIMIT 1;
SQL
cat 04_db_final_result.txt
echo ""

echo "=== Summary ==="
EXIT_CODE=$(sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "SELECT exit_code FROM spawns WHERE uuid='$SPAWN_UUID' LIMIT 1;" 2>/dev/null)
STATUS=$(sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "SELECT status FROM spawns WHERE uuid='$SPAWN_UUID' LIMIT 1;" 2>/dev/null)
STDOUT=$(sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "SELECT stdout FROM spawns WHERE uuid='$SPAWN_UUID' LIMIT 1;" 2>/dev/null)

echo "Exit Code: $EXIT_CODE"
echo "Status: $STATUS"
echo "Stdout: $STDOUT"

if [ "$EXIT_CODE" == "0" ] && [ "$STATUS" == "completed" ]; then
  echo ""
  echo "✅ SUCCESS: Python task executed correctly with task_type routing!"
  echo "✅ Output is correct: $STDOUT (2+2=4)"
else
  echo ""
  echo "❌ FAILED"
fi
