# Operator UI Runtime (Dev vs Prod)

**Versión:** 7.0 | **Módulo:** `operator_backend/frontend`  
**Objetivo:** Claridad sobre cómo corre UI en desarrollo local vs producción Docker

---

## Development Local (npm run dev)

### Setup

```bash
cd operator_backend/frontend
npm install  # Install deps (TanStack Query already included)
npm run dev   # Start Vite dev server on http://localhost:5173
```

### Environment Variables

**File:** `.env.local` (gitignored)

```bash
# Backend URL (default: localhost:8011)
VITE_OPERATOR_API_URL=http://localhost:8011

# VX11 Token (dev only)
VITE_VX11_TOKEN=vx11-local-token

# Enable debug logs
VITE_DEBUG=true
```

### Features Active

| Feature | Status | Notes |
|---------|--------|-------|
| **TanStack Query caching** | ✅ | 30s staleTime, automatic retries |
| **WebSocket reconnection** | ✅ | Exponential backoff, max 10 attempts |
| **Hot reload** | ✅ | Vite HMR on port 5173 |
| **Source maps** | ✅ | Full debugging with `npm run type-check` |
| **React DevTools** | ✅ | Browser extension supported |

### Accessing UI

```
Frontend:  http://localhost:5173
Backend:   http://localhost:8011
WebSocket: ws://localhost:8011/ws
```

### Debugging

```bash
# Type checking
npm run type-check

# Run tests
npm run test

# E2E testing (Playwright)
npm run e2e

# ESLint (if available)
npm run lint
```

---

## Production Docker (docker-compose.yml)

### Build

```bash
cd operator_backend/frontend
npm ci           # Clean install (lockfile-based)
npm run build    # Build dist/ (minified, optimized)
```

**Output:** `operator_backend/frontend/dist/`

### Docker Image

**File:** `Dockerfile` (hypothetical, if Docker setup exists)

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 8020
CMD ["nginx", "-g", "daemon off;"]
```

### Environment (docker-compose)

```yaml
operator-frontend:
  image: vx11/operator-frontend:latest
  ports:
    - "8020:80"  # Nginx on port 8020
  environment:
    - VITE_OPERATOR_API_URL=http://operator-backend:8011  # Internal network
    - VITE_VX11_TOKEN=vx11-local-token
  networks:
    - vx11
  depends_on:
    - operator-backend
```

### Runtime Features

| Feature | Status | Notes |
|---------|--------|-------|
| **TanStack Query caching** | ✅ | Browser localStorage + memory |
| **WebSocket reconnection** | ✅ | Exponential backoff |
| **Hot reload** | ❌ | Not applicable (built, static files) |
| **Performance optimizations** | ✅ | Code splitting, lazy loading, minified |
| **Gzip compression** | ✅ | Nginx handles |

### Accessing UI

```
Frontend:  http://localhost:8020  (Nginx reverse proxy)
Backend:   http://operator-backend:8011  (internal Docker network)
WebSocket: ws://127.0.0.1:8011/ws or ws://localhost:8020/ws (CORS config needed)
```

---

## Key Configuration Files

### Vite Config (`vite.config.ts`)

```typescript
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    // Proxy API calls to backend during dev
    proxy: {
      "/operator": {
        target: "http://localhost:8011",
        changeOrigin: true,
      },
      "/ws": {
        target: "ws://localhost:8011",
        ws: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,  // Set to true for prod debugging
    rollupOptions: {
      output: {
        manualChunks: {
          // Code splitting for better caching
          vendor: ["react", "react-dom", "@tanstack/react-query"],
        },
      },
    },
  },
});
```

### TypeScript Config (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "jsx": "react-jsx",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "resolveJsonModule": true,
    "skipLibCheck": true
  }
}
```

---

## Networking & CORS

### Development Local

**Request:** `http://localhost:5173` → `http://localhost:8011/operator/chat`
- Vite proxy handles: ✅ Automatic forwarding (see proxy config)
- CORS issues: ❌ None (proxy handles)

### Production Docker

**Request:** `http://localhost:8020` → `ws://localhost:8011/ws`
- Nginx proxy: ✅ Can forward `/ws` to backend
- CORS issues: ⚠️ Depends on backend CORS config

**Solution:** Backend debe exponer CORS:

```python
# operator_backend/backend/main_v7.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8020", "http://127.0.0.1:8020"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Caching Strategy (TanStack Query)

### Query Keys

```typescript
// Chat session queries
["operatorSession", sessionId]  // Grouped by session

