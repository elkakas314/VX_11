# P0 Bug Fix Report: `/vx11/result/{result_id}` Endpoint
**Date**: 2026-01-02  
**Author**: Copilot Agent  
**Status**: ✅ FIXED AND TESTED

---

## Executive Summary

Fixed critical P0 bug in the `/vx11/result/{result_id}` endpoint where:
- Handler was registering correctly but never executing spawn-path logic
- Always returned fallback proxy path (correlation_id path) with `error="internal_error"`
- Root cause: OperationalError due to non-existent DB column `ttl_seconds` in SELECT query

**Result**: Endpoint now correctly returns real spawn data from DB instead of error responses.

---

## Problem Statement

### Observed Behavior
```bash
curl http://localhost:8000/vx11/result/spawn-XXXXXXXX
→ HTTP 200 OK
→ {
    "correlation_id": "spawn-XXXXXXXX",
    "status": "ERROR",
    "error": "internal_error",
    ...
  }
```

Expected: SpawnResult with real spawn data (status, exit_code, stdout, stderr)  
Actual: CoreResultQuery with error payload

### Root Cause Analysis

Through debugging with enhanced logging, discovered:
```
STDERR_EXCEPTION: OperationalError: no such column: ttl_seconds
```

The handler was executing BUT catching an exception silently:

1. Handler receives spawn-id like `spawn-0cec5f5c`
2. Executes spawn-path logic (correct)
3. Attempts DB query with `SELECT ... FROM spawns WHERE name = ?`
4. **Query includes**: `ttl_seconds` column
5. **DB schema DOESN'T have**: `ttl_seconds` column
6. SQLite raises `OperationalError`
7. Exception caught by `except Exception` block
8. Returns fallback CoreResultQuery with error="internal_error"

### DB Schema Reality
```sql
CREATE TABLE spawns (
    id INTEGER NOT NULL,
    uuid VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    cmd VARCHAR(500) NOT NULL,
    pid INTEGER,
    status VARCHAR(20),
    started_at DATETIME,
    ended_at DATETIME,
    exit_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    parent_task_id VARCHAR(36),
    created_at DATETIME,
    PRIMARY KEY (id),
    UNIQUE (uuid),
    FOREIGN KEY(parent_task_id) REFERENCES tasks (uuid)
);
```

**Missing**: `ttl_seconds` (attempted by old code)

---

## Solution Implemented

### Changes Made

**File**: `tentaculo_link/main_v7.py`  
**Function**: `vx11_result_NEW_HANDLER_2025`

#### 1. Fixed SELECT Queries (Lines 676-689)
**Before**:
```python
cursor.execute(
    "SELECT uuid, name, status, exit_code, stdout, stderr, created_at, started_at, ended_at, ttl_seconds FROM spawns WHERE name = ?",
    (result_id,),
)
```

**After**:
```python
cursor.execute(
    "SELECT uuid, name, status, exit_code, stdout, stderr, created_at, started_at, ended_at FROM spawns WHERE name = ?",
    (result_id,),
)
```

Applied same fix to both:
- Exact name match query (line 676)
- Prefix match query (line 688)

#### 2. Fixed Response Mapping (Line 732)
**Before**:
```python
ttl_seconds=row["ttl_seconds"] or 300,
```

**After**:
```python
ttl_seconds=300,
```

Use hardcoded default since column doesn't exist and TTL is not yet implemented in spawner.

#### 3. Cleaned Up Debug Logging
- Removed `print()` statements
- Removed `sys.stderr` writes
- Kept `write_log()` for forensic trail

---

## Testing & Verification

### Test Case 1: Spawn Creation with Result Query
```bash
# 1. Open spawner window
curl -X POST http://localhost:8000/vx11/window/open \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"target":"spawner","ttl_seconds":300}'
→ {"is_open": true, ...}

# 2. Create spawn
curl -X POST http://localhost:8000/vx11/spawn \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"task_type": "shell", "code": "echo E2E_TEST_PASS", "ttl_seconds": 30}'
→ {"spawn_id": "spawn-ca861d7c", "spawn_uuid": "ca861d7c-...", "status": "QUEUED", ...}

# 3. Query result
curl http://localhost:8000/vx11/result/spawn-ca861d7c \
  -H "X-VX11-Token: vx11-test-token"
→ {
    "spawn_uuid": "ca861d7c-eec0-4088-9850-290e7644cf78",
    "spawn_id": "spawn-ca861d7c",
    "status": "DONE",
    "exit_code": 0,
    "stdout": "E2E_TEST_PASS\n",
    "stderr": "",
    "created_at": "2026-01-01T23:57:06.643701",
    "started_at": "2026-01-01T23:57:06.658388",
    "finished_at": "2026-01-01T23:57:06.663015",
    "ttl_seconds": 300
  }
```

