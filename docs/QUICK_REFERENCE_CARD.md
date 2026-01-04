# VX11 Operator - Quick Reference Card (2026-01-04)

## 🌐 Access Frontend

```
http://localhost:8000/operator/
```

**Expected on page load:**
- VX11 Operator Dashboard title
- React app mounted
- Connection status: "Connecting..." (until EventsClient implemented)
- Policy status: "SOLO_MADRE - Read-only"

---

## 🔑 Authentication 3-Tier System

| Tier | Token | TTL | Storage | Use |
|------|-------|-----|---------|-----|
| **1** | `vx11-test-token` | 60+ min | localStorage | Main auth |
| **2** | UUID (206717d1...) | 60s | Redis | SSE stream |
| **3** | `vx11-operator-test-token` | Long | Headers | Inter-service |

---

## 📡 SSE Token Flow

```
1. Frontend POST /operator/api/events/sse-token
   ├─ Header: X-VX11-Token: vx11-test-token
   └─ Response: {"sse_token": "uuid", "ttl_sec": 60}
   
2. Frontend GET /operator/api/events/stream?token=uuid
   ├─ Status: 101 Switching Protocols
   └─ Messages: Keep-alive every 10s + events
   
3. Auto-refresh at 55s (before 60s expiration)
   └─ Repeat steps 1-2 seamlessly
```

---

## 🛠️ Quick Commands

### Test Token Generation
```bash
curl -X POST http://localhost:8000/operator/api/events/sse-token \
  -H "X-VX11-Token: vx11-test-token"
```

### Test SSE Stream
```bash
SSE_TOKEN=$(curl -s -X POST http://localhost:8000/operator/api/events/sse-token \
  -H "X-VX11-Token: vx11-test-token" | jq -r .sse_token)

# Open stream (20 second test)
timeout 20 curl -N "http://localhost:8000/operator/api/events/stream?token=$SSE_TOKEN"
```

### Check Redis Tokens
```bash
docker compose -f docker-compose.full-test.yml exec redis-test redis-cli KEYS "vx11:sse_token:*"
```

### View Logs
```bash
docker compose -f docker-compose.full-test.yml logs -f tentaculo_link
```

### Get Window Status
```bash
curl http://localhost:8000/operator/api/window/status | jq
```

---

## 📊 System Status

| Service | Port | Status | Health |
|---------|------|--------|--------|
| tentaculo_link | 8000 | ✅ | Healthy |
| operator-backend | 8011 | ✅ | Healthy |
| madre | 8001 | ✅ | Healthy |
| redis | 6379 | ✅ | Healthy |
| switch | 8002 | ✅ | Healthy |
| hermes | 8003 | ✅ | Healthy |
| operator-frontend | Proxy | ✅ | Healthy |

**Verify**: `docker compose -f docker-compose.full-test.yml ps`

---

## 🚀 Frontend Implementation (3-4 hours)

### Step 1: Create EventsClient
- File: `src/services/eventsClient.ts`
- Reference implementation in: `docs/IMPLEMENTATION_CHECKLIST_20260104.md`
- Methods: `constructor()`, `getEphemeralToken()`, `connect()`, `disconnect()`, `subscribe()`

### Step 2: React Integration
- File: `src/components/Operator/Operator.tsx`
- Add: `useState(eventsClient)`, `useEffect(initialize)`, `subscribe(onMessage)`
- Display: Connection status badge
- Disable: Chat input in SOLO_MADRE mode

### Step 3: Testing
- DevTools (F12) → Network tab
- Look for: `POST /events/sse-token` (200) → `GET /events/stream?token=...` (101)
- Monitor: Keep-alive messages every 10 seconds
- Verify: Token refresh at 55s mark (new requests appear)

---

