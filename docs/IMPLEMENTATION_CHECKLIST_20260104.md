# Frontend Implementation Checklist ✅

**Status**: Backend complete (100%) | Frontend implementation ready  
**Date**: 2026-01-04  
**Target**: EventsClient TypeScript class + React integration

---

## Phase 1: Create EventsClient Class

### File: `src/services/eventsClient.ts`

- [ ] **Create file with these responsibilities:**
  ```
  1. Maintain main token (from localStorage)
  2. Exchange for ephemeral token (POST /events/sse-token)
  3. Open EventSource stream with ephemeral token
  4. Manage keep-alive monitoring
  5. Auto-refresh token before 60s expiration
  6. Handle reconnection with exponential backoff
  7. Emit events to subscribers
  ```

- [ ] **Implement getEphemeralToken() method**
  ```typescript
  private async getEphemeralToken(): Promise<string> {
    // POST /operator/api/events/sse-token
    // Send: X-VX11-Token header (main token from localStorage)
    // Receive: {"sse_token": "uuid", "ttl_sec": 60}
    // Return: sse_token value
    // Handle: 401 errors, network errors
  }
  ```

- [ ] **Implement connect() method**
  ```typescript
  public async connect(onMessage: (event: any) => void): Promise<void> {
    // 1. Get ephemeral token
    // 2. Create EventSource(url + ?token=ephemeral)
    // 3. onopen: Set isConnected = true
    // 4. onmessage: Parse JSON, call onMessage callback
    // 5. onerror: Close stream, schedule reconnection
    // 6. Schedule token refresh at: 55s (before 60s expiration)
  }
  ```

- [ ] **Implement disconnect() method**
  ```typescript
  public disconnect(): void {
    // Close EventSource
    // Clear all timers (refresh, reconnect, etc)
    // Set isConnected = false
  }
  ```

- [ ] **Implement token refresh logic**
  ```typescript
  // Schedule at: 55s (5s buffer before 60s expiration)
  // Action: Get new ephemeral token silently
  // Create new EventSource with new token
  // Close old stream
  ```

- [ ] **Implement reconnection logic**
  ```typescript
  // Exponential backoff: 1s, 2s, 4s, 8s, 16s (max)
  // Max retries: 5
  // After max retries: Emit error event
  ```

### Reference Implementation Pattern

```typescript
class EventsClient {
  private mainToken: string;
  private currentEphemeralToken: string | null = null;
  private eventSource: EventSource | null = null;
  private isConnected: boolean = false;
  private refreshTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private subscribers: Set<(event: any) => void> = new Set();

  constructor(mainToken: string) {
    this.mainToken = mainToken;
  }

  async getEphemeralToken(): Promise<string> {
    const response = await fetch('/operator/api/events/sse-token', {
      method: 'POST',
      headers: {
        'X-VX11-Token': this.mainToken,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return data.sse_token;
  }

  async connect(): Promise<void> {
    try {
      this.currentEphemeralToken = await this.getEphemeralToken();
      
      const url = `/operator/api/events/stream?token=${this.currentEphemeralToken}`;
      this.eventSource = new EventSource(url);
      
      this.eventSource.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.scheduleTokenRefresh();
      };
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.subscribers.forEach(cb => cb(data));
        } catch (e) {
          console.error('Failed to parse event:', e);
        }
      };
      
      this.eventSource.onerror = () => {
        this.handleConnectionError();
      };
    } catch (error) {
      console.error('Failed to connect:', error);
      this.handleConnectionError();
    }
  }

  private scheduleTokenRefresh(): void {
    // Refresh at 55s (before 60s expiration)
    this.refreshTimer = setTimeout(() => {
      this.refreshToken();
    }, 55000);
  }

  private async refreshToken(): Promise<void> {
    try {
      const oldStream = this.eventSource;
      await this.connect();
      oldStream?.close();
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.handleConnectionError();
    }
  }

  private handleConnectionError(): void {
    this.isConnected = false;
    this.eventSource?.close();
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 32000);
      this.reconnectAttempts++;
      
      this.reconnectTimer = setTimeout(() => {
        this.connect();
      }, delay);
    }
  }

  disconnect(): void {
    clearTimeout(this.refreshTimer as any);
    clearTimeout(this.reconnectTimer as any);
    this.eventSource?.close();
    this.isConnected = false;
  }

  subscribe(callback: (event: any) => void): () => void {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  getStatus() {
    return {
      isConnected: this.isConnected,
      hasToken: !!this.currentEphemeralToken,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

export default EventsClient;
```

---

## Phase 2: Integrate into React Components

### File: `src/components/Operator/Operator.tsx`

#### Setup: Initialize on component mount

- [ ] **Import EventsClient**
  ```typescript
  import EventsClient from '../../services/eventsClient';
  ```

- [ ] **Add state variables**
  ```typescript
  const [mainToken] = useState(() => 
    localStorage.getItem('vx11_token') || 'vx11-test-token'
  );
  const [eventsClient] = useState(() => new EventsClient(mainToken));
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  ```