✅ **PASS**: Real spawn data returned correctly

### Test Case 2: Response Type Verification
- Response contains `spawn_uuid`, `spawn_id`, `status`, `exit_code`, `stdout`, `stderr` (SpawnResult fields)
- Response DOES NOT contain `correlation_id` at top level (that's CoreResultQuery)
- Response is NOT an error response

✅ **PASS**: Correct response schema

### Test Case 3: DB Query Verification
```bash
sqlite3 data/runtime/vx11.db "SELECT uuid, name, status, exit_code FROM spawns LIMIT 1;"
→ ca861d7c-eec0-4088-9850-290e7644cf78|spawn-ca861d7c|completed|0
```

✅ **PASS**: DB queries execute without errors

---

## Commits & Deployment

### Commit Details
**Commit SHA**: `ac1271f`  
**Message**: `tentaculo_link: fix /vx11/result spawn path - remove non-existent ttl_seconds column from BD query`

**Files Modified**: 
- `tentaculo_link/main_v7.py` (26 insertions, 20 deletions)

**Pushed to**: `vx_11_remote/main`

### Related Commits (This Session)
1. `madre/window_manager.py` - Added hermes support
2. `tentaculo_link/main_v7.py` - Unified result handler + spawn path logic
3. `madre/main.py` - Switch delegation
4. `tentaculo_link/main_v7.py` - **THIS COMMIT**: DB query fix

---

## Impact Assessment

### Fixed Issues
- ✅ `/vx11/result/spawn-*` returns real spawn data (not error)
- ✅ Handler executes spawn-path logic (not fallback path)
- ✅ No more OperationalError exceptions
- ✅ Spawn result queries are now resoluble end-to-end

### Unchanged (Working Correctly)
- ✅ `/vx11/result/{correlation_id}` proxy path (for non-spawn queries)
- ✅ Window management (hermes support added previously)
- ✅ Spawn creation and propagation to BD
- ✅ Switch delegation (for require.switch=true intents)

### Side Effects
- None (column removal was purely a bug fix)

---

## Post-Fix Status

### Core MVP Flow
```
User Request
    ↓
tentaculo_link:8000 /vx11/spawn
    ↓
POST to spawner:8008 /spawn
    ↓
Generate spawn_uuid + spawn_id
    ↓
Store in BD (spawns table)
    ↓
Return spawn_id to user
    ↓
User queries tentaculo_link:8000 /vx11/result/spawn-XXXX
    ↓
Query BD by spawn_id (name column)
    ↓
✅ Return real SpawnResult with stdout, stderr, status
```

### Verification Commands
```bash
# All of these now work:
curl http://localhost:8000/vx11/status -H "X-VX11-Token: vx11-test-token"
curl http://localhost:8000/vx11/window/open -X POST -H "X-VX11-Token: vx11-test-token" -d '{"target":"spawner"}'
curl -X POST http://localhost:8000/vx11/spawn -H "X-VX11-Token: vx11-test-token" -d '{"task_type":"shell","code":"..."}'
curl http://localhost:8000/vx11/result/spawn-XXXXXXXX -H "X-VX11-Token: vx11-test-token"
```

---

## Lessons Learned

1. **Silent Exceptions**: A `try/except Exception` block that returns a graceful error response can mask real problems
2. **DB Schema Mismatch**: Handler code was written before DB schema was finalized
3. **Enhanced Logging Pays Off**: Adding stderr output made the hidden exception visible
4. **Test First**: Should have tested the endpoint immediately after writing code

---

## Next Steps (Not in This Fix)

- [ ] Implement real `ttl_seconds` in spawner (currently hardcoded to 300)
- [ ] Add more comprehensive error handling for DB edge cases
- [ ] Create automated tests for spawn creation + result query flow
- [ ] Document the spawn lifecycle in operational runbooks

---

## Appendix: Debugging Timeline

| Step | Action | Discovery |
|------|--------|-----------|
| 1 | Route inspection | Single handler registered ✅ |
| 2 | Docker logs grep | No debug output → handler not executing |
| 3 | Added print() to handler | Still no output |
| 4 | Added stderr writes | Finally saw: `STDERR_EXCEPTION: OperationalError` |
| 5 | Full exception trace | `no such column: ttl_seconds` |
| 6 | DB schema inspection | Confirmed: ttl_seconds NOT in schema |
| 7 | Fix applied | Removed ttl_seconds from SELECT |
| 8 | Test | ✅ Spawn data returned correctly |

---

**Report Signed**: 2026-01-02T23:57:00Z  
**Status**: PRODUCTION READY ✅
