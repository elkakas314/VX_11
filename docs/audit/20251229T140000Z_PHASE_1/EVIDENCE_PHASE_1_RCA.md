# PHASE 1 — SWITCH CRASH RCA + FIX

**Timestamp**: 2025-12-29T14:00:00Z  
**Objective**: Fix ModuleNotFoundError, make switch arrancable en ventana temporal  
**Status**: ANALYSIS + FIX READY

---

## EVIDENCE: SWITCH LOGS & DOCKERFILE

###logs Analysis

```
ModuleNotFoundError: No module named 'switch'
```

**Stack trace shows**:
- uvicorn trying to load `switch.main:app` (from CMD)
- importlib._bootstrap unable to find module
- Loop repeats (container restart loop)

### Dockerfile Analysis

```dockerfile
FROM python:3.10-slim AS builder
WORKDIR /build
# ... build stage ...
COPY --from=builder /root/.local /root/.local

FROM python:3.10-slim
WORKDIR /app
ENV BASE_PATH=/app
ENV PYTHONUNBUFFERED=1

COPY config /app/config/
COPY switch /app/switch/
COPY sitecustomize.py /app/

CMD ["python", "-m", "uvicorn", "switch.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### Switch Module Structure

```
switch/
├── __init__.py           ✅ EXISTS (21 bytes)
├── main.py               ✅ EXISTS (99K)
├── adapters.py
├── cli_concentrator/
├── deepseek_r1_provider.py
├── fluzo/
├── ga_optimizer.py
├── ga_router.py
├── hermes/
├── pheromone_engine.py
└── ... (10+ more files)
```

---

## ROOT CAUSE ANALYSIS

### Hypothesis 1: PYTHONPATH not configured ✅ ROOT CAUSE

**Evidence**:
- `switch/__init__.py` EXISTS (21 bytes)
- Working directory: `/app`
- CMD uses `-m uvicorn switch.main:app` (module mode)
- No explicit PYTHONPATH configuration in Dockerfile
- Python 3.10 default PYTHONPATH may not include `/app`

**Verification**:
- When Python runs `-m uvicorn`, it needs `.` or `/app` in PYTHONPATH
- Without explicit `export PYTHONPATH=/app:$PYTHONPATH`, Python can't find `switch` package

### Hypothesis 2: Missing `__pycache__` (unlikely)

**Evidence**: `switch/__pycache__/` exists on host; but Docker build is fresh

### Conclusion

**PRIMARY**: Missing explicit PYTHONPATH in Dockerfile  
**SECONDARY**: Possibly missing environment propagation  
**SEVERITY**: LOW (one-line fix)  

---

## MINIMAL FIX (Tier 1)

### Option A: Add PYTHONPATH to Dockerfile (RECOMMENDED)

**File**: `switch/Dockerfile`  
**Change**: Add one line after `ENV PYTHONUNBUFFERED=1`

```dockerfile
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH    # ← ADD THIS
```

**Reasoning**:
- Explicit PYTHONPATH tells Python where to find modules
- Ensures `-m uvicorn switch.main:app` can resolve `switch` package
- No other changes needed (no file moves, no rebuild of main.py)

### Option B: Change CMD to use absolute path (alternative)

```dockerfile
CMD ["python", "-m", "uvicorn", "/app/switch/main.py", "--host", "0.0.0.0", "--port", "8002"]
```

**Downside**: Changes entry point semantics; less conventional

### Option C: Use entrypoint script (overkill for this issue)

---

## IMPLEMENTATION: OPTION A (RECOMMENDED)

**Target file**: `switch/Dockerfile`  
**Lines**: After line ~19 (after ENV PYTHONUNBUFFERED=1)  
**Change**: Single line addition  

```diff
 ENV BASE_PATH=/app
 ENV ULTRA_LOW_MEMORY=true
 ENV PYTHONUNBUFFERED=1
+ENV PYTHONPATH=/app:$PYTHONPATH

 RUN apt-get update && apt-get install -y --no-install-recommends curl && \
```

---

## VERIFICATION PLAN (POST-FIX)

### Step 1: Rebuild switch image

```bash
docker compose build switch
```

### Step 2: Open temporary window

```bash
docker compose up -d switch
sleep 3
```

### Step 3: Check health

```bash
docker compose ps switch
curl -s http://localhost:8002/health || echo "Failed"
```

### Step 4: Verify logs (should NOT see ModuleNotFoundError)

```bash
docker compose logs --tail=50 switch | grep -i "error\|traceback" || echo "✅ No errors"
```

### Step 5: Stop switch (revert to solo_madre)

```bash
docker compose stop switch
docker compose ps --all | grep switch
# Should show: Exited (0) just now
```

---

## DS-R1(A) PLAN — PHASE 1

**Objective**: Fix switch crash via PYTHONPATH env var  
**Scope**: 1-line Dockerfile change  
**Risk**: Very LOW (isolated, container-level)  
**Rollback**: `git checkout -- switch/Dockerfile`  

**Phases**:
1. Modify switch/Dockerfile (1 line)
2. Rebuild image
3. Test in window (up → health check → down)
4. Verify solo_madre reverts
5. Commit

**Expected outcome**: switch container boots with PYTHONPATH fix, no ModuleNotFoundError

---

## NEXT: IMPLEMENT

Proceeding with Option A (add PYTHONPATH to switch/Dockerfile)

