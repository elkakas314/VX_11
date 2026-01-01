# 🚀 RUNBOOK — OPERATOR V7 (Frontend + Chat Window + Events)
**Version**: 7.0.0 | **Last Updated**: 2026-01-01 | **Status**: PRODUCTION READY

---

## 📌 QUICK START

### 1. Default Stack (solo_madre)
```bash
# Start with default policy (read-only, no window)
docker compose -f docker-compose.full-test.yml up -d
docker compose ps
# Expected: madre, tentaculo_link, operator-backend, operator-frontend (9 services)
```

### 2. Access Operator UI
```bash
# Open browser to
http://localhost:8000/operator/

# In UI:
# - Chat tab: shows "⊘ solo_madre" badge
# - Hormiguero tab: shows "solo_madre: events unavailable (open window to enable)"
# - "↑ Open Window" button visible in header
```

### 3. Open Chat Window (from UI or API)
```bash
# Via UI:
# - Click "↑ Open Window" button
# - Confirm: button changes to "↓ Close Window"
# - Chat now works (degraded mode if Switch unavailable)

# Via API:
TOKEN="vx11-test-token"
curl -X POST -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"services":["switch","hermes"]}' \
  http://localhost:8000/operator/api/chat/window/open | jq
# Returns: window_id, deadline, ttl_remaining_sec
```

### 4. Send Chat Message
```bash
# Via UI:
# - Type message in input box
# - Press Enter or click button
# - Response appears (may be degraded if Switch off)

# Via API:
curl -X POST -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","session_id":"test-123"}' \
  http://localhost:8000/operator/api/chat | jq
```

### 5. Close Chat Window
```bash
# Via UI:
# - Click "↓ Close Window" button
# - Reverts to "⊘ solo_madre"

# Via API:
curl -X POST -H "X-VX11-Token: $TOKEN" \
  http://localhost:8000/operator/api/chat/window/close | jq
```

---

## 🔐 AUTHENTICATION

### Token Requirement
- **All** `/operator/api/*` endpoints require `X-VX11-Token` header
- Test token (dev): `vx11-test-token`
- Without token: HTTP 401 Unauthorized

```bash
# ✅ Correct
curl -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/chat/window/status

# ❌ Will fail (401)
curl http://localhost:8000/operator/api/chat/window/status
```

---

## 📊 CORE ENDPOINTS

### Window Management
| Endpoint | Method | Purpose | Requires Window |
|----------|--------|---------|-----------------|
| `/operator/api/chat/window/status` | GET | Check window state | No |
| `/operator/api/chat/window/open` | POST | Open window, start services | No |
| `/operator/api/chat/window/close` | POST | Close window, stop services | Yes |

### Chat Operations
| Endpoint | Method | Purpose | Requires Window |
|----------|--------|---------|-----------------|
| `/operator/api/chat` | POST | Send message | Yes* |
| `/operator/api/events` | GET | Stream events (Hormiguero) | Optional |

*Can work in solo_madre (degraded), but full functionality requires window

### Settings & Status
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/operator/api/status` | GET | Health check |
| `/operator/api/settings` | GET/POST | UI preferences |
| `/operator/api/modules` | GET | List available modules |
| `/operator/api/scorecard` | GET | Performance metrics |

---

## ⚠️ ERROR SEMANTICS

### 401 Unauthorized
```json
{"error": "auth_required", "status_code": 401}
```
**Action**: Provide `X-VX11-Token` header

### 403 OFF_BY_POLICY
```json
{"status": "OFF_BY_POLICY", "message": "solo_madre policy active", "status_code": 403}
```
**Action**: NOT an error. Expected in solo_madre mode. Open window to enable.

### 400 Bad Request
```json
{"status": "error", "error_code": "invalid_request", "error_msg": "..."}
```
**Action**: Check request body/parameters

### 500 Server Error
```json
{"error": "server_error", "detail": "..."}
```
**Action**: Check service logs, restart if needed

---

## 🔍 DEBUGGING

### Check Window Status
```bash
TOKEN="vx11-test-token"
curl -s -H "X-VX11-Token: $TOKEN" \
  http://localhost:8000/operator/api/chat/window/status | jq
