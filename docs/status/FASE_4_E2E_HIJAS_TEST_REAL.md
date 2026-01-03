# FASE 4: E2E Real Test - Spawner Hijas Lifecycle

**Timestamp**: 2026-01-03T00:00:00Z  
**Profile**: full-test (with spawner)  
**Objective**: Verify spawner hijas creation → registration → TTL → cleanup  
**Protocol**: All calls via tentaculo_link `:8000` (single entrypoint, never internal ports)

---

## Prerequisites

```bash
# Make sure full-test is running
make up-full-test  # or: docker compose -f docker-compose.full-test.yml up -d

# Verify services up
make smoke

# Verify DB connectivity
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table';"
# Expected: ~30 tables
```

---

## Test 1: Create Hija via /vx11/spawn

### Objective
Spawn a daughter instance with TTL=30s, verify creation.

### Command

```bash
SPAWN_PAYLOAD='{"profile":"spawner_test","ttl_seconds":30,"metadata":{"reason":"e2e-cleanup-test","phase":"4"}}'

curl -X POST http://localhost:8000/vx11/spawn \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d "$SPAWN_PAYLOAD" \
  | tee /tmp/spawn_response.json
```

### Expected Response

```json
{
  "status": "ok",
  "hija_id": "hija_20260103_001_uuid",
  "hija_port": 9001,
  "ttl_seconds": 30,
  "registered_at": "2026-01-03T00:00:00Z",
  "metadata": {
    "reason": "e2e-cleanup-test",
    "phase": "4"
  }
}
```

### Verification

```bash
# Extract hija_id
HIJA_ID=$(cat /tmp/spawn_response.json | jq -r '.hija_id')
echo "Spawned hija: $HIJA_ID"

# Verify hija is running
make status | grep -i hija

# Query DB for spawned entry
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db \
  "SELECT hija_id, registered_at, ttl_seconds, status FROM spawner_hijas WHERE hija_id='$HIJA_ID';"
# Expected: 1 row with status='active'
```

---

## Test 2: Verify Hija Registration in DB

### Objective
Confirm hija_id appears in `spawner_hijas` table with correct metadata.

### Command

```bash
# Query hijas table
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db << 'SQL'
  SELECT 
    hija_id, 
    registered_at, 
    ttl_seconds, 
    status, 
    metadata
  FROM spawner_hijas 
  ORDER BY registered_at DESC 
  LIMIT 5;
SQL
```

### Expected Output

```
hija_20260103_001_uuid|2026-01-03 00:00:00|30|active|{"reason":"e2e-cleanup-test","phase":"4"}
```

### Verification

```bash
# Check row count (should grow with each spawn)
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "SELECT COUNT(*) FROM spawner_hijas WHERE status='active';"
# Expected: 1 (or more if multiple tests running)
```

---

## Test 3: Wait for TTL Expiry (30s)

### Objective
Let TTL pass; verify automatic cleanup triggers.

### Command

```bash
# Record start time
echo "Waiting 35 seconds for TTL expiry..."
START=$(date +%s)

# Wait 35s (TTL is 30s)
sleep 35

END=$(date +%s)
ELAPSED=$((END - START))
echo "Elapsed: $ELAPSED seconds"

# Check hija status
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db \
  "SELECT hija_id, status, expired_at FROM spawner_hijas WHERE hija_id='$HIJA_ID';"
# Expected: status='expired' or 'cleaned', expired_at populated
```

### Expected Output

```
hija_20260103_001_uuid|expired|2026-01-03 00:00:30
```

---

## Test 4: Verify Cleanup (Port Released, DB Updated)

### Objective
Confirm hija port released, DB status updated to 'cleaned'.

### Command

```bash
# Check if hija port is released
lsof -i :9001 2>/dev/null || echo "Port 9001: RELEASED ✓"

# Query final status
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db \
  "SELECT hija_id, status, cleaned_at FROM spawner_hijas WHERE hija_id='$HIJA_ID';"
# Expected: status='cleaned', cleaned_at populated
```

### Expected Output

```
hija_20260103_001_uuid|cleaned|2026-01-03 00:00:35
```

---

## Test 5: Full Lifecycle Summary

### Command

```bash
# Generate full audit trail
cat > /tmp/e2e_summary.sql << 'SQL'
SELECT 
  'hija_id' AS column_name,
  'registered_at' AS when_created,
  'ttl_seconds' AS ttl,
  'status' AS final_status,
  'metadata' AS test_reason
FROM spawner_hijas 
WHERE metadata LIKE '%e2e-cleanup-test%'
ORDER BY registered_at DESC;
SQL

sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db < /tmp/e2e_summary.sql
```

### Expected Output

```
hija_id|when_created|ttl|final_status|test_reason
hija_20260103_001_uuid|2026-01-03 00:00:00|30|cleaned|{"reason":"e2e-cleanup-test","phase":"4"}
```

