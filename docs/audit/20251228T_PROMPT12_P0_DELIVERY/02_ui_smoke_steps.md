# P12 UI Smoke Test — Manual Verification Steps

## Environment
- URL: http://localhost:8000/operator/ui/
- Browser: Chrome/Firefox DevTools enabled
- Services: madre + redis + tentaculo_link (SOLO_MADRE policy)

---

## Step 1: Load Operator UI

1. Open browser to `http://localhost:8000/operator/ui/`
2. **Verify**: Page loads without NetworkError
3. **DevTools Network tab**: Check that requests go to `/operator/ui/` (same origin)

---

## Step 2: Check API Base URL

1. **DevTools Console**:
   ```javascript
   // Check if api client is using relative URLs
   fetch('/operator/api/status')
       .then(r => r.json())
       .then(d => console.log('Status:', d))
   ```

2. **Expected Network Tab entries**:
   - Request: `GET /operator/api/status` (NOT `http://localhost:8000/...`)
   - Response: 200 OK with JSON body containing `{"status": "ok", "policy": "solo_madre", ...}`

3. **Verify**: No CORS errors, same origin ✓

---

## Step 3: Click Chat Tab

1. Navigate to "Chat" tab in Operator UI
2. **Verify**: Chat panel loads without errors

---

## Step 4: Send Chat Message (solo_madre mode)

1. Type message: "Hello, what is your current mode?"
2. Click "Send"
3. **DevTools Network tab**:
   - Request: `POST /operator/api/chat`
   - Status: 200
   - Response body includes:
     ```json
     {
       "fallback_source": "local_llm_degraded",
       "model": "local_llm_degraded",
       "degraded": true,
       "response": "[LOCAL LLM DEGRADED] ..."
     }
     ```

4. **Verify**:
   - ✓ No NetworkError
   - ✓ Response shows `fallback_source` field (NEW in P12)
   - ✓ `degraded: true` (because switch offline in solo_madre)
   - ✓ Response acknowledges solo_madre mode

---

## Step 5: Check Security

1. **DevTools Sources tab**:
   - Open `services/api.ts`
   - Search for `BASE_URL`
   - **Verify**: Should show `const BASE_URL = import.meta.env.VITE_VX11_API_BASE_URL ?? ''`
   - **NOT**: `const BASE_URL = 'http://localhost:8000'`

2. **DevTools Storage → Cookies**:
   - **Verify**: No sensitive tokens in cookies (should use header `x-vx11-token`)

3. **DevTools Network → Request Headers**:
   - For any `/operator/api/*` request, verify:
     - `x-vx11-token: vx11-local-token` ✓
     - `Content-Type: application/json` ✓

---

## Step 6: Status Endpoint

1. **DevTools Console**:
   ```javascript
   fetch('/operator/api/status')
       .then(r => r.json())
       .then(d => {
           console.log('Status response:', d)
           console.log('Policy:', d.policy)
           console.log('Switch status:', d.optional_services.switch)
       })
   ```

2. **Expected output**:
   ```json
   {
     "status": "ok",
     "policy": "solo_madre",
     "core_services": {
       "madre": true,
       "redis": true,
       "tentaculo_link": true
     },
     "optional_services": {
       "switch": {"status": "OFF_BY_POLICY", "reason": "solo_madre policy"},
       ...
     }
   }
   ```

3. **Verify**: ✓ Policy shows `solo_madre`, Switch shows `OFF_BY_POLICY` (not error)

---

## Step 7: Verify No Hardcoded Localhost

1. **DevTools Network tab**:
   - Filter by XHR/Fetch
   - For each request, verify URL is **relative** (starts with `/`), NOT `http://localhost:...`

2. **Example**:
   - ✗ BAD: `http://localhost:8000/operator/api/chat`
   - ✓ GOOD: `/operator/api/chat`

---

## Step 8: Token Validation

1. **DevTools Console**:
   ```javascript
   // Make request without token header (should fail)
   fetch('/operator/api/status', {
       headers: { 'Content-Type': 'application/json' }
   })
   .then(r => {
       console.log('Status (no token):', r.status)
   })
   ```

2. **Expected**: 401 Unauthorized (or 403 Forbidden)

3. **Now with token**:
   ```javascript
   fetch('/operator/api/status', {
       headers: {
           'x-vx11-token': 'vx11-local-token',
           'Content-Type': 'application/json'
       }
   })
   .then(r => r.json())
   .then(d => console.log('Status (with token):', d))
   ```

4. **Expected**: 200 OK with status data

---

## Step 9: Rate Limit Test (Optional)

1. **DevTools Console**:
   ```javascript
   // Send 11 rapid chat requests (same session_id)
   for (let i = 0; i < 11; i++) {
       fetch('/operator/api/chat', {
           method: 'POST',
           headers: {
               'x-vx11-token': 'vx11-local-token',
               'Content-Type': 'application/json'
           },
           body: JSON.stringify({
               message: `Test message ${i}`,
               session_id: 'test_rate_limit'
           })
       })
       .then(r => console.log(`Request ${i}: ${r.status}`))
   }
   ```

2. **Expected pattern**:
   - Requests 1-10: 200 OK
   - Request 11: 429 Too Many Requests

---

## SUMMARY CHECKLIST

- [ ] Operator UI loads without NetworkError
- [ ] `/operator/api/*` requests are same-origin (relative URLs)
- [ ] Chat endpoint returns `fallback_source` field (NEW in P12)
- [ ] Degraded mode shows `degraded: true` + `fallback_source: local_llm_degraded`
- [ ] Policy endpoint shows `solo_madre` + `OFF_BY_POLICY` for optional services
- [ ] Token validation works (401 without, 200 with valid token)
- [ ] No hardcoded `http://localhost:...` URLs in requests
- [ ] Frontend code shows relative BASE_URL (not hardcoded)

**Status**: ✓ GATE PASSED

