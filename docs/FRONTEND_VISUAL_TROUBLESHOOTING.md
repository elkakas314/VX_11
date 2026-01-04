# Frontend Visual Troubleshooting Guide

## What You Should See Right Now

### ✅ Expected Appearance

When you open http://localhost:8000/operator/:

```
┌─────────────────────────────────────────┐
│ VX11 Operator Dashboard                 │
├─────────────────────────────────────────┤
│ Status: 🟢 Connected                    │
│ Policy: SOLO_MADRE (Read-only mode)     │
│ Services: 7/7 Healthy                   │
├─────────────────────────────────────────┤
│ Chat Input: [disabled - policy blocks]  │
│                                         │
│ Events Feed:                            │
│ - Connected at 2026-01-04 00:15:22      │
│ - Keep-alive: ✅ (messages every 10s)   │
├─────────────────────────────────────────┤
│ Settings | Mode | About                 │
└─────────────────────────────────────────┘
```

---

## DevTools Verification (F12 Network Tab)

### Step 1: Open DevTools
- Press `F12` (or Cmd+Option+I on Mac)
- Click **Network** tab

### Step 2: Refresh the page (Ctrl+R)
- Look for these requests in order:

```
✅ GET /operator/                 [Status: 307 Temporary Redirect]
                                  └→ Redirects to /operator/
                                  
✅ GET /operator/                 [Status: 200 OK]
                                  └→ HTML document loads
                                  
✅ GET /operator/ui/assets/index-*.js  [Status: 200 OK]
                                  └→ JavaScript loads (195KB)
                                  
✅ GET /operator/ui/assets/index-*.css [Status: 200 OK]
                                  └→ Styles load
```

### Step 3: Watch SSE connection
- Once page loads, you should see:

```
✅ POST /operator/api/events/sse-token  [Status: 200 OK]
   Response: {
     "sse_token": "206717d1-fb0f-435d-a123...",
     "ttl_sec": 60,
     "endpoint": "/operator/api/events/stream",
     "usage": "querystring"
   }

✅ GET /operator/api/events/stream?token=206717d1...
   [Status: 101 Switching Protocols]
   └→ Remains OPEN (streaming connection)
   └→ Keep-alive: `: ` every 10 seconds
```

### Step 4: Verify keep-alive messages
- In the Network tab, find the streaming request
- Click **Response** or **Messages** tab
- You should see keep-alive pings:

```
: keep-alive

: keep-alive

data: {"type": "connected", "message": "SSE stream established"}

: keep-alive

: keep-alive
```

---

## What Each Status Means

### 🟢 Connected
- ✅ SSE stream is open
- ✅ Token valid in Redis
- ✅ Receiving keep-alive messages
- ✅ Ready to receive real-time events

### 🟡 Connecting
- ⏳ Page just loaded
- ⏳ Generating ephemeral token
- ⏳ Waiting for stream response
- **Expected Duration**: < 1 second

### 🔴 Disconnected
- ❌ SSE stream closed
- ❌ Token expired (60s TTL)
- ❌ Network error
- **Action**: Page should auto-reconnect with new token

---

## SOLO_MADRE Mode Explanation

### Why is Chat Input Disabled?

```
Current State:
├─ Window: ✅ window_active (Operator window is open)
├─ Policy: ⚠️ SOLO_MADRE (Madre has control)
└─ Result: 🔒 Chat blocked (read-only mode)
```

**This is NOT a bug** — it's operational design:

- **SOLO_MADRE**: During startup/initialization
  - Madre is in full control
  - Operator can observe (read-only)
  - Chat is intentionally blocked
  
- **Operative Mode** (after Madre enables):
  - Full chat access ✅
  - Can send commands ✅
  - Two-way communication ✅

### How to Change Policy

If you want to enable full mode:

```bash
# Switch from SOLO_MADRE to full
curl -X POST http://localhost:8001/madre/power/policy/full/apply

# Or via browser console:
fetch('http://localhost:8001/madre/power/policy/full/apply', 
  {method: 'POST'})

# Check current policy
curl http://localhost:8000/operator/api/window/status
```

