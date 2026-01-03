# Frontend EventSource Implementation Guide
## VX11 Operator - SSE Ephemeral Token Flow

**Last Updated:** 2026-01-04  
**Status:** ✅ Backend ready for frontend integration  

---

## Overview

The VX11 Operator frontend needs to be updated to use **ephemeral SSE tokens** for real-time event streaming. This document provides the complete flow and code patterns.

### Problem Solved

- ❌ **Before**: Main auth token passed in URL (security risk, logged)
- ✅ **After**: Short-lived ephemeral UUID token (60s TTL, rotatable, low-impact if leaked)

### Why Ephemeral Tokens?

EventSource API cannot send custom headers (`Authorization`, `X-VX11-Token`), only querystring parameters. Passing long-lived main tokens in URLs is a security anti-pattern per OWASP:

- Tokens appear in browser history
- Tokens appear in server logs
- Tokens may be cached by proxies
- Tokens leak via referer headers

**Solution**: Exchange main token for ephemeral UUID (60s TTL) → use ephemeral in querystring.

---

## 3-Tier Token Architecture

```
┌─ Frontend (browser) ─────────────────────┐
│                                          │
│  1. POST /events/sse-token               │
│     Header: X-VX11-Token: <main_token>   │──┐
│                                          │  │
│  3. new EventSource(                     │  │ Tier 1: Frontend→Gateway
│     /events/stream?token=<ephemeral>)    │  │ (Bearer or X-VX11-Token)
│                                          │  │
└──────────────────────────────────────────┘  │
                                              │
                                              ▼
                        ┌───────────────────────────────────┐
                        │ tentaculo_link (Gateway :8000)    │
                        │                                   │
                        │ 2. Generate ephemeral token       │
                        │    Store in Redis (60s TTL)       │
                        │    Return UUID token              │
                        │                                   │
                        │ 4. Validate ephemeral token       │
                        │    (Redis lookup, TTL check)      │
                        │    Return SSE stream if valid     │
                        │                                   │
                        └───────────────────────────────────┘
                                      │
                                      │ Tier 2: Gateway→Backend
                                      │ (X-VX11-Token: service token)
                                      │
                        ┌─────────────▼──────────┐
                        │ operator-backend:8011  │
                        │ (processes requests)   │
                        └────────────────────────┘
```

### Tokens in Each Tier

| Tier | Usage | Token | Storage | TTL | Risk |
|------|-------|-------|---------|-----|------|
| 1 | Frontend→Gateway | `vx11-test-token` (main) | Browser localStorage | ∞ | Never expose in URL |
| 1a | Frontend→Gateway (SSE only) | `<ephemeral-uuid>` (secondary) | Browser memory | 60s | Safe in querystring |
| 2 | Gateway→Backend | `vx11-operator-test-token` (inter-service) | Docker env | ∞ | Internal only |

---

## Implementation Steps

### Step 1: Update Browser localStorage

**Before making any requests**, ensure the main auth token is stored:

```javascript
// In your app initialization (App.tsx or main.tsx)
const MAIN_TOKEN = 'vx11-test-token';

if (!localStorage.getItem('vx11_token')) {
  localStorage.setItem('vx11_token', MAIN_TOKEN);
}

// Verify it's set
console.log('Auth token:', localStorage.getItem('vx11_token'));
```

### Step 2: Implement Ephemeral Token Exchange

Create a function to get ephemeral tokens from the backend:

```typescript
// File: src/services/tokenService.ts

export async function getEphemeralSseToken(mainToken: string): Promise<{
  sse_token: string;
  ttl_sec: number;
  endpoint: string;
}> {
  const response = await fetch('/operator/api/events/sse-token', {
    method: 'POST',
    headers: {
      'X-VX11-Token': mainToken,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(
      `SSE token request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
}
```

### Step 3: Implement EventsClient with Ephemeral Tokens

Replace your existing EventsClient:

```typescript
// File: src/services/eventsClient.ts

export class EventsClient {
  private mainToken: string;
  private eventSource: EventSource | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isConnected = false;

  constructor(mainToken: string) {
    this.mainToken = mainToken;
  }

