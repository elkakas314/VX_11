# DS-R1(A) PLAN — PHASE 1: SWITCH CRASH FIX STRATEGY

**DeepSeek R1 Reasoning Model**  
**Correlation ID**: phase-1-plan-20251229-140000  
**Objective**: Plan switch crash fix based on RCA findings

---

## ANALYSIS

### Root Cause (Evidence-Based)
- Error: `ModuleNotFoundError: No module named 'switch'`
- Location: uvicorn import loader
- Context: Dockerfile does NOT set PYTHONPATH
- Solution: Add `ENV PYTHONPATH=/app:$PYTHONPATH` to Dockerfile

### Why This Works
1. Python `-m uvicorn switch.main:app` requires module discovery
2. Without explicit PYTHONPATH, Python can't find `/app/switch` package
3. Adding PYTHONPATH to /app tells Python where to find `switch` module
4. No other changes needed (switch/__init__.py exists, requirements installed)

### Risk Assessment
- **Scope**: 1-line Dockerfile change
- **Blast radius**: switch container only
- **Rollback**: Single git checkout
- **Downtime**: ~1 min (rebuild + restart)

---

## IMPLEMENTATION PLAN

### Phase 1.1: Modify Dockerfile
```dockerfile
# ADD THIS LINE after ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
```

### Phase 1.2: Rebuild Image
```bash
docker compose build switch
```

### Phase 1.3: Test in Temporal Window
```bash
docker compose up -d switch
curl http://localhost:8002/health
docker compose stop switch
```

### Phase 1.4: Verify solo_madre Reverts
```bash
docker compose ps --all  # switch should be Exited(0)
```

### Phase 1.5: Commit
```bash
git add switch/Dockerfile
git commit -m "vx11: PHASE-1: Fix switch ModuleNotFoundError via PYTHONPATH"
git push vx_11_remote main
```

---

## EXPECTED OUTCOMES

- ✅ switch container boots without ModuleNotFoundError
- ✅ /health endpoint responds (200 OK for GET, allowed methods correct)
- ✅ Application startup completes normally
- ✅ Default state remains solo_madre (switch OFF, exited cleanly)
- ✅ No side-effects to other services

---

## DELIVERABLES

1. Updated switch/Dockerfile with PYTHONPATH fix
2. Test evidence: logs, health check, process status
3. Commit with clear message
4. PHASE 1 REVIEW (DS-R1(B)) follows

