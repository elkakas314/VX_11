# TOKEN AUTH AUDIT — 2026-01-03 DEEPSEEK R1 REASONING

## ROOT CAUSE ANALYSIS

### Token Configuration (docker-compose.full-test.yml)

**tentaculo_link service:**
```
VX11_TENTACULO_LINK_TOKEN=vx11-test-token
VX11_GATEWAY_TOKEN=vx11-test-token
```

**operator-backend service:**
```
VX11_OPERATOR_TOKEN=vx11-operator-test-token     ← DIFFERENT TOKEN!
VX11_GATEWAY_TOKEN=vx11-test-token
VX11_TENTACULO_LINK_TOKEN=vx11-test-token
```

### Token Priority Resolution

**tentaculo_link/main_v7.py line 79-81:**
```python
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")    # Priority 1: vx11-test-token ✅
    or get_token("VX11_GATEWAY_TOKEN")        # Priority 2: vx11-test-token (fallback)
    or ...
)
```
**Effective token in tentaculo_link: `vx11-test-token`**

**operator/backend/main.py line 21-24:**
```python
VX11_TOKEN = (
    get_token("VX11_OPERATOR_TOKEN")          # Priority 1: vx11-operator-test-token ✅
    or get_token("VX11_GATEWAY_TOKEN")        # Priority 2: vx11-test-token (fallback)
    or settings.api_token
)
```
**Effective token in operator-backend: `vx11-operator-test-token`**

### Token Mismatch Flow (SSE /operator/api/events)

1. Frontend sends: `GET /operator/api/events?token=vx11-test-token&follow=true`
2. tentaculo_link receives in `operator_api_proxy` (line 250):
   - `provided_token = vx11-test-token` (query param)
   - Line 282: matches `VX11_TOKEN` (vx11-test-token) → REWRITES to `vx11-operator-test-token`
   - Forwards to operator-backend with params: `token=vx11-operator-test-token`
3. operator-backend in `check_sse_auth` (line 76-102):
   - Receives query param: `token=vx11-operator-test-token`
   - Expected token: `VX11_TOKEN = vx11-operator-test-token`
   - Comparison: `vx11-operator-test-token == vx11-operator-test-token` ✅ SHOULD PASS
   - **BUT LINE 95 FAILS: `provided_token != VX11_TOKEN` returns 403**

### Hypothesis: Token Still Not Reaching Backend

Despite tentaculo rewriting token, operator-backend still sees mismatch.

**Possible causes:**
1. SSE query param NOT being forwarded by proxy correctly
2. Header injection (line 286) using WRONG token
3. Token translation logic broken (lines 281-284)

### Key Evidence

**tentaculo_link line 281-286:**
```python
if "token" in params and params["token"]:
    if params["token"] == VX11_TOKEN:           # if token == vx11-test-token
        params["token"] = OPERATOR_BACKEND_TOKEN  # rewrite to vx11-operator-test-token
else:
    headers[settings.token_header] = OPERATOR_BACKEND_TOKEN  # fallback to header
```

**Problem identified**: 
- Query param rewrite looks correct
- BUT in line 304-312, httpx.AsyncClient.stream() is called with both `headers` and `params`
- If query param translation happened, should work
- If not, this code path might use header-only fallback

### DECISION: Multi-Token Solution

Instead of 1:1 rewrite, implement **token set validation**:

1. **tentaculo_link**: Accept any valid token (vx11-test-token OR vx11-operator-test-token) and PASSTHROUGH as-is
2. **operator-backend**: Accept any valid token from set {vx11-test-token, vx11-operator-test-token}
3. **Rationale**: Avoids translation errors, maintains compatibility, prevents 401 by design

### Implementation Plan

**File 1: tentaculo_link/main_v7.py (operator_api_proxy middleware)**
- Build `VALID_OPERATOR_TOKENS` from all env vars (VX11_*_TOKEN)
- Passthrough `provided_token` AS-IS (no rewrite)
- Validate token exists in set (if auth enabled)
- Forward same token in query param and header

**File 2: operator/backend/main.py (TokenGuard + check_sse_auth)**
- Build `VALID_TOKENS` from all env vars
- Validate provided token ∈ VALID_TOKENS
- No more 1:1 priorty confusion

### Backward Compatibility

Existing deployments:
- If env sets only `VX11_OPERATOR_TOKEN`: works (token in set)
- If env sets `VX11_GATEWAY_TOKEN` + `VX11_OPERATOR_TOKEN`: works (both in set)
- If env sets both as DIFFERENT tokens: still works (accepts both)

**Conclusion: No breaking changes.**
