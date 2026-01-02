# P2: LONG TASKS + DAUGHTERS LIFECYCLE + ROUTING EVIDENCE
**Date**: 2026-01-02  
**Phase**: P2 - E2E curl tests with growing tasks + daughter process validation + Switch routing instrumentation  
**Status**: ✅ **COMPLETED WITH FINDINGS**

---

## EXECUTIVE SUMMARY

**Objective**: Execute 3 growing E2E tasks via spawner, validate daughter process lifecycle (birth → death), and verify routing/CLI usage tracking.

**Results**:
- ✅ Task 1 (shell trivial): **DONE** - stdout captured, PID cleanup verified
- ⚠️ Task 2 (python calc): **ERROR** - `task_type: python` not properly routed to Python interpreter
- ✅ Task 3 (shell multi-step): **DONE** - complex output with JSON phases captured
- ✅ Daughter processes: **All dead** (no lingering PIDs)
- ✅ BD timestamps: `started_at`, `ended_at`, `exit_code` populated correctly
- ⚠️ Routing events: **No CID correlation** (routing_events not updated for recent P2 tasks)
- ⚠️ CLI usage stats: **No P2 events** (old test data from Dec 31)

---

## TEST EXECUTION

### FASE 1: 3 TASKS E2E

#### Task 1: Shell Trivial
```bash
POST /vx11/spawn
{
  "task_type": "shell",
  "code": "echo TASK1_OK",
  "ttl_seconds": 60
}
```

**Response**: `spawn-0f4bfb1a`  
**Status**: ✅ DONE  
**Exit Code**: 0  
**Stdout**: `TASK1_OK\n`  
**Timing**: 8.2ms (created → finished)  
**BD Record**: ✅ Found in spawns table with all fields populated

#### Task 2: Python Calculation
```bash
POST /vx11/spawn
{
  "task_type": "python",
  "code": "import json, time, math...",
  "ttl_seconds": 120
}
```

**Response**: `spawn-c300c78f`  
**Status**: ❌ **ERROR** (exit_code: 2)  
**Stderr**: `/bin/sh: 1: import: not found...`  
**Root Cause**: Handler attempted to execute as shell script instead of Python interpreter  

**Findings**:
- The endpoint accepts `task_type: python` but doesn't route to Python interpreter
- Fallback to shell execution fails because shell syntax ≠ Python syntax
- Need to fix spawner handler to detect task_type and use correct interpreter

#### Task 3: Shell Multi-Step Pipeline
```bash
POST /vx11/spawn
{
  "task_type": "shell",
  "code": "echo TASK3_START; python3 - <<'PY'...",
  "ttl_seconds": 240
}
```

**Response**: `spawn-ac44903d`  
**Status**: ✅ DONE (exit_code: 0)  
**Stdout**: Multi-line output with JSON phases  
**Timing**: 2.465s (created → finished)  
**BD Record**: ✅ All timestamps and output captured

---

## FASE 2: DAUGHTER PROCESS VALIDATION

### BD Query Results

```sql
SELECT name, status, pid, exit_code, created_at, started_at, ended_at
FROM spawns
WHERE name IN ('spawn-0f4bfb1a', 'spawn-c300c78f', 'spawn-ac44903d');
```

**Results**:
| name | status | pid | exit_code | created_at | started_at | ended_at | stdout |
|------|--------|-----|-----------|------------|------------|----------|--------|
| spawn-0f4bfb1a | completed | NULL | 0 | 00:55:49.237 | 00:55:49.250 | 00:55:49.258 | TASK1_OK |
| spawn-c300c78f | failed | NULL | 2 | 00:55:49.480 | 00:55:49.489 | 00:55:49.497 | (empty) |
| spawn-ac44903d | completed | NULL | 0 | 00:55:49.763 | 00:55:49.773 | 00:55:52.238 | TASK3_START... |

**Findings**:
- ✅ **All PIDs NULL**: No lingering processes (daughters properly cleaned up)
- ✅ **Status terminal**: `completed` or `failed` (no `accepted` or `pending` states)
- ✅ **Timestamps complete**: `started_at` and `ended_at` always populated
- ✅ **Exit codes**: 0 for success, 2 for error, captured correctly

### Spawn Status Distribution

```
accepted: 2
completed: 48
failed: 10
pending: 29
```

**Observations**:
- 48 completed spawns in total (healthy baseline)
- 10 failed spawns (some from old tests)
- 29 pending spawns (stuck; may indicate backlog or TTL issue)
- No zombie processes (PIDs all NULL)

---

## FASE 3: ROUTING EVENTS & CLI USAGE STATS

### Routing Events (Last 20)

```sql
SELECT * FROM routing_events ORDER BY timestamp DESC LIMIT 20;
```

**Results**: All entries are from **Dec 31, 03:29:31** (2025-12-31), with:
- `trace_id`: `test-trace-123`
- `route_type`: `cli`
- `provider_id`: `copilot_cli`
- `score`: 95.5
- `reasoning_short`: "High priority + balanced mode"

**Finding**: ❌ **NO P2 EVENTS** - routing_events not updated with P2 tasks or CID_SWITCH (`7a053f5a-b039-46ff-8220-02402a356e7f`)

### CLI Usage Stats (Last 20)

```sql
SELECT * FROM cli_usage_stats ORDER BY timestamp DESC LIMIT 20;
```

**Results**: All entries from **Dec 31** with providers:
- `test_provider`
- `copilot_cli`
- `generic_shell`

**Finding**: ❌ **NO P2 STATS** - No entries for current P2 execution