- [ ] **Initialize on mount**
  ```typescript
  useEffect(() => {
    // Store main token in localStorage
    localStorage.setItem('vx11_token', mainToken);
    
    // Set up event listener
    const unsubscribe = eventsClient.subscribe((event) => {
      setIsConnected(true);
      setEvents(prev => [...prev, event]);
    });
    
    // Connect to stream
    eventsClient.connect().catch(console.error);
    
    // Cleanup on unmount
    return () => {
      unsubscribe();
      eventsClient.disconnect();
    };
  }, [eventsClient, mainToken]);
  ```

#### Display: Connection status

- [ ] **Add status badge**
  ```typescript
  <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
    {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
  </div>
  ```

- [ ] **CSS styling**
  ```css
  .status-badge {
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 600;
  }
  
  .status-badge.connected {
    background: #d4edda;
    color: #155724;
  }
  
  .status-badge.disconnected {
    background: #f8d7da;
    color: #721c24;
  }
  ```

#### Display: Policy state

- [ ] **Show SOLO_MADRE warning**
  ```typescript
  {policy === 'SOLO_MADRE' && (
    <div className="policy-warning">
      ⚠️ SOLO_MADRE Policy Active
      Chat is disabled (Read-only mode until Madre enables full control)
    </div>
  )}
  ```

#### Disable: Chat input when policy blocks

- [ ] **Disable chat based on policy**
  ```typescript
  <input 
    type="text"
    placeholder="Type your message..."
    disabled={policy === 'SOLO_MADRE'}
    // ... other props
  />
  ```

### File: `src/components/Operator/Settings.tsx` (Optional UI)

- [ ] **Display current policy**
  ```typescript
  <div className="settings-panel">
    <h3>Operator Settings</h3>
    <div className="setting-row">
      <label>Policy Mode:</label>
      <span className="policy-badge">{policy}</span>
    </div>
    <div className="setting-row">
      <label>Window Status:</label>
      <span className="status-value">{windowStatus}</span>
    </div>
  </div>
  ```

- [ ] **Optional: Policy change button** (if authorized)
  ```typescript
  {canChangePolicies && (
    <button 
      onClick={() => changePolicyTo('full')}
      disabled={policy === 'full'}
    >
      Enable Full Mode
    </button>
  )}
  ```

---

## Phase 3: Testing

### Browser DevTools Verification

- [ ] **Open DevTools (F12) → Network tab**

- [ ] **Refresh page (Ctrl+R)**
  - [ ] See: `POST /operator/api/events/sse-token` → **200 OK**
  - [ ] Response body: `{"sse_token": "...", "ttl_sec": 60}`
  - [ ] See: `GET /operator/api/events/stream?token=...` → **101 Switching Protocols**

- [ ] **Check Messages tab**
  - [ ] See keep-alive pings: `: keep-alive` every 10 seconds
  - [ ] See connected message: `data: {"type": "connected", ...}`
  - [ ] See business events streaming in

- [ ] **Check console (F12 → Console tab)**
  - [ ] No errors about 401 Unauthorized
  - [ ] No CORS errors
  - [ ] Should see EventsClient initialization logs (if added)

### Token Refresh Verification

- [ ] **Open DevTools → Network tab**

- [ ] **Wait 55 seconds**
  - [ ] New `POST /operator/api/events/sse-token` appears
  - [ ] New ephemeral token generated
  - [ ] New `GET /operator/api/events/stream?token=...` request opens
  - [ ] Old request closes gracefully

- [ ] **Verify in console**
  - [ ] No "Connection lost" message
  - [ ] No error spikes
  - [ ] Connection status stays "Connected"

### Connection Status UI

- [ ] **On page load**
  - [ ] Should show: "🔴 Disconnected" briefly (< 1 second)

- [ ] **After SSE opens**
  - [ ] Should show: "🟢 Connected"
  - [ ] Should remain "Connected" during token refresh

- [ ] **On network error**
  - [ ] Should show: "🔴 Disconnected"
  - [ ] Should show: "Reconnecting... (attempt 1/5)"
  - [ ] After reconnection: Back to "🟢 Connected"

### SOLO_MADRE Policy Display

- [ ] **On page load**
  - [ ] Should show: "Policy: SOLO_MADRE"
  - [ ] Should show: "Chat is disabled (Read-only mode)"

- [ ] **Chat input**
  - [ ] Should be disabled (grayed out)
  - [ ] Should show tooltip: "Disabled in SOLO_MADRE mode"

- [ ] **After policy change** (if tested)
  - [ ] Should show: "Policy: full" or "Policy: operative"
  - [ ] Chat input should enable

---

## Phase 4: Error Handling

### Implement graceful degradation

- [ ] **Token generation fails (401)**
  ```typescript
  Try to:
  1. Refresh main token from localStorage
  2. Re-attempt ephemeral token request
  3. If still fails: Show error message to user
     "Unable to establish connection. Please refresh the page."
  ```

