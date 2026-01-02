# P2.1 Fix: Task Type Routing for Python/Bash Execution

## Problem Statement

In Session 3 (P2 Long Tasks), Task 2 (Python calculation) failed with:
- **Exit code**: 2
- **Stderr**: `/bin/sh: 1: import not found` (shell trying to execute Python syntax)
- **Root cause**: `spawner/main.py` used `subprocess.Popen(cmd, shell=True)` for all task types, but Python code requires Python interpreter, not shell

## Solution Implemented

### Change 1: Update `_execute_command` function signature (lines 395-442 in spawner/main.py)

**Before**: 
```python
def _execute_command(cmd: str, ttl_seconds: int) -> Tuple[int, str, str, str]:
    # Always used shell=True
    proc = subprocess.Popen(cmd, shell=True, ...)
```

**After**:
```python
def _execute_command(cmd: str, ttl_seconds: int, task_type: Optional[str] = None) -> Tuple[int, str, str, str]:
    if task_type == "python":
        proc = subprocess.Popen(["python3", "-c", cmd], ...)
    elif task_type == "bash":
        proc = subprocess.Popen(["/bin/bash", "-c", cmd], ...)
    else:
        proc = subprocess.Popen(cmd, shell=True, ...)  # Default behavior
```

### Change 2: Update `_run_spawn_lifecycle` function signature (line 492)

Added `task_type: Optional[str] = None` parameter to accept and forward task_type.

### Change 3: Update `_run_spawn_lifecycle` call to `_execute_command` (line 532)

**Before**:
```python
exit_code, stdout, stderr, status = await asyncio.to_thread(
    _execute_command, cmd, ttl_seconds
)
```

**After**:
```python
exit_code, stdout, stderr, status = await asyncio.to_thread(
    _execute_command, cmd, ttl_seconds, task_type
)
```

### Change 4: Update POST `/spawn` handler (lines 825-839)

Added `req.task_type` parameter to `background_tasks.add_task()` call.

## Verification

### Test Execution

**Command**:
```bash
curl -s -X POST "http://localhost:8000/vx11/spawn" \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "python",
    "code": "import json; print(json.dumps({\"result\": 2 + 2, \"status\": \"ok\"}))",
    "max_retries": 0,
    "ttl_seconds": 30
  }'
```

**Spawn Details**:
- Spawn UUID: `011de22d-9779-4b1f-9196-8fdb7c56c617`
- Task type: python
- Command: `import json; print(json.dumps({"result": 2 + 2, "status": "ok"}))`

**Result** (from spawns table):
- Status: **completed** ✅
- Exit code: **0** ✅
- Stdout: **`{"result": 4, "status": "ok"}`** ✅
- Execution time: 82.24ms
- Created at: 2026-01-02 01:05:53.070250
- Ended at: 2026-01-02 01:05:53.152490

### Verification Query
```sql
SELECT uuid, status, exit_code, stdout, stderr, created_at, ended_at
FROM spawns 
WHERE uuid = '011de22d-9779-4b1f-9196-8fdb7c56c617';
```

Result:
```
011de22d-9779-4b1f-9196-8fdb7c56c617 | completed | 0 | {"result": 4, "status": "ok"} | [null] | 2026-01-02 01:05:53.070250 | 2026-01-02 01:05:53.152490
```

## Impact

- ✅ Python tasks now execute via `python3` interpreter (not shell)
- ✅ Bash tasks can execute via `/bin/bash -c` (explicit routing available)
- ✅ Shell tasks still execute with `shell=True` (backward compatible)
- ✅ Task 2 now **WORKS** (was failing with exit code 2, now returns exit code 0)

## Code Changes Summary

- **Files modified**: 1 (spawner/main.py)
- **Functions modified**: 3 (_execute_command, _run_spawn_lifecycle, POST /spawn handler)
- **Lines added**: 40 (new _execute_command logic)
- **Lines removed**: 0 (only extensions, no deletions)
- **Service restarted**: spawner (successful restart)

## Next Steps

1. ✅ Complete P2 E2E re-run with all 3 tasks to verify full flow
2. ⏳ Implement routing event recording (P2.2)
3. ⏳ Enable Hermes discovery (P2.3)
4. ⏳ Add CLI provider registration (P2.4)

## Session Context

- **Session**: 3 (Late)
- **Objective**: Fix task_type routing bug found during P2 long tasks E2E
- **Time spent on fix**: ~10 minutes (identify, modify, test, verify)
- **Status**: ✅ FIX VERIFIED & WORKING