### Search for CID_SWITCH in routing_events

```sql
SELECT * FROM routing_events
WHERE trace_id='7a053f5a-b039-46ff-8220-02402a356e7f'
```

**Result**: **(empty)** - CID_SWITCH not recorded

---

## FASE 4: HERMES AUTOMATION STATUS

### Hermes Endpoints

```
/hermes/execute
/hermes/get-engine
/vx11/hermes/catalog
/vx11/hermes/discover
/vx11/hermes/health
```

### Hermes Health
```json
{
  "status": "ok",
  "module": "hermes",
  "version": "minimal"
}
```

✅ Hermes is healthy

### Hermes Discover
```json
{
  "status": "ok",
  "discovered": 0
}
```

⚠️ **0 CLIs discovered** - No automatic CLI/model registration happening

### Hermes Catalog
```json
{
  "cli_providers": [],
  "models": []
}
```

⚠️ **Empty** - No models registered

### HuggingFace Token
**Result**: No HF_TOKEN env variable found in hermes container

### Models Directory
**Files found**:
- `switch/hermes/local_scanner.py`
- `switch/hermes/scanner_v2.py`
- `switch/hermes/hf_scanner.py`
- `switch/hermes/cli_registry.py`
- `switch/hermes/model_scanner.py`

**Finding**: Infrastructure exists but not actively discovering/registering

---

## FASE 5+6: SERVICE LOGS

### Log Files Extracted
- `LOG_redis-test_tail300.txt` (1.6K)
- `LOG_madre_tail300.txt` (20K)
- `LOG_tentaculo_link_tail300.txt` (30K)
- `LOG_switch_tail300.txt` (24K)
- `LOG_hermes_tail300.txt` (20K)
- `LOG_spawner_tail300.txt` (24K)
- `LOG_operator-backend_tail300.txt` (21K)
- `LOG_operator-frontend_tail300.txt` (0K)

### Routing/Switch Evidence
```bash
grep -niE "switch|routing|provider|hermes|cli|trace_id|delegation" LOG_spawner_tail300.txt
```

**Result**: **(no matches)** - Spawner logs do not contain routing instrumentation

---

## FINDINGS & RECOMMENDATIONS

### ✅ Working Well
1. **Spawn lifecycle**: Create → start → finish with correct timestamps
2. **Process cleanup**: All daughter PIDs properly terminated (no zombies)
3. **Exit codes**: Captured correctly in DB
4. **Single entrypoint**: All operations via `http://localhost:8000`
5. **SOLO_MADRE policy**: Window enforcement working

### ⚠️ Needs Fixing
1. **Task type routing**: `task_type: python` should route to Python interpreter, not shell
2. **Routing event correlation**: P2 CID_SWITCH not recorded in `routing_events`
3. **CLI usage stats**: No automatic recording of Switch/Hermes usage
4. **Hermes automation**: Discover/catalog endpoints working but not finding/registering CLIs or models

### 🔧 Proposed Minimal Changes

#### 1. Fix spawner handler to respect task_type
**File**: `spawner/main.py` (or relevant handler)  
**Change**: Detect `task_type` and use appropriate interpreter:
- `task_type: shell` → `/bin/sh`
- `task_type: python` → `python3`
- `task_type: bash` → `/bin/bash`

#### 2. Add routing event recording in madre/switch delegation
**File**: `madre/main.py` (vx11_intent handler)  
**Change**: When delegating to Switch, insert into `routing_events`:
```python
routing_events.insert(
    trace_id=correlation_id,
    route_type="vx11_intent",
    provider_id="switch",
    score=1.0,
    reasoning_short=f"Delegation via require.switch=true"
)
```

#### 3. Add spawn trace_id and routing event for spawner
**File**: `spawner/main.py`  
**Change**: When spawning, create routing event:
```python
routing_events.insert(
    trace_id=spawn_uuid,
    route_type="spawn",
    provider_id="spawner",
    score=1.0,
    reasoning_short=f"Daughter spawn: {spawn_id}"
)
```

#### 4. Enable Hermes low-power discovery
**File**: `hermes/main.py` (discover endpoint)  
**Change**: Scan `/app/hermes/models/` and register local CLIs:
```python
@router.post("/discover")
async def discover():
    cli_providers = scan_local_models()  # ← Add this
    for cli in cli_providers:
        db.insert("cli_providers", cli)  # ← Register
    return {"status": "ok", "discovered": len(cli_providers)}
```

---

## CRITICAL INVARIANTS PRESERVED

- ✅ **Single entrypoint**: All via `http://localhost:8000`
- ✅ **SOLO_MADRE policy**: Windows enforced
- ✅ **No Operator changes**: Untouched
- ✅ **Process cleanup**: No zombies
- ✅ **DB consistency**: Spawns table correct

---

## NEXT STEPS

1. **P2.1**: Fix spawner task_type routing (shell vs python)
2. **P2.2**: Add routing event recording for delegation chains
3. **P2.3**: Enable Hermes discovery + model registration
4. **P2.4**: Re-run E2E with all fixes and validate BD consistency

---

## TEST ARTIFACTS

**Location**: `/home/elkakas314/vx11/docs/audit/20260102_p2_long_tasks_hijas/`

**Files** (50 total, ~250KB):
- Spawn requests/responses (10, 20, 30 prefixes)
- Result polling (11, 21, 31 prefixes)
- BD queries (40-52 prefixes)
- Hermes API (60-65 prefixes)
- Service logs (LOG_* files)
- This report