- [ ] **SSE stream closes unexpectedly**
  ```typescript
  Automatically:
  1. Wait 1s
  2. Try to reconnect (exponential backoff)
  3. Regenerate ephemeral token
  4. Re-open stream
  5. After 5 failures: Show error message
  ```

- [ ] **Network error during token refresh**
  ```typescript
  When 55s refresh timer fires:
  1. Try to get new token
  2. If fails, close old stream
  3. Start reconnection logic
  4. Don't break existing connection
  ```

---

## Phase 5: Documentation

- [ ] **Add JSDoc comments to EventsClient**
  ```typescript
  /**
   * Client for SSE-based real-time events
   * 
   * Manages 3-tier authentication:
   * 1. Main token (localStorage, long-lived)
   * 2. Ephemeral token (Redis, 60s TTL, auto-rotates)
   * 3. Service tokens (inter-pod communication)
   * 
   * Auto-reconnects with exponential backoff on failure
   * Token refresh is transparent to caller (every 55s)
   */
  ```

- [ ] **Add usage example comment in Operator.tsx**
  ```typescript
  // Usage:
  // const eventsClient = new EventsClient(mainToken);
  // const unsub = eventsClient.subscribe((event) => {
  //   console.log('Event received:', event);
  // });
  // await eventsClient.connect();
  // // ... later
  // unsub();
  // eventsClient.disconnect();
  ```

---

## Deployment Checklist

- [ ] **Before deploying to production:**
  1. [ ] All tests passing (DevTools verification)
  2. [ ] Token refresh working seamlessly (55s+ observation)
  3. [ ] Connection status badge updating correctly
  4. [ ] Policy display accurate (SOLO_MADRE vs full)
  5. [ ] Chat disabled in SOLO_MADRE, enabled in full
  6. [ ] Reconnection works after network failure
  7. [ ] No console errors or warnings
  8. [ ] localStorage correctly storing main token

- [ ] **Backend API checklist** (already done)
  - [x] POST `/operator/api/events/sse-token` working (200 OK)
  - [x] GET `/operator/api/events/stream?token=...` working (101)
  - [x] Redis token storage with TTL
  - [x] Keep-alive messages every 10s
  - [x] Token refresh before expiration
  - [x] Multi-worker safety (Redis backing)

---

## Reference URLs

| Resource | URL | Purpose |
|----------|-----|---------|
| **Frontend Guide** | [FRONTEND_SSE_EPHEMERAL_TOKENS.md](../FRONTEND_SSE_EPHEMERAL_TOKENS.md) | Complete implementation details |
| **Troubleshooting** | [FRONTEND_VISUAL_TROUBLESHOOTING.md](../FRONTEND_VISUAL_TROUBLESHOOTING.md) | Debug guide + common issues |
| **Smoke Tests** | [SMOKE_TEST_RESULTS_20260104.md](../SMOKE_TEST_RESULTS_20260104.md) | Backend verification results |
| **SOLO_MADRE Explanation** | [READONLY_FULLMODE_EXPLANATION.md](../READONLY_FULLMODE_EXPLANATION.md) | Policy documentation |

---

## Debugging Commands

```bash
# Watch logs in real-time
docker compose -f docker-compose.full-test.yml logs -f tentaculo_link | grep -i "operator\|token\|sse"

# Check Redis tokens
docker compose -f docker-compose.full-test.yml exec redis-test redis-cli MONITOR

# Get window status
curl http://localhost:8000/operator/api/window/status | jq

# Test token generation manually
curl -X POST http://localhost:8000/operator/api/events/sse-token \
  -H "X-VX11-Token: vx11-test-token" | jq

# Test SSE with token (20 second test)
SSE_TOKEN=$(curl -s -X POST http://localhost:8000/operator/api/events/sse-token \
  -H "X-VX11-Token: vx11-test-token" | jq -r .sse_token)
timeout 20 curl -N "http://localhost:8000/operator/api/events/stream?token=$SSE_TOKEN"
```

---

## Success Criteria

✅ **Implementation Complete When:**

1. [ ] EventsClient TypeScript class created and tested
2. [ ] React component successfully connects to SSE stream
3. [ ] Connection status badge shows "🟢 Connected" after ~1s
4. [ ] Token refresh happens silently every 55s (no interruption to user)
5. [ ] Keep-alive messages visible in DevTools Network tab
6. [ ] Policy state correctly displayed (SOLO_MADRE vs full)
7. [ ] Chat input disabled in SOLO_MADRE, enabled in full
8. [ ] Reconnection works after simulated network failure
9. [ ] No console errors or network errors
10. [ ] Code reviewed and merged to main branch

---

**Backend Status**: ✅ 100% Complete  
**Frontend Status**: ⏳ Ready to implement (this checklist)  
**Expected Timeline**: 2-3 hours for experienced TypeScript/React developer  

**Next Step**: Follow this checklist, referencing the implementation guide and troubleshooting docs.