// Stale times
staleTime: 30000  // 30s (fresh data, no background refetch)
cacheTime: 5 * 60 * 1000  // 5 min (keep in memory)
```

### Invalidation

```typescript
// When sending a chat message, invalidate session:
queryClient.invalidateQueries(["operatorSession", sessionId]);
// This triggers automatic refetch of session history
```

### Browser Storage

- **Memory cache:** React Query internal
- **Persistent cache:** localStorage (optional, if implemented)
- **IndexedDB:** Optional for large session history

---

## WebSocket Reconnection Logic

### State Machine

```
                    ┌─────────────────────┐
                    │  Connection Lost    │
                    └──────────┬──────────┘
                               │
                          Start Timer
                               │
                          ┌────▼────┐
                          │  OPEN   │
                          └────┬────┘
                               │
                         Connect OK?
                        /       |        \
                      YES      NO        MAX_ATTEMPTS?
                     /          |          \
            ┌────────────┐  ┌─────────┐  ┌──────────┐
            │ CONNECTED  │  │ WAITING │  │  FAILED  │
            └────────────┘  └──────┬──┘  └──────────┘
                                   │
                           Backoff: 1s, 2s, 4s, 8s, 16s, 30s max
```

### Implementation (in api-improved.ts)

```typescript
attemptReconnect(): void {
  this.reconnectAttempts++;
  const delay = Math.min(
    1000 * Math.pow(2, this.reconnectAttempts - 1),  // Exponential
    30000  // Max 30s
  );
  setTimeout(() => this.connect(), delay);
}
```

---

## Performance Optimization

### Code Splitting

```typescript
// Lazy-load heavy components
const ChatPanel = lazy(() => import("./components/ChatPanel"));
const HormigueroPanel = lazy(() => import("./components/HormigueroPanel"));

// In JSX:
<Suspense fallback={<Spinner />}>
  <ChatPanel />
</Suspense>
```

### Virtual Scrolling

```typescript
// If message count > 200, use react-window
import { FixedSizeList } from "react-window";

<FixedSizeList
  height={600}
  itemCount={messages.length}
  itemSize={50}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>{messages[index].content}</div>
  )}
</FixedSizeList>
```

---

## Troubleshooting

### Dev Local

**Issue:** API calls timeout (>15s)
- **Cause:** Backend slow, Switch not available
- **Solution:** Check `curl http://localhost:8011/health`

**Issue:** WebSocket won't reconnect
- **Cause:** Max retries reached or manual disconnect
- **Solution:** Open browser console, check logs, reload UI

**Issue:** stale data in UI
- **Cause:** Query cache too aggressive
- **Solution:** Reduce `staleTime` in query config

### Production Docker

**Issue:** 404 for static assets (dist/)
- **Cause:** Nginx not serving dist/ directory
- **Solution:** Check Dockerfile COPY instruction

**Issue:** WebSocket can't connect from browser
- **Cause:** CORS or proxy misconfiguration
- **Solution:** Check backend CORS + Nginx proxy config

**Issue:** Credentials not sent to backend
- **Cause:** fetch() without `credentials: "include"`
- **Solution:** Enable in api calls if needed

---

## Migration from Legacy (api.ts → api-improved.ts)

### Old Pattern

```typescript
import { sendChat } from "../services/api";

const response = await sendChat(message, mode, { session_id });
```

### New Pattern (Recommended)

```typescript
import { useChat } from "../services/api-improved";

const chatMutation = useChat(sessionId);
await chatMutation.mutateAsync(message);
```

**Benefits:**
- ✅ Automatic caching + retries
- ✅ Type-safe with React Query
- ✅ Built-in error handling
- ✅ Deduplication of requests

---

## Environment Setup Checklist

### Development

- [ ] Node.js 18+ installed
- [ ] `npm install` completed
- [ ] Backend running on localhost:8011
- [ ] `npm run dev` starts on port 5173
- [ ] `VITE_OPERATOR_API_URL=http://localhost:8011` in .env.local
- [ ] Token configured (default: vx11-local-token)

### Production

- [ ] Docker image built: `docker build -t vx11/operator-frontend:latest .`
- [ ] `docker-compose.yml` has correct ports (8020)
- [ ] Backend service running and accessible
- [ ] CORS configured in backend
- [ ] WebSocket proxy configured in Nginx
- [ ] SSL/TLS configured if HTTPS (outside scope)

---

## References

- `operator_backend/frontend/` — Frontend source
- `operator_backend/frontend/src/services/api-improved.ts` — New TanStack Query wrapper
- `operator_backend/frontend/vite.config.ts` — Build configuration
- `docs/API_OPERATOR_CHAT.md` — Backend API
- `docs/WORKFLOWS_VX11_LOW_COST.md` — Testing endpoints

---

**Versión:** 7.0 | **Fase:** H | **Actualizado:** 2025-12-14