  /**
   * Connect to SSE stream using ephemeral token flow
   */
  async connect(onMessage: (event: MessageEvent) => void): Promise<void> {
    try {
      // Step 1: Get ephemeral token from backend
      console.log('[EventsClient] Requesting ephemeral token...');
      const tokenData = await getEphemeralSseToken(this.mainToken);
      const ephemeralToken = tokenData.sse_token;
      const ttlSec = tokenData.ttl_sec;

      console.log(
        `[EventsClient] Got ephemeral token (TTL: ${ttlSec}s): ${ephemeralToken.substring(0, 16)}...`
      );

      // Step 2: Connect EventSource with ephemeral token
      const streamUrl = `/operator/api/events/stream?token=${encodeURIComponent(
        ephemeralToken
      )}&follow=true`;

      this.eventSource = new EventSource(streamUrl);

      // Step 3: Set up event handlers
      this.eventSource.onopen = () => {
        console.log('[EventsClient] Connected to SSE stream');
        this.isConnected = true;
      };

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[EventsClient] Message:', data.type);
          onMessage(event);
        } catch (e) {
          console.error('[EventsClient] Failed to parse message:', e);
        }
      };

      this.eventSource.onerror = (event) => {
        console.error('[EventsClient] Stream error:', event);
        this.isConnected = false;
        this.disconnect();

        // Trigger reconnection
        this.scheduleReconnect(onMessage);
      };

      // Step 4: Schedule token refresh BEFORE expiration
      // Refresh every (ttlSec - 5) seconds to avoid race condition
      const refreshInterval = Math.max(1000, (ttlSec - 5) * 1000);
      this.scheduleTokenRefresh(onMessage, refreshInterval);
    } catch (error) {
      console.error('[EventsClient] Connection failed:', error);
      throw error;
    }
  }

  /**
   * Refresh ephemeral token and reconnect
   */
  private async scheduleTokenRefresh(
    onMessage: (event: MessageEvent) => void,
    interval: number
  ): Promise<void> {
    // Clear any existing timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    // Set new timer to refresh token
    this.reconnectTimer = setTimeout(() => {
      console.log('[EventsClient] Token expiring soon, refreshing...');
      this.disconnect();
      // Recursively reconnect (will get new token)
      this.connect(onMessage).catch((err) => {
        console.error('[EventsClient] Reconnection failed:', err);
      });
    }, interval);
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(
    onMessage: (event: MessageEvent) => void,
    attempt: number = 1
  ): void {
    // Exponential backoff: 500ms, 1s, 2s, 4s, max 10s
    const delay = Math.min(500 * Math.pow(2, attempt - 1), 10000);

    console.log(
      `[EventsClient] Scheduling reconnection in ${delay}ms (attempt ${attempt})`
    );

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(() => {
      this.connect(onMessage).catch((err) => {
        console.error('[EventsClient] Reconnection failed:', err);
        this.scheduleReconnect(onMessage, Math.min(attempt + 1, 5));
      });
    }, delay);
  }

  /**
   * Disconnect from SSE stream
   */
  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.isConnected = false;
    console.log('[EventsClient] Disconnected');
  }

  /**
   * Check if connected
   */
  getIsConnected(): boolean {
    return this.isConnected;
  }
}

export default EventsClient;
```

### Step 4: Integrate EventsClient in React Component

Example integration in your main UI component:

```typescript
// File: src/components/Operator/Operator.tsx

import { useEffect, useState } from 'react';
import EventsClient from '@/services/eventsClient';

