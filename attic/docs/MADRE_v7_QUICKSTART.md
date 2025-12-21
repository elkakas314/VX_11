# Madre v7 — QUICK START GUIDE

**Goal:** Get Madre running and test endpoints in 5 minutes

---

## 1️⃣ VERIFY STRUCTURE

```bash
cd /home/elkakas314/vx11

# Check core modules
ls -lh madre/core/
# Expected: __init__.py, models.py, db.py, parser.py, policy.py, planner.py, runner.py, delegation.py

# Check main files
ls -lh madre/main.py madre/main_v7_production.py

# Check tests
ls -lh tests/test_madre.py
```

**Expected output:** All files present ✅

---

## 2️⃣ RUN TESTS

```bash
cd /home/elkakas314/vx11

# Verify Python environment
python3 --version  # Should be 3.10+

# Compile Python
python3 -m py_compile madre/core/*.py madre/main.py

# Run tests
python3 -m pytest tests/test_madre.py -v --tb=short

# Expected: 25/25 PASSED
```

**Sample output:**
```
============================= 25 passed in 5.65s ==============================
```

---

## 3️⃣ START MADRE (LOCAL DEV)

### Option A: Docker Compose (Recommended)

```bash
cd /home/elkakas314/vx11

# Build image
docker build -f madre/Dockerfile -t vx11-madre:7.0 .

# Start service
docker-compose up -d madre

# Check logs
docker logs -f vx11-madre-1

# Health check
curl -s http://127.0.0.1:8001/health | jq .

# Expected: {"module": "madre", "status": "ok", "version": "7.0", ...}
```

### Option B: Direct Python (Development Only)

```bash
cd /home/elkakas314/vx11

# Source virtual environment
source .venv/bin/activate

# Run Madre
python3 -m madre.main

# Logs output to console
# Server running on http://0.0.0.0:8001
```

---

## 4️⃣ TEST ENDPOINTS

### Health Check

```bash
curl -s http://127.0.0.1:8001/health -H "X-VX11-Token: vx11-local-token" | jq .
```

**Expected response:**
```json
{
  "module": "madre",
  "status": "ok",
  "version": "7.0",
  "time": "2025-01-08T14:30:45Z",
  "deps": {
    "switch": "ok",
    "hormiguero": "ok",
    "manifestator": "ok",
    "shub": "ok",
    "spawner": "unknown"
  }
}
```

---

### Chat Endpoint (Simple)

```bash
curl -X POST http://127.0.0.1:8001/madre/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "hello madre",
    "session_id": "test-session-1"
  }' | jq .
```

**Expected response:**
```json
{
  "response": "Plan executed. Mode: MADRE. Status: DONE",
  "session_id": "test-session-1",
  "intent_id": "intent-abc123",
  "plan_id": "plan-xyz789",
  "status": "DONE",
  "mode": "MADRE",
  "warnings": [],
  "targets": [],
  "actions": []
}
```

---

### Chat Endpoint (Audio Intent)

```bash
curl -X POST http://127.0.0.1:8001/madre/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "mix 3 stems with eq and compression",
    "session_id": "test-session-2"
  }' | jq .
```

**Expected response:** (status may be WAITING if Shub is not running)
```json
{
  "response": "Plan executed. Mode: AUDIO_ENGINEER. Status: DONE",
  "session_id": "test-session-2",
  "intent_id": "intent-def456",
  "plan_id": "plan-abc111",
  "status": "DONE",
  "mode": "AUDIO_ENGINEER",
  "warnings": ["fallback_parser_used"],
  "targets": ["shub"],
  "actions": []
}
```

---

### Control Endpoint (HIGH RISK)

```bash
curl -X POST http://127.0.0.1:8001/madre/control \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "shub",
    "action": "delete",
    "params": {}
  }' | jq .
```

**Expected response:** (HIGH risk action requires confirmation)
```json
{
  "status": "pending_confirmation",
  "confirm_token": "qvB3xYz_7k9mNpQrA2...",
  "reason": "Risk: HIGH. Provide this token to confirm.",
  "action_id": null
}
```

---

### List Plans

```bash
curl -s "http://127.0.0.1:8001/madre/plans?skip=0&limit=5" \
  -H "X-VX11-Token: vx11-local-token" | jq .
```

**Expected response:**
```json
{
  "plans": [],
  "skip": 0,
  "limit": 5,
  "note": "Full implementation requires DB query"
}
```

---

### Get Plan Details

Replace `PLAN_ID` with actual plan ID from chat response:

```bash
PLAN_ID="plan-xyz789"

curl -s "http://127.0.0.1:8001/madre/plans/$PLAN_ID" \
  -H "X-VX11-Token: vx11-local-token" | jq .
```

**Expected response:**
```json
{
  "task": {
    "uuid": "plan-xyz789",
    "name": "madre_plan",
    "module": "madre",
    "status": "completed",
    "result": "{...}"
  },
  "plan_json": "{...}",
  "intent_id": "intent-abc123",
  "mode": "MADRE"
}
```

---

### Confirm Plan (If Waiting)