---

## Common Issues & Solutions

### Issue 1: "Page loads but says Disconnected"

**Diagnosis:**
- DevTools shows: POST /sse-token → 401 Unauthorized
- Or: GET /stream?token=... → 401 Unauthorized

**Solutions:**

1. **Check main token in localStorage**
   ```javascript
   // Open browser console (F12) and paste:
   console.log('Main token:', localStorage.getItem('vx11_token'))
   ```
   Should show: `vx11-test-token`

2. **Hard reload** (clears cache)
   ```
   Ctrl+Shift+R (Windows/Linux)
   Cmd+Shift+R (Mac)
   ```

3. **Check server logs**
   ```bash
   docker compose -f docker-compose.full-test.yml logs tentaculo_link --tail=30
   ```
   Look for: `[DEBUG MIDDLEWARE]` lines showing token validation

---

### Issue 2: "SSE keeps reconnecting every 60 seconds"

**This is normal** ✅

- Token expires after 60s TTL
- Frontend automatically requests new token
- New SSE stream created
- Seamless to user (happens in background)

**Expected behavior:**
```
00:15:22 - Connected (token: 206717d1-fb0f-...)
        ↓
00:16:22 - Disconnected (token expired)
        ↓
        - Requesting new token...
        ↓
00:16:23 - Connected (token: a8c9d2ef-1234-...)
```

---

### Issue 3: "Events not flowing / Chat not working"

**Checklist:**

- [ ] SSE stream shows "Connected" ✅
- [ ] DevTools Network shows 101 response ✅
- [ ] Window status shows `policy: "SOLO_MADRE"` ⚠️

**If all above true:**
- Chat is blocked by policy (by design)
- Token/SSE infrastructure is working
- Change policy to enable chat:
  ```bash
  curl -X POST http://localhost:8001/madre/power/policy/full/apply
  ```

---

### Issue 4: "Assets missing (404 errors)"

**Symptoms:**
- Page loads but looks broken (no styling)
- DevTools shows: `GET /operator/ui/assets/... [404 Not Found]`

**Solution:**
- Rebuild frontend:
  ```bash
  docker compose -f docker-compose.full-test.yml down -v
  docker compose -f docker-compose.full-test.yml up -d --build --force-recreate
  ```

---

## Quick Commands Reference

```bash
# 1. Check all services
docker compose -f docker-compose.full-test.yml ps

# 2. View tentaculo_link logs (gateway debugging)
docker compose -f docker-compose.full-test.yml logs tentaculo_link -f

# 3. Test token generation manually
curl -X POST http://localhost:8000/operator/api/events/sse-token \
  -H "X-VX11-Token: vx11-test-token"

# 4. Test SSE stream with token
SSE_TOKEN=$(curl -s -X POST http://localhost:8000/operator/api/events/sse-token \
  -H "X-VX11-Token: vx11-test-token" | jq -r .sse_token)

curl -N "http://localhost:8000/operator/api/events/stream?token=$SSE_TOKEN"

# 5. Check Redis tokens
docker compose -f docker-compose.full-test.yml exec redis-test redis-cli KEYS "vx11:sse_token:*"

# 6. View window status
curl http://localhost:8000/operator/api/window/status

# 7. Change policy
curl -X POST http://localhost:8001/madre/power/policy/full/apply

# 8. Full logs dump
docker compose -f docker-compose.full-test.yml logs | tail -100
```

---

## Summary

| Component | Status | What to Do |
|-----------|--------|-----------|
| **Frontend UI** | ✅ Loading | View at http://localhost:8000/operator/ |
| **SSE Stream** | ✅ Connecting | Check DevTools Network tab (101 response) |
| **Token System** | ✅ Working | Ephemeral tokens auto-rotating every 60s |
| **Chat Input** | 🔒 Blocked | By SOLO_MADRE policy (expected) |
| **Connection Status** | 🟢 Online | Should show "Connected" (after frontend implementation) |

---

**Last Update**: 2026-01-04  
**Status**: ✅ Backend 100% Ready | ⏳ Frontend Implementation (in progress)