```

**Expected output in solo_madre**:
```json
{
  "status": "none",
  "window_id": null,
  "mode": "solo_madre"
}
```

**Expected output with window open**:
```json
{
  "status": "open",
  "window_id": "270d9668-...",
  "deadline": "2026-01-01T02:49:43.794307+00:00Z",
  "ttl_remaining_sec": 408,
  "active_services": ["switch", "hermes", "redis", "madre"],
  "mode": "window_active"
}
```

### Check Services Health
```bash
docker compose -f docker-compose.full-test.yml ps

# Look for:
# - tentaculo_link (healthy) = :8000 entrypoint
# - madre (healthy) = window gating + routing
# - operator-backend (healthy) = API business logic
# - operator-frontend (healthy) = UI static files
```

### View Logs
```bash
# Tentaculo (entrypoint, routing)
docker logs vx11-tentaculo-link-test -f

# Madre (window gating, power management)
docker logs vx11-madre-test -f

# Operator backend (chat, events)
docker logs vx11-operator-backend-test -f

# Frontend browser console
# Open DevTools (F12) → Console tab
# Look for: Network tab to see API requests with token
```

---

## 🛠️ COMMON TASKS

### Task: Why does chat show "degraded mode"?
**Answer**: Switch service is not running (expected in solo_madre). 
- To enable Switch: Open window → button "↑ Open Window"
- Window will start Switch + Hermes on demand

### Task: I see "solo_madre: events unavailable" in Hormiguero
**Answer**: Events require window. It's not an error.
- Open window to populate Hormiguero with events
- In solo_madre: no events are generated

### Task: Window won't open, shows error
**Answer**: Check logs:
```bash
docker logs vx11-tentaculo-link-test | grep -i "window"
docker logs vx11-madre-test | grep -i "window"
```

### Task: Token is wrong, getting 401
**Answer**: Verify token:
```bash
# In dev:
echo $VX11_TOKEN  # Should be set in docker-compose

# In container:
docker exec vx11-tentaculo-link-test env | grep TOKEN
```

---

## 📋 VALIDATION CHECKLIST

Before deploying to production:

- [ ] `docker compose ps` shows all 9 services healthy
- [ ] `curl -H "X-VX11-Token: ..." http://localhost:8000/operator/api/status` returns 200
- [ ] Open window button appears in UI
- [ ] Chat works with window open
- [ ] Window closes cleanly
- [ ] Hormiguero shows events when window open, "unavailable" when closed
- [ ] No 403-loops in DevTools console
- [ ] Post-task maintenance run: `curl -X POST http://localhost:8001/madre/power/maintenance/post_task`

---

## 🚀 PRODUCTION DEPLOYMENT

1. **Build operator-frontend with latest code**
   ```bash
   docker compose build operator-frontend
   ```

2. **Start full stack**
   ```bash
   docker compose -f docker-compose.full-test.yml up -d
   ```

3. **Verify health**
   ```bash
   curl -H "X-VX11-Token: $TOKEN" http://localhost:8000/operator/api/status
   ```

4. **Run smoke test** (5 steps)
   ```bash
   # See QUICK START section above
   ```

5. **Monitor logs**
   ```bash
   docker logs -f vx11-tentaculo-link-test
   docker logs -f vx11-madre-test
   ```

---

## 🔗 RELATED DOCS

- Architecture: `OPERATOR_UI_ARCHITECTURE_PHASE4.md`
- E2E Testing: `OPERATOR_E2E_COMPLETION_20260101.md`
- Frontend Fix: `OPERATOR_FRONTEND_V7_FIX_REPORT_20260101.md`
- Power Windows: `POWER_MANAGER_HARDENING_PHASE1.md`

---

**Last Update**: 2026-01-01 | **Author**: VX11 Architect + QA | **Status**: PRODUCTION READY ✅