---

## Test 6: Stress Test (Multiple Hijas)

### Objective
Spawn 5 hijas rapid-fire; verify no collisions, all cleanup properly.

### Command

```bash
# Spawn 5 hijas in parallel
for i in {1..5}; do
  curl -s -X POST http://localhost:8000/vx11/spawn \
    -H "X-VX11-Token: vx11-test-token" \
    -H "Content-Type: application/json" \
    -d "{\"profile\":\"stress_test_$i\",\"ttl_seconds\":15}" \
    > /tmp/spawn_$i.json &
done
wait

echo "All 5 spawns initiated"

# Wait for cleanup
sleep 20

# Verify all cleaned
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db \
  "SELECT COUNT(*) as total, \
          SUM(CASE WHEN status='cleaned' THEN 1 ELSE 0 END) as cleaned, \
          SUM(CASE WHEN status='active' THEN 1 ELSE 0 END) as still_active \
   FROM spawner_hijas \
   WHERE metadata LIKE '%stress_test%';"
# Expected: total=5, cleaned=5, still_active=0
```

### Expected Output

```
total|cleaned|still_active
5|5|0
```

---

## Invariant Checks

### 1. Single Entrypoint (Always :8000)

```bash
# Verify spawn calls NEVER go direct to internal ports (8008, 8009, etc.)
grep -r "8008\|8009" docs/canon/ || echo "✓ No direct internal spawner port references"

# Verify tentaculo_link routes all spawn requests
grep "spawn" docs/canon/TENTACULO_LINK_ROUTING.md || echo "⚠️ Routing not documented"
```

### 2. solo_madre Default

```bash
# Verify spawner doesn't activate without explicit ttl_seconds
INVALID_SPAWN=$(curl -s -X POST http://localhost:8000/vx11/spawn \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{}' 2>&1)

echo "$INVALID_SPAWN" | grep -q "ttl_seconds\|required" && echo "✓ TTL required (solo_madre protected)" || echo "✗ Missing validation"
```

### 3. Token Security

```bash
# Verify spawn endpoint requires token
NO_TOKEN=$(curl -s -X POST http://localhost:8000/vx11/spawn \
  -H "Content-Type: application/json" \
  -d '{"ttl_seconds":30}' 2>&1)

echo "$NO_TOKEN" | grep -q "401\|unauthorized\|token" && echo "✓ Token enforced" || echo "✗ Missing auth check"
```

### 4. Database Integrity

```bash
# Full integrity check
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "PRAGMA integrity_check;"
# Expected: ok

# Foreign key check
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "PRAGMA foreign_key_check;"
# Expected: (empty = no violations)
```

---

## Success Criteria (Checklist)

- [ ] Test 1: Spawn endpoint returns 200 + hija_id
- [ ] Test 2: Hija registered in DB with correct metadata
- [ ] Test 3: TTL expires after specified seconds
- [ ] Test 4: Cleanup removes port binding + updates DB status
- [ ] Test 5: Full lifecycle logged correctly
- [ ] Test 6: Stress test (5 hijas) all cleanup without collision
- [ ] Invariant 1: All calls via :8000 (single entrypoint)
- [ ] Invariant 2: TTL required (solo_madre protected)
- [ ] Invariant 3: Token enforced
- [ ] Invariant 4: DB integrity OK

---

## Rollback Plan

If any test fails:

```bash
# Stop all hijas immediately
curl -X POST http://localhost:8000/vx11/policy/solo_madre/apply \
  -H "X-VX11-Token: vx11-test-token"

# Reset hijas table (DESTRUCTIVE)
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db \
  "DELETE FROM spawner_hijas WHERE metadata LIKE '%e2e-cleanup-test%' OR metadata LIKE '%stress_test%';"

# Restart services
make down && make up-full-test

# Re-run test from beginning
```

---

## Test Execution Log

**Date**: [TO BE FILLED]  
**Executor**: [copilot]  
**Passed**: [ ] YES / [ ] NO  
**Failures**: (if any)  

```
[Test results will be appended here]
```

---

## Post-Test Maintenance

After all tests complete:

```bash
# Regenerate DB maps
PYTHONPATH=/home/elkakas314/vx11 python3 -m scripts.generate_db_map_from_db /home/elkakas314/vx11/data/runtime/vx11.db

# Update SCORECARD
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "PRAGMA quick_check;" > /tmp/quick_check.txt
echo "Quick check: $(cat /tmp/quick_check.txt)"

# Commit evidence
git add docs/status/FASE_4_E2E_HIJAS_TEST_REAL.md
git commit -m "vx11: fase-4-e2e-hijas: real spawner lifecycle test + invariant checks"
```

---

**Status**: READY FOR EXECUTION  
**Next**: FASE 5 - Switch/Hermes Lightweight Setup
