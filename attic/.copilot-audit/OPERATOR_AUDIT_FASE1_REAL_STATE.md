# 🔍 AUDITORÍA OPERATOR FASE 1 — ESTADO REAL (Diciembre 2025)

**Generado:** 2025-12-14 | **Estado:** Sin modificaciones | **Objetivo:** Documentar qué existe y cómo funciona realmente

---

## ✅ RENDER GARANTIZADO

### Bootstrap Chain (main.tsx → App.tsx)
```
main.tsx (boot screen) 
  ↓ ensureRootElement() 
  ↓ createRoot() 
  ↓ <App /> 
  ↓ RENDERIZADO
```

**Estado:** ✅ **ROBUSTO**
- Boot screen inline (gradiente 030712→0a0e14)
- Error boundary renderFatal() captura crashes
- No depende de CSS externo para boot
- Fallback: "Inicialización fallida" si error

### Render Real (App.tsx)
```tsx
<AppErrorBoundary>
  <Layout isConnected={events.isConnected} error={events.error}>
    <TabsView events={...} isConnected={...} />
  </Layout>
</AppErrorBoundary>
```

**Status:** ✅ **FUNCIONAL** — Los 7 tabs están presentes y renderizables

---

## 🎨 ARQUITECTURA UI ACTUAL

### Layout (Inline Styles, NO Tailwind)
- **Sidebar** — 16rem, gradiente 030712→1a1a2e→000, estilos inline
- **Header** — Pasthru desde Layout
- **Main content** — Flex, children renderizable

**Conclusión:** ✅ Estilos inline **SIN DEPENDENCIA TAILWIND** ahora

### Tabs (7 Total)
1. **dashboard** (📊) — DashboardView
2. **chat** (💬) — ChatView ← 🎯 **FOCO**
3. **forensics** (📸) — Snapshots panel
4. **decisions** (🧠) — Decisions panel
5. **narrative** (🎙️) — Narratives panel
6. **correlations** (🔗) — Correlations DAG
7. **status** (⚡) — System status

**Render:** ✅ Todos tabs renderizables (component exists)

---

## 💬 CHAT ACTUAL — ESTADO DETALLADO

### ChatView.tsx (125 líneas)
**Flujo:**
```
TextArea (draft state)
  ↓ [Enter]
  ↓ sendMessage(draft)
  ↓ typeInto() → stream-like animation
  ↓ Render messages + error
```

**Features Presentes:**
- ✅ Historial visible (space-y-3)
- ✅ Estilos diferenciados user/assistant
- ✅ Loading spinner (pulsing ●●●)
- ✅ Error display (red border)
- ✅ Input multiline (rows=2, Shift+Enter = newline)
- ✅ Placeholder dinámico según mode
- ✅ Header con status badge (◆ Backend conectado | ○ Modo local)
- ✅ "Operator no actúa; observa." — mensaje pasivo

### useChat.ts Hook (185 líneas)
**Funcionalidad:**

#### 1. **LocalStorage Persistence**
```typescript
STORAGE_KEY = "vx11_chat_messages"
safeLoadMessages() → parse, validate, slice(-200)
safePersistMessages() → every message update
```
✅ **Chat sobrevive page reload**

#### 2. **Probing Backend**
```typescript
probeChatApi() 
  ↓ buildCandidates() → ["http://localhost:8000/chat", ...]
  ↓ fetchWithTimeout(url, OPTIONS, 1500ms)
  ↓ Sets mode: "backend" | "local"
```

**Candidatos testeados:**
1. `VITE_VX11_CHAT_URL` (si existe)
2. `http://localhost:8000/chat` (default)
3. `http://localhost:8000/operator/chat`
4. `http://localhost:8000/v1/chat`

✅ **Auto-detection sin dependencias**

#### 3. **Modo Dual**
```typescript
mode: ChatMode = backendStatus.kind === "connected" ? "backend" : "local"
```

**Backend Mode:**
- `activeApiUrl` != null
- `sendChat(apiUrl, messages)` → real HTTP POST
- Respuesta esperada: `{ response?: string, message?: string }`

**Local Mode (Fallback):**
- `localResponse(input)` → echo + hint
- Persiste en localStorage
- No timeout, no error

✅ **100% tolerancia fallos**

#### 4. **SendMessage Flow**
```typescript
sendMessage(content)
  1. Trim input
  2. Persist user message
  3. Create empty assistant shell (id, animate)
  4. IF apiUrl:
       sendChat(apiUrl, payload) → responseText
     ELSE:
       responseText = localResponse(content)
  5. typeInto(assistantId, responseText) → 12ms chunks, 3 chars per step
  6. Render VIVO (update message.content cada paso)
```

