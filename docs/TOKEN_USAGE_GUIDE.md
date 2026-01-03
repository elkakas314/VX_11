# VX11 Token Authentication Guide

## Overview

VX11 uses **X-VX11-Token** header authentication for all `/operator/api/*` endpoints. For browsers using EventSource API (which cannot send custom headers), token can be passed via **query parameter**.

**Default Token (Test)**: `vx11-test-token`

---

## For Server/Backend Clients

### Using Header (Recommended)

```bash
curl -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/status
```

### Using Query Parameter (Fallback)

```bash
curl "http://localhost:8000/operator/api/status?token=vx11-test-token"
```

### Python httpx Example

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/operator/api/status",
        headers={"X-VX11-Token": "vx11-test-token"}
    )
    print(response.json())
```

---

## For Browser/Frontend Clients

### EventSource API (SSE Streaming)

The browser EventSource API **cannot send custom headers**. Use query parameter instead:

```javascript
// Initialize SSE connection with token via query param
const token = localStorage.getItem("vx11_token") || "vx11-test-token";
const eventSource = new EventSource(
  `http://localhost:8000/operator/api/events?token=${token}&follow=true`
);

// Listen for service status events
eventSource.addEventListener('service_status', (event) => {
  const data = JSON.parse(event.data);
  console.log('Service status:', data);
  // {
  //   "service": "madre",
  //   "status": "up",
  //   "timestamp": "2026-01-03T00:56:44Z",
  //   "correlation_id": "..."
  // }
});

// Listen for feature toggle events
eventSource.addEventListener('feature_toggle', (event) => {
  const data = JSON.parse(event.data);
  console.log('Feature toggled:', data);
  // {
  //   "feature": "chat",
  //   "status": "on",
  //   "timestamp": "2026-01-03T00:56:44Z",
  //   "correlation_id": "..."
  // }
});

// Listen for heartbeat (connection keep-alive)
eventSource.addEventListener('heartbeat', (event) => {
  const data = JSON.parse(event.data);
  console.log('Heartbeat:', data.timestamp);
});

// Handle errors
eventSource.onerror = (error) => {
  console.error('SSE Connection error:', error);
  eventSource.close();
};

// Close when done
// eventSource.close();
```

### Storing Token in LocalStorage

```javascript
// On login/authentication
function setToken(token) {
  localStorage.setItem("vx11_token", token);
}

// On page load
function getStoredToken() {
  return localStorage.getItem("vx11_token") || "vx11-test-token";
}

// Clear on logout
function clearToken() {
  localStorage.removeItem("vx11_token");
}
```

### Fetch API (for non-streaming endpoints)

```javascript
const token = localStorage.getItem("vx11_token") || "vx11-test-token";

// Option 1: Header (recommended)
const response = await fetch("http://localhost:8000/operator/api/status", {
  headers: {
    "X-VX11-Token": token
  }
});

// Option 2: Query parameter
const response = await fetch(
  `http://localhost:8000/operator/api/status?token=${token}`
);

const data = await response.json();
console.log(data);
```

---

## Configuration

### Docker Compose

Token is set in `docker-compose.yml`:

```yaml
services:
  tentaculo_link:
    environment:
      - VX11_TENTACULO_LINK_TOKEN=vx11-test-token
      - VX11_EVENTS_ENABLED=1  # Enable SSE events
```

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `VX11_TENTACULO_LINK_TOKEN` | Token for authentication | `vx11-test-token` |
| `VX11_EVENTS_ENABLED` | Enable/disable events endpoint | `1` or `true` |
| `ENABLE_AUTH` | Enable/disable auth checks globally | `true` |

---

## Endpoints

### Available Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check (public) |
| `/operator/api/status` | GET | Yes | System status |
| `/operator/api/events` | GET | Yes | Event polling (JSON) |
| `/operator/api/events?follow=true` | GET | Yes | Event streaming (SSE) |

### Response Formats

#### JSON Endpoint
```bash
curl -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/status
```

Response:
```json
{
  "status": "operational",
  "services": {
    "madre": "up",
    "switch": "up"
  },
  "timestamp": "2026-01-03T00:56:44Z"
}
```

#### SSE Endpoint
```bash
curl -N "http://localhost:8000/operator/api/events?token=vx11-test-token&follow=true"
```

Response:
```
event: service_status
data: {"service":"madre","status":"up","timestamp":"2026-01-03T00:56:44Z"}

event: feature_toggle
data: {"feature":"chat","status":"on","timestamp":"2026-01-03T00:56:44Z"}

:heartbeat
```

---

## Error Responses

### 401 Unauthorized
```json
{"detail": "auth_required"}
```
**Cause**: Token missing or not provided
**Solution**: Add header or query param with valid token

### 403 Forbidden
```json
{"detail": "forbidden"}
```
**Cause**: Token invalid or wrong
**Solution**: Check token value against configured token

### 503 Feature Disabled
```json
{
  "error": "feature_disabled",
  "flag": "VX11_EVENTS_ENABLED",
  "status_code": 503
}
```
**Cause**: Feature flag not enabled
**Solution**: Set `VX11_EVENTS_ENABLED=1` in environment

---

## Testing

### Test Auth (Query Param)

```bash
# Without token (should fail)
curl http://localhost:8000/operator/api/status

# With header token (should pass)
curl -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/status

# With query param token (should pass)
curl "http://localhost:8000/operator/api/status?token=vx11-test-token"
```

### Test SSE Stream

```bash
# Direct curl (will stream events)
timeout 5 curl -N \
  "http://localhost:8000/operator/api/events?token=vx11-test-token&follow=true"

# Output (until timeout):
# event: service_status
# data: {...}
# event: feature_toggle
# data: {...}
```

---

## Single Entrypoint

All requests go through **gateway on port 8000** (tentaculo_link):

```
Browser/Client
    ↓
:8000/operator/api/*  (gateway - validates auth)
    ↓
Upstream services (operator-backend, madre, etc.)
```

---

## Security Notes

- Tokens are **environment-configured** (no hardcoding)
- Auth checks happen at **middleware level** (before endpoint execution)
- Both **header** and **query param** support same token validation logic
- Query param used only for EventSource API (browser limitation)
- In production, use HTTPS to protect token in URLs

---

## References

- **SSE Spec**: https://html.spec.whatwg.org/multipage/server-sent-events.html
- **EventSource API**: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- **FastAPI Docs**: https://fastapi.tiangolo.com/