```bash
PLAN_ID="plan-xyz789"
TOKEN="qvB3xYz_7k9mNpQrA2..."

curl -X POST "http://127.0.0.1:8001/madre/plans/$PLAN_ID/confirm" \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d "{\"confirm_token\": \"$TOKEN\"}" | jq .
```

**Expected response:**
```json
{
  "status": "confirmed",
  "plan_id": "plan-xyz789"
}
```

---

## 5️⃣ CHECK LOGS & FORENSICS

### Real-time logs

```bash
# If running in container
docker logs -f vx11-madre-1

# Or check forensic logs
tail -f forensic/madre/logs/$(date +%Y-%m-%d).log
```

**Sample output:**
```
2025-01-08T14:30:45.123456Z [INFO] startup:v7_initialized
2025-01-08T14:30:46.234567Z [INFO] chat:test-session-1:success
2025-01-08T14:30:50.345678Z [INFO] plan:plan-xyz789:executing_step_1
2025-01-08T14:30:52.456789Z [INFO] plan:plan-xyz789:step_1_ok
2025-01-08T14:30:54.567890Z [INFO] plan:plan-xyz789:status_done
```

### Database audit trail

```bash
sqlite3 data/runtime/vx11.db

# Query intents
SELECT intent_id, source, result_status, processed_by_madre_at FROM intents_log ORDER BY created_at DESC LIMIT 3;

# Query tasks
SELECT uuid, name, status, result FROM tasks WHERE module='madre' ORDER BY created_at DESC LIMIT 5;

# Query context
SELECT task_id, key, value FROM context WHERE task_id='plan-xyz789';

.quit
```

---

## 6️⃣ TROUBLESHOOTING

### Error: "Connection refused" on /health

**Cause:** Madre not running  
**Fix:**
```bash
# Check if service is running
docker ps | grep madre

# Or start manually
python3 -m madre.main
```

### Error: "401 Unauthorized"

**Cause:** Missing or invalid X-VX11-Token header  
**Fix:**
```bash
# Add token to request
curl -H "X-VX11-Token: vx11-local-token" ...
```

### Error: "plan_id not found"

**Cause:** Plan ID is invalid or expired  
**Fix:**
```bash
# Get actual plan ID from previous chat response
# Use that ID in subsequent requests
```

### Switch shows "unknown" in /health

**Cause:** Switch service is down (normal)  
**Fix:**
```bash
# Madre continues working with fallback parser
# No action needed
```

---

## 7️⃣ NEXT STEPS

### Development
- [ ] Review [madre/README.md](madre/README.md) (endpoints reference)
- [ ] Study [madre/core/models.py](madre/core/models.py) (data structures)
- [ ] Inspect [madre/main.py](madre/main.py) (implementation)
- [ ] Run all tests: `pytest tests/test_madre.py -v`

### Testing
- [ ] Run load test: `ab -n 100 -c 10 http://127.0.0.1:8001/health`
- [ ] Stress test: `for i in {1..100}; do curl ... ; done`
- [ ] Monitor memory: `docker stats vx11-madre-1`

### Deployment
- [ ] Review [docs/MADRE_v7_EXECUTION_REPORT.md](docs/MADRE_v7_EXECUTION_REPORT.md) (what was done)
- [ ] Check [docs/MADRE_v7_ROADMAP.md](docs/MADRE_v7_ROADMAP.md) (what's next)
- [ ] Plan Docker registry push
- [ ] Setup monitoring (Prometheus, Grafana)

---

## 📞 HELPFUL COMMANDS

### Get all tests status
```bash
pytest tests/test_madre.py -v --tb=short
```

### Compile & check syntax
```bash
python3 -m py_compile madre/core/*.py madre/main.py
```

### Check module imports
```bash
python3 -c "from madre.core import models, db, parser, policy, planner, runner, delegation; print('✅ All imports OK')"
```

### View test coverage
```bash
pytest tests/test_madre.py --cov=madre --cov-report=term-missing
```

### Format code
```bash
black madre/core/*.py madre/main.py
```

### Lint code
```bash
pylint madre/core/*.py madre/main.py
```

---

## ✅ QUICK CHECKLIST

Before going to production:

- [ ] All 25 tests pass
- [ ] `/health` endpoint responds
- [ ] `/madre/chat` works (simple message)
- [ ] `/madre/chat` works (audio intent)
- [ ] `/madre/control` works (low risk = accepted)
- [ ] `/madre/control` works (high risk = pending confirmation)
- [ ] Plans list returns OK
- [ ] Forensic logs created
- [ ] DB audit trail populated
- [ ] No Python errors in logs
- [ ] Memory stable (<512MB)
- [ ] Latency <2s (p99)

---

**Ready? Let's go!** 🚀

For detailed documentation, see:
- [madre/README.md](madre/README.md) — Full reference
- [docs/MADRE_v7_EXECUTION_REPORT.md](docs/MADRE_v7_EXECUTION_REPORT.md) — What was built
- [docs/MADRE_v7_ROADMAP.md](docs/MADRE_v7_ROADMAP.md) — Next phases