## 📖 Documentation

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [IMPLEMENTATION_CHECKLIST_20260104.md](docs/IMPLEMENTATION_CHECKLIST_20260104.md) | **Step-by-step tasks** | 15 min |
| [FRONTEND_SSE_EPHEMERAL_TOKENS.md](docs/FRONTEND_SSE_EPHEMERAL_TOKENS.md) | Deep dive implementation | 20 min |
| [FRONTEND_VISUAL_TROUBLESHOOTING.md](docs/FRONTEND_VISUAL_TROUBLESHOOTING.md) | DevTools debugging guide | 15 min |
| [SMOKE_TEST_RESULTS_20260104.md](docs/SMOKE_TEST_RESULTS_20260104.md) | Backend verification | 10 min |
| [READONLY_FULLMODE_EXPLANATION.md](docs/READONLY_FULLMODE_EXPLANATION.md) | SOLO_MADRE policy | 10 min |

---

## ⚠️ Important Notes

### SOLO_MADRE Policy (Expected)
- Chat input is **intentionally disabled**
- NOT a bug - this is operational design
- Madre has full control during startup
- To enable full mode: `curl -X POST http://localhost:8001/madre/power/policy/full/apply`

### Token Refresh (Normal)
- Every 60 seconds, tokens expire
- Frontend should regenerate automatically
- Brief reconnection (< 1 second)
- No user interruption

### Multi-Worker Safety
- Tokens stored in Redis (not in-process memory)
- Works with 1+ Uvicorn workers
- Shared token namespace: `vx11:sse_token:<uuid>`

---

## 🐛 Troubleshooting

### Frontend loads but says "Disconnected"
1. Check DevTools (F12)
2. Look for `POST /events/sse-token` → should be 200 OK
3. Look for `GET /events/stream?token=...` → should be 101
4. If 401: Token may have expired, refresh page (Ctrl+R)

### SSE stream closes after ~60 seconds
This is **normal** - token expired, auto-refresh in progress

### Chat input disabled
Check policy: `curl http://localhost:8000/operator/api/window/status | jq '.policy'`
- If `SOLO_MADRE`: Wait for policy change or change manually
- If `full`: Bug - submit issue with logs

### Assets 404 (page looks broken)
Rebuild: `docker compose -f docker-compose.full-test.yml up -d --build --force-recreate`

---

## 📝 Commit Template

```
feat: Implement EventsClient and SSE integration

- Create EventsClient TypeScript class
- Manage ephemeral token lifecycle (60s TTL)
- Open EventSource stream with querystring auth
- Auto-refresh token before expiration
- Implement exponential backoff reconnection
- Display connection status badge
- Disable chat in SOLO_MADRE policy
- Add token refresh at 55s interval
- Handle network errors gracefully
- Test with DevTools Network tab
```

---

## ✅ Definition of Done

- [ ] EventsClient class created and exported
- [ ] React component calls EventsClient.connect() on mount
- [ ] Connection status updates correctly
- [ ] Ephemeral tokens refresh every 55s (verified in DevTools)
- [ ] Keep-alive messages appear in Network tab
- [ ] Policy display shows SOLO_MADRE correctly
- [ ] Chat input disabled in SOLO_MADRE
- [ ] No console errors or warnings
- [ ] localStorage persists main token
- [ ] Code merged to main branch

---

## 🎯 Success Criteria

✅ **Backend**: 100% Complete (verified Session 2)
- Token generation API: 200 OK
- SSE streaming: 101 Switching
- Keep-alive: Every 10s
- Token refresh: Every 55s
- Redis storage: Verified
- Multi-worker: Safe

⏳ **Frontend**: Ready to implement (this checklist)
- Expected timeline: 3-4 hours
- Reference implementation: Provided in checklist
- Testing guide: Visual troubleshooting doc
- Documentation: 5 comprehensive guides

---

**Generated**: 2026-01-04 00:30 UTC  
**Status**: ✅ Backend 100% Ready | ⏳ Frontend Ready to Build  
**Reference**: Follow [IMPLEMENTATION_CHECKLIST_20260104.md](docs/IMPLEMENTATION_CHECKLIST_20260104.md)