✅ **Typing animation garantiza render**

### chat-api.ts Service (111 líneas)
**Contrato HTTP Expected:**

```typescript
// sendChat() espera:
POST {apiUrl}
Headers:
  Content-Type: application/json
  X-VX11-Token: {token from VITE_VX11_TOKEN}
Body:
  { messages: [{ role: "user"|"assistant", content: string }, ...] }

Response:
  { 
    response?: string,    // ← primary fallback
    message?: string,     // ← secondary fallback
    error?: string
  }
```

**Env Variables:**
- `VITE_VX11_CHAT_URL` — Override default URL
- `VITE_VX11_TOKEN` — Header X-VX11-Token (optional, allows 401 if missing)

**Error Handling:**
- 401 → "Unauthorized: token inválido o faltante"
- 404 → "Chat endpoint not found"
- Timeout (12s) → caught, fallback to local
- No response field → fallback to "…"

✅ **Robusto ante todos los fallos**

---

## 📊 ESTADO DE EVENTOS

### useDashboardEvents.ts (109 líneas)
**Escucha 6 eventos canónicos vía WebSocket:**

```
system.alert → setAlerts (max 10)
system.correlation.updated → setCorrelations (max 5)
forensic.snapshot.created → setSnapshots (max 20)
madre.decision.explained → setDecisions (max 5)
switch.tension.updated → setTensions (max 5)
shub.action.narrated → setNarratives (max 5)
```

**WebSocket URL:** `ws://localhost:8000/ws` (from vx11.config.ts)

**Estado Actual:**
- ✅ Hook estructura OK
- ❌ **WebSocket endpoint NO existe en gateway** (intenta conectar, falla silenciosamente, fallback a desconectado)
- ✅ Handlers registran correctamente
- ✅ isConnected = boolean
- ✅ Error capture

### event-client.ts (112 líneas)
**EventClient WebSocket Implementation:**

```typescript
class EventClient {
  connect() → Promise
  subscribe(eventType, handler)
  dispatch(event) → handlers[eventType]
  attemptReconnect() → 5 intentos, backoff 3s
}
```

**Validación:**
```typescript
isCanonicalEvent(payload) → type check (6 tipos permitidos)
```

✅ **Cliente correcto, pero backend no envía eventos ahora**

---

## 🔧 VARIABLES DE CONFIGURACIÓN

### vx11.config.ts
```typescript
GATEWAY_PORT = 8000
GATEWAY_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

MODULES = { tentaculo_link, madre, switch, hermes, ... }
API_ENDPOINTS = { health, events, dashboard, alerts, ... }
POLLING_INTERVAL = 5000
REQUEST_TIMEOUT = 8000
```

**Usados Actualmente:**
- ✅ WS_URL (para WebSocket, falla ok)
- ❌ POLLING_INTERVAL (no usado, solo WS)
- ❌ API_ENDPOINTS (definidos, no usados en chat)

---

## 🧩 DEPENDENCIAS EXTERNAS

### Node Dependencies (package.json v0.0.0)
```json
react: ^19.2.0 ← ACTUAL (19.2.0-rc.0)
react-dom: ^19.2.0
reactflow: ^11.11.4
```

### Dev Dependencies
```
@tailwindcss/postcss: ^4.1.18 (instalado pero NO usado en estilos)
vite: ^5.x (implícito)
typescript: ^5.7.x (tsconfig.json)
```

**Status:**
- ✅ React 19 — funcional
- ✅ ReactFlow — no usado aún (para correlations DAG)
- ⚠️ Tailwind dev dep pero estilos inline → considerar remover o activar

---

## 🎯 QUÉ ESTÁ DESCONECTADO AHORA

| Feature | Estado | Razón |
|---------|--------|-------|
| Chat backend | ❌ Echo local | No existe `POST /chat` en VX11 |
| WebSocket eventos | ⚠️ Intenta, falla | `/ws` no existe en gateway |
| DeepSeek R1 | ❌ No conectado | Switch no tiene integración ahora |
| Decisions panel | ⚠️ Empty | Espera eventos madre.decision.explained |
| Forensics panel | ⚠️ Empty | Espera eventos forensic.snapshot.created |
| Narrative panel | ⚠️ Empty | Espera eventos shub.action.narrated |

---

## 🎯 QUÉ FUNCIONA AHORA

