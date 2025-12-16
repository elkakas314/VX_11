# VX11 Runtime Truth Report

**Generated:** 2025-12-16T02:29:15.506620Z

## Service Status Matrix

| Service | Port | Status | HTTP Code | Latency (ms) | Endpoint | Snippet |
|---------|------|--------|-----------|--------------|----------|---------|
| tentaculo_link | 8000 | ✓ OK | 200 | 5 | /health | {"status":"ok","module":"tenta... |
| madre | 8001 | ✓ OK | 200 | 15 | /health | {"module":"madre","status":"ok... |
| switch | 8002 | ✓ OK | 200 | 4 | /health | {"status":"ok","module":"switc... |
| hermes | 8003 | ✓ OK | 200 | 4 | /health | {"status":"ok","module":"herme... |
| hormiguero | 8004 | ✓ OK | 200 | 5 | /health | {"status":"ok","service":"horm... |
| manifestator | 8005 | ✓ OK | 200 | 14 | /health | {"status":"healthy","service":... |
| mcp | 8006 | ✓ OK | 200 | 3 | /health | {"status":"ok"}... |
| shubniggurath | 8007 | ✗ BROKEN | — | — | — | —... |
| spawner | 8008 | ✓ OK | 200 | 6 | /health | {"status":"ok"}... |
| operator | 8011 | ✓ OK | 200 | 9 | /health | {"ok":true,"status":"ok","modu... |

## Summary
- **OK:** 9/10
- **BROKEN:** 1/10
- **UNKNOWN:** 0/10

## Details
```json
[
  {
    "name": "tentaculo_link",
    "port": 8000,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 5,
    "endpoint_ok": "/health",
    "snippet": "{\"status\":\"ok\",\"module\":\"tentaculo_link\",\"version\":\"7.0\"}"
  },
  {
    "name": "madre",
    "port": 8001,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 15,
    "endpoint_ok": "/health",
    "snippet": "{\"module\":\"madre\",\"status\":\"ok\",\"version\":\"v2\"}"
  },
  {
    "name": "switch",
    "port": 8002,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 4,
    "endpoint_ok": "/health",
    "snippet": "{\"status\":\"ok\",\"module\":\"switch\",\"active_model\":\"general-7b\",\"warm_model\":\"audio-engineering\",\"queue"
  },
  {
    "name": "hermes",
    "port": 8003,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 4,
    "endpoint_ok": "/health",
    "snippet": "{\"status\":\"ok\",\"module\":\"hermes\"}"
  },
  {
    "name": "hormiguero",
    "port": 8004,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 5,
    "endpoint_ok": "/health",
    "snippet": "{\"status\":\"ok\",\"service\":\"hormiguero\"}"
  },
  {
    "name": "manifestator",
    "port": 8005,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 14,
    "endpoint_ok": "/health",
    "snippet": "{\"status\":\"healthy\",\"service\":\"manifestator\"}"
  },
  {
    "name": "mcp",
    "port": 8006,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 3,
    "endpoint_ok": "/health",
    "snippet": "{\"status\":\"ok\"}"
  },
  {
    "name": "shubniggurath",
    "port": 8007,
    "status": "BROKEN",
    "http_code": null,
    "latency_ms": null,
    "endpoint_ok": null,
    "snippet": null
  },
  {
    "name": "spawner",
    "port": 8008,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 6,
    "endpoint_ok": "/health",
    "snippet": "{\"status\":\"ok\"}"
  },
  {
    "name": "operator",
    "port": 8011,
    "status": "OK",
    "http_code": 200,
    "latency_ms": 9,
    "endpoint_ok": "/health",
    "snippet": "{\"ok\":true,\"status\":\"ok\",\"module\":\"operator\",\"version\":\"7.0\"}"
  }
]
```