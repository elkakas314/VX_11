# FASE 0 — DISCOVERY BASELINE

**Date**: 2026-01-02  
**Goal**: Map entrypoint (8000) vs internal hermes (8003), identify missing proxy routes.

---

## A) ENTRYPOINT STATUS (port 8000)

✅ **Health**: `GET http://localhost:8000/health`  
```json
{"status":"ok","module":"tentaculo_link","version":"7.0"}
```

### Existing Hermes Proxies on Entrypoint (8000)

| Path | Method | Status | Notes |
|------|--------|--------|-------|
| `/vx11/hermes/health` | GET | ✅ EXISTS | Calls upstream `http://hermes:8003/health` |
| `/vx11/hermes/discover` | POST | ✅ EXISTS | Window policy + DB mock discovery |
| `/vx11/hermes/catalog` | GET | ✅ EXISTS | Window policy + DB read |
| `/hermes/execute` | POST | ✅ EXISTS | Direct proxy (no window check?) |
| `/hermes/get-engine` | POST | ✅ EXISTS | Direct proxy (no window check?) |

### Missing Proxy on Entrypoint (8000)

| Path | Method | Status | Upstream | Notes |
|------|--------|--------|----------|-------|
| `/vx11/hermes/models/pull` | POST | ❌ **404** | `http://hermes:8003/hermes/models/pull` | **PROBLEM**: Endpoint exists on 8003 but NOT exposed on 8000 |

**Test Result**:
```bash
$ curl -X POST http://localhost:8000/vx11/hermes/models/pull \
  -H "X-VX11-Token: vx11-local-token" \
  -d '{"model_id":"test"}'

→ 404 Not Found
```

---

## B) UPSTREAM HERMES (port 8003 — internal)

### Docker Network URL
- **Hostname**: `hermes`
- **Port**: `8003`
- **Full URL**: `http://hermes:8003`
- **Config source**: `config/settings.py` → `_resolve_docker_url("hermes", 8003)`

### Endpoint: POST /hermes/models/pull

**Location**: `switch/hermes/main.py:734`

**Signature**:
```python
@app.post("/hermes/models/pull")
async def models_pull(req: ModelPullRequest, _: bool = Depends(_token_guard)):
```

**Request Schema** (`ModelPullRequest`):
```json
{
  "model_id": "string (required)",
  "token": "string|null (optional - HF token)",
  "cache_dir": "string|null (optional - download cache path)"
}
```

**Gates**:
1. `_token_guard`: X-VX11-Token validation (standard)
2. `HERMES_ALLOW_DOWNLOAD=1` environment variable (window policy gate)

**Response** (success 200):
```json
{
  "status": "ok",
  "model_id": "string",
  "registered_id": "int",
  "path": "string",
  "size_bytes": "int",
  "downloaded_at": "ISO timestamp",
  "out_dir": "string"
}
```

**Errors**:
- `403`: `HERMES_ALLOW_DOWNLOAD != 1` or download disabled
- `500`: Download/registration failed
- `422`: Invalid request schema

---

## C) WINDOW POLICY PATTERN (Existing in tentaculo_link)

Used in `/vx11/hermes/discover` and `/vx11/hermes/catalog`:

```python
window_manager = get_window_manager()
window_status = window_manager.get_window_status("hermes")
if not window_status.get("is_open", False):
    return {
        "status": "ERROR",
        "error": "off_by_policy",
        "hint": 'POST /vx11/window/open {"target":"hermes", "ttl_seconds":300}'
    }
```

---

## D) PROXY PATTERN (Existing in tentaculo_link)

Example from `/hermes/get-engine`:

```python
@app.post("/hermes/get-engine", tags=["proxy-hermes"])
async def proxy_hermes_get_engine(body: dict, _: bool = Depends(token_guard)):
    """Proxy: POST /hermes/get-engine (forward to Hermes service)"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://hermes:8003/hermes/get-engine",
                json=body,
                headers=AUTH_HEADERS,
            )
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail="hermes_proxy_error")
```

---

## E) SUMMARY: WHAT'S MISSING

**Problem**: `/vx11/hermes/models/pull` endpoint exists on hermes (8003) but is **NOT exposed** on entrypoint (8000).

**Solution**: Add proxy route in `tentaculo_link/main_v7.py`:
- Path: `POST /vx11/hermes/models/pull`
- Upstream: `http://hermes:8003/hermes/models/pull`
- Gates:
  1. Token guard (X-VX11-Token)
  2. **NEW**: Window policy check (hermes window must be open)
  3. Forward HERMES_ALLOW_DOWNLOAD status (or proxy directly)

**Implementation Plan** (FASE 1):
1. Add `/vx11/hermes/models/pull` proxy in tentaculo_link/main_v7.py (after line 1491 or with other hermes proxies)
2. Use window policy (existing pattern)
3. Forward request body + headers to `http://hermes:8003/hermes/models/pull`
4. Return response as-is (JSON or error)
5. Add logging with correlation_id

---

## F) INVARIANT CHECK

✅ **SINGLE ENTRYPOINT**: All client traffic goes to port 8000 (tentaculo_link)  
✅ **SOLO_MADRE**: No service spawning, hermes is subordinate  
✅ **WINDOW POLICY**: Hermes requires window to be open (discover/catalog already use it)  
✅ **NO SECRETS IN LOGS**: HF_TOKEN passed in request body (not headers by default)  
✅ **TOKEN GUARD**: X-VX11-Token required on all /vx11/* endpoints

---

## G) NEXT STEPS

→ **FASE 1**: Implement `/vx11/hermes/models/pull` proxy in tentaculo_link/main_v7.py  
→ **FASE 2**: Write E2E tests (no direct 8003 calls)  
→ **FASE 3**: Verify switch + hermes integrity  
→ **FASE 4**: Commit & push