export function Operator() {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [eventsClient, setEventsClient] = useState<EventsClient | null>(null);

  useEffect(() => {
    // Get main token from localStorage
    const mainToken = localStorage.getItem('vx11_token');
    if (!mainToken) {
      console.error('No auth token in localStorage');
      return;
    }

    // Create and connect EventsClient
    const client = new EventsClient(mainToken);

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        // Handle "connected" message
        if (data.type === 'connected') {
          setIsConnected(true);
          return;
        }

        // Handle regular events
        setEvents((prev) => [...prev, data]);
      } catch (e) {
        console.error('Failed to parse event:', e);
      }
    };

    // Start connection
    client
      .connect(handleMessage)
      .then(() => {
        console.log('EventsClient connected');
        setEventsClient(client);
      })
      .catch((err) => {
        console.error('EventsClient failed:', err);
      });

    // Cleanup on component unmount
    return () => {
      client.disconnect();
    };
  }, []);

  return (
    <div>
      {/* Connection status indicator */}
      <div className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? '✅ Connected' : '❌ Disconnected'}
      </div>

      {/* Events feed */}
      <div className="events-feed">
        {events.map((event, i) => (
          <div key={i} className="event">
            {JSON.stringify(event)}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Step 5: Hard Browser Reload

After deploying the updated frontend:

1. **Clear browser cache**: Ctrl+Shift+Delete (or Cmd+Shift+Delete on Mac)
2. **Hard reload**: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
3. **Verify token is set**: Open DevTools Console → `localStorage.getItem('vx11_token')`

---

## Testing Checklist

### Before Deployment

- [ ] EventsClient class created
- [ ] Token exchange function implemented
- [ ] React component integrated
- [ ] localStorage initialization added

### After Deployment

- [ ] localStorage shows: `vx11_token: "vx11-test-token"`
- [ ] DevTools Network tab shows:
  - [ ] `POST /operator/api/events/sse-token` → 200 OK
  - [ ] `GET /operator/api/events/stream?token=...` → 101 Switching Protocols
  - [ ] Response headers include: `Content-Type: text/event-stream`
- [ ] UI shows "✅ Connected" (not "❌ Disconnected")
- [ ] Console has NO red errors
- [ ] SSE stream maintains connection (keep-alive comments every 10s)

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "401 invalid_token" on stream | Ephemeral token not in Redis | Check Redis connection: `docker compose logs tentaculo_link` |
| "401 invalid_token" on /sse-token | Main token invalid | Verify `localStorage.getItem('vx11_token')` |
| "404 Not Found" on /sse-token | Endpoint missing | Check if tentaculo_link rebuilt |
| "Disconnected" in UI | Stream connection failed | Check DevTools Network + Console logs |
| Token keeps expiring/reconnecting | Working as intended | Ephemeral tokens are 60s TTL (by design) |

---

## Backend API Contract

### POST `/operator/api/events/sse-token`

**Request:**
```http
POST /operator/api/events/sse-token
X-VX11-Token: vx11-test-token
Content-Type: application/json
```

**Response (200 OK):**
```json
{
  "sse_token": "550e8400-e29b-41d4-a716-446655440000",
  "ttl_sec": 60,
  "endpoint": "/operator/api/events/stream",
  "usage": "curl -N '/operator/api/events/stream?token=550e8400-e29b-41d4-a716-446655440000' -H 'Accept: text/event-stream'"
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "invalid_token",
  "reason": "main_auth_failed"
}
```

### GET `/operator/api/events/stream`

**Request:**
```http
GET /operator/api/events/stream?token=550e8400-e29b-41d4-a716-446655440000
Accept: text/event-stream
```

**Response (101 Switching Protocols):**
```
HTTP/1.1 101 Switching Protocols
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "connected", "message": "SSE stream established"}

: keep-alive 0

: keep-alive 1

data: {...actual event...}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "invalid_token"
}
```

---

## Known Limitations & Future Work

1. **Single process limitation**: SSE tokens are now Redis-backed, so they work across multiple Uvicorn workers. ✅

2. **Token expiration**: Frontend must handle 60s TTL by:
   - Either refreshing token before TTL (recommended)
   - Or handling 401 errors and reconnecting

3. **No bidirectional**: SSE is one-way (server → client). For chat, use separate endpoint.

4. **Browser support**: EventSource requires ES6 and works in all modern browsers (IE not supported).

---

## References

- [MDN EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [Server-Sent Events Best Practices](https://html.spec.whatwg.org/multipage/server-sent-events.html)

---

## Need Help?

Check these resources:

1. **Backend logs**: `docker compose logs tentaculo_link | grep SSE`
2. **Redis status**: `docker compose exec redis-test redis-cli KEYS "vx11:*"`
3. **Network debugging**: DevTools → Network tab → Filter by "events"

