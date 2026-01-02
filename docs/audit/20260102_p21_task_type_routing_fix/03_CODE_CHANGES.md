# Code Changes - P2.1 Task Type Routing Fix

## Files Modified

### 1. spawner/main.py

#### Change 1: Function `_execute_command` (lines 395-442)

**Old signature**:
```python
def _execute_command(cmd: str, ttl_seconds: int) -> Tuple[int, str, str, str]:
```

**New signature**:
```python
def _execute_command(cmd: str, ttl_seconds: int, task_type: Optional[str] = None) -> Tuple[int, str, str, str]:
```

**Key additions**:
```python
# Route to appropriate interpreter based on task_type
if task_type == "python":
    proc = subprocess.Popen(
        ["python3", "-c", cmd],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
elif task_type == "bash":
    proc = subprocess.Popen(
        ["/bin/bash", "-c", cmd],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
else:
    # Default: shell execution (backward compatible)
    proc = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
```

#### Change 2: Function `_run_spawn_lifecycle` signature (line 492-503)

**Old**:
```python
async def _run_spawn_lifecycle(
    spawn_uuid: str,
    task_id: int,
    daughter_id: int,
    attempt_id: int,
    cmd: str,
    ttl_seconds: int,
    max_retries: int,
    auto_retry: bool,
    mutation_level: int,
) -> None:
```

**New** (added parameter):
```python
async def _run_spawn_lifecycle(
    spawn_uuid: str,
    task_id: int,
    daughter_id: int,
    attempt_id: int,
    cmd: str,
    ttl_seconds: int,
    max_retries: int,
    auto_retry: bool,
    mutation_level: int,
    task_type: Optional[str] = None,  # ← ADDED
) -> None:
```

#### Change 3: Call to `_execute_command` in `_run_spawn_lifecycle` (line 532)

**Old**:
```python
exit_code, stdout, stderr, status = await asyncio.to_thread(
    _execute_command, cmd, ttl_seconds
)
```

**New** (passes task_type):
```python
exit_code, stdout, stderr, status = await asyncio.to_thread(
    _execute_command, cmd, ttl_seconds, task_type
)
```

#### Change 4: POST `/spawn` handler call (lines 825-839)

**Old**:
```python
if req.cmd:
    background_tasks.add_task(
        _run_spawn_lifecycle,
        spawn_uuid,
        task_id,
        daughter_id,
        attempt_id,
        req.cmd,
        req.ttl_seconds,
        req.max_retries,
        req.auto_retry,
        req.mutation_level,
    )
```

**New** (added `req.task_type`):
```python
if req.cmd:
    background_tasks.add_task(
        _run_spawn_lifecycle,
        spawn_uuid,
        task_id,
        daughter_id,
        attempt_id,
        req.cmd,
        req.ttl_seconds,
        req.max_retries,
        req.auto_retry,
        req.mutation_level,
        req.task_type,  # ← ADDED
    )
```

## Models - No Changes Required

The `SpawnRequest` model in spawner/main.py already had the `task_type` field:
```python
class SpawnRequest(BaseModel):
    name: Optional[str] = None
    cmd: Optional[str] = None
    task_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    intent: str = "spawn"
    task_type: Optional[str] = None  # ← Already present
    ...
```

## Impact Analysis

### Backward Compatibility
✅ **Fully backward compatible**:
- `task_type` parameter is optional (defaults to `None`)
- When `task_type=None`, uses original `shell=True` behavior
- Existing callers with no `task_type` parameter continue to work

### Type Safety
✅ **Type annotations preserved**:
- Added `Optional[str]` type hints
- No breaking changes to function signatures

### Performance
✅ **No performance degradation**:
- Single conditional check per execution
- No additional overhead for default case
- Subprocess execution time unchanged

### Bug Fixes
✅ **Fixes Python execution bug**:
- Before: Python code → shell tried to parse it → exit code 2, error "/bin/sh: import not found"
- After: Python code → python3 interpreter → exit code 0, correct output

## Testing

### Test Case
- **Task**: Execute Python calculation: `2 + 2 = 4`
- **Command**: `import json; print(json.dumps({"result": 2 + 2, "status": "ok"}))`
- **task_type**: `"python"`

### Results
✅ Status: **completed**
✅ Exit code: **0**
✅ Output: **`{"result": 4, "status": "ok"}`**
✅ Execution time: **67.56ms** (from aa93afc6-b9d5-474f-84ad-6d0acf3192a5)

## Deployment Notes

1. **Service restart**: spawner must be restarted to load new code
   - Status: ✅ Already restarted (confirmed healthy)
   
2. **DB schema**: No changes required
   - spawns table remains unchanged
   - task_type is passed as part of spawn request, not stored separately
   
3. **Rollback**: No special considerations
   - Changes are purely additive
   - Can safely revert by removing `task_type` parameter
   
## Related Documents

- P2 Long Tasks Report: `docs/audit/20260102_p2_long_tasks_hijas/FINAL_REPORT_P2_LONG_TASKS.md`
- P2.1 Fix Summary: `docs/audit/20260102_p21_task_type_routing_fix/01_FIX_SUMMARY.md`
- Test Evidence: `docs/audit/20260102_p21_task_type_routing_fix/02_TEST_EVIDENCE.sh`