| Feature | Estado | Verificado |
|---------|--------|-----------|
| Page render | ✅ Always | Boot screen + Error boundary |
| Chat UI | ✅ Visible | ChatView renders, tabs switch |
| Local chat | ✅ Echo mode | localStorage persist, typeInto animation |
| Tab switching | ✅ Works | 7 tabs clickable, activeTab state |
| Input/Enter | ✅ Works | sendMessage triggered, draft cleared |
| Error display | ✅ Works | Red box if HTTP fails |
| Backend probe | ✅ Auto | Checks candidates on mount |
| Fallback | ✅ Always | Si no backend, local + hint |

---

## 📋 VARIABLES DE ENTORNO ESPERADAS

### .env o .env.local (en `operator/`)
```bash
VITE_VX11_CHAT_URL=http://localhost:8000/chat
VITE_VX11_TOKEN=vx11-local-token
VITE_OPERATOR_BACKEND_URL=http://localhost:8011
```

**Status:**
- ❌ No existen ahora → defaults used
- Default chat: `http://localhost:8000/chat` (no existe)
- Default token: none (header omitted si no set)

---

## 🧠 FLUJO DE UNA CONVERSACIÓN (LOCAL MODE AHORA)

```
1. User abre http://localhost:5173
   ↓
2. main.tsx bootHTML rendered
   ↓
3. App → useDashboardEvents (WebSocket connect attempt, falla silenciosamente)
   ↓
4. TabsView renders, chat tab visible
   ↓
5. User escribe "Hola" + Enter
   ↓
6. useChat.sendMessage("Hola")
   ↓
7. activeApiUrl = null (backend probe failed)
   ↓
8. responseText = localResponse("Hola")
   ↓
   ◇ Modo local (sin backend)
   
   El Operator escucha y refleja:
   
   Hola
   
   Configura `VITE_VX11_CHAT_URL` y `VITE_VX11_TOKEN` para hablar con el corazón.
   ↓
9. typeInto animates response (visible, 12ms)
   ↓
10. Messages saved to localStorage
    ↓
11. Next reload: messages recovered
```

---

## 🚨 RIESGOS ACTUALES

| Riesgo | Severity | Descripción |
|--------|----------|-------------|
| No backend endpoint | HIGH | Chat solo funciona local, necesita /chat POST |
| No WebSocket | MEDIUM | Eventos no llegan, paneles vacíos |
| Token optional | LOW | Permite anon requests (ok para dev) |
| TypeScript unused | LOW | @tailwindcss/postcss como dev dep, estilos inline |
| ReactFlow unused | LOW | Incluido, no usado en correlations |

---

## ✨ CONCLUSIÓN FASE 1

### ✅ Qué Está Correcto
- Render nunca falla (boot + error boundary)
- Chat UI completa (tabs, input, messages, typing)
- Fallback a local (localStorage persist)
- Modo dual ready (backend check automático)
- Error handling robusto

### ❌ Qué NO Existe
- `POST /chat` endpoint en VX11
- `GET /ws` WebSocket en gateway
- DeepSeek integration
- Event publisher (Madre, Switch, Shub → eventos)

### 📝 Documentación Encontrada
```
operator/src/
  ├── App.tsx → Entry, uses useDashboardEvents
  ├── main.tsx → Bootstrap chain
  ├── hooks/
  │   ├── useChat.ts → Chat logic (185 L)
  │   └── useDashboardEvents.ts → Events listener (109 L)
  ├── components/chat/
  │   ├── ChatView.tsx → UI (125 L)
  │   └── useChat.ts → Re-export from hooks
  ├── services/
  │   ├── chat-api.ts → HTTP client (111 L)
  │   └── event-client.ts → WebSocket client (112 L)
  ├── types/
  │   ├── chat.ts → ChatMessage, ChatRole
  │   └── canonical-events.ts → 6 event types (105 L)
  └── config/
      └── vx11.config.ts → URLs, env config
```

### 🎯 RECOMENDACIONES (Para FASE 2+)
1. **FASE 2:** Definir `/operator/chat` endpoint exacto
2. **FASE 2:** Definir `/ws` WebSocket protocol en gateway
3. **FASE 3:** Conectar Switch/DeepSeek como responder
4. **FASE 3:** Implementar event publishers (Madre, Manifestator, etc.)
5. **FASE 4:** Reemplazar echo con reasoning real

---

**Auditoría completada sin modificaciones.** ✅
Listo para FASE 2 (definición de contrato backend).
