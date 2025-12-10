# Operator UI v7.1 — Modernización ChatGPT-Style

**Fecha:** 9 dic 2025  
**Versión:** VX11 v7.1  
**Objetivo:** Upgrade visual + UX + estructura limpia

---

## 📊 ESTADO ACTUAL vs DESEADO

| Aspecto | Actual | v7.1 Target |
|---------|--------|-------------|
| **Chat UI** | Inline texto, sin estilo | Burbujas ChatGPT dark theme |
| **Typing Indicator** | ❌ No | ✅ Animated dots |
| **Timestamps** | ✅ ISO strings | ✅ Human-friendly (HH:MM) |
| **Avatars** | ❌ No | ✅ User/Assistant badges |
| **Sessions** | ⚠️ Generated, no UI | ✅ Sidebar list + persist |
| **Error Handling** | ✅ Alerts | ✅ Toast-style notifications |
| **Responsive** | ⚠️ Partial | ✅ Mobile-friendly |
| **Autoscroll** | ✅ Yes | ✅ Yes (maintain) |
| **Markdown** | ❌ No | ✅ Basic (code blocks, bold) |

---

## 🎨 DISEÑO v7.1

### 1. Chat Panel — ChatGPT Dark Theme

```
┌─────────────────────────────────────┐
│ ✕ CHAT                         [⋮]  │  ← Header bar
├─────────────────────────────────────┤
│                                     │
│  [Avatar] Assistant                 │  ← Bubble left (gray)
│  "Hola, ¿cómo puedo ayudarte?"      │
│  12:34                              │
│                                     │
│                        [Avatar] You │  ← Bubble right (blue)
│                "Analiza este audio" │
│                              12:35  │
│                                     │
│  [Avatar] Assistant                 │
│  "Analizando..."                    │  ← Typing indicator
│  ⊙ ⊙ ⊙                              │
│                                     │
├─────────────────────────────────────┤
│ [📎] [Archivo...] [Send →]          │  ← Input bar
└─────────────────────────────────────┘
```

### 2. Sessions Sidebar (NEW)

```
┌────────────────┐
│  SESIONES (⊕)  │
├────────────────┤
│ ⭐ Sesión 1... │ ← Current
│   Sesión 2...  │
│   Sesión 3...  │
│   Sesión 4...  │
│                │
│  [Nueva sesión]│
└────────────────┘
```

### 3. Module Panels — Expandible (BONUS)

```
┌───────────────────────────────┐
│ ▶ Madre (8001)        🟢 LIVE  │ ← Click to expand
└───────────────────────────────┘

┌───────────────────────────────┐
│ ▼ Switch (8002)       🟢 LIVE  │
│  - Queue size: 0               │
│  - Active model: general-7b     │
│  - Warm model: audio-enging     │
│  [Restart] [Logs]              │
└───────────────────────────────┘
```

---

## 📝 CAMBIOS CONCRETOS

### A. Archivo: `src/styles.css`

**Agregar:**

```css
/* ============ ChatGPT DARK THEME ============ */

:root {
  --primary-bg: #0d0d0d;
  --secondary-bg: #1a1a1a;
  --tertiary-bg: #262626;
  --border-color: #404040;
  --text-primary: #ececec;
  --text-secondary: #b4b4b4;
  --user-bubble: #10a37f;
  --assistant-bubble: #565869;
  --error-color: #ff6b6b;
  --success-color: #1dd1a1;
}

body, html, #root {
  background: var(--primary-bg);
  color: var(--text-primary);
}

.chat-container {
  display: flex;
  height: 100vh;
  gap: 0;
}

.chat-sidebar {
  width: 260px;
  background: var(--secondary-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.chat-sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-sidebar-header h2 {
  margin: 0;
  font-size: 16px;
}

.chat-sidebar-header button {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 18px;
  color: var(--text-secondary);
}

.chat-sidebar-list {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
  list-style: none;
  margin: 0;
}

.chat-sidebar-item {
  padding: 10px 12px;
  margin: 4px 0;
  border-radius: 8px;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s;
}

.chat-sidebar-item:hover {
  background: var(--tertiary-bg);
}

.chat-sidebar-item.active {
  background: var(--tertiary-bg);
  border-color: var(--user-bubble);
}

.chat-sidebar-new {
  padding: 12px;
  margin: 12px;
  background: var(--tertiary-bg);
  border: 1px dashed var(--border-color);
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  font-size: 12px;
}

/* ========== CHAT BUBBLES ========== */

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--primary-bg);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  display: flex;
  gap: 12px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  justify-content: flex-end;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  flex-shrink: 0;
}

.message.assistant .message-avatar {
  background: var(--assistant-bubble);
  color: white;
}

.message.user .message-avatar {
  background: var(--user-bubble);
  color: white;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message.assistant .message-bubble {
  background: var(--tertiary-bg);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.message.user .message-bubble {
  background: var(--user-bubble);
  color: white;
}

.message-timestamp {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 4px;
  text-align: right;
}

.message.user .message-timestamp {
  text-align: right;
  padding-right: 44px;
}

/* ========== TYPING INDICATOR ========== */

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-10px);
  }
}

/* ========== INPUT BAR ========== */

.chat-input-area {
  padding: 20px;
  border-top: 1px solid var(--border-color);
  background: var(--primary-bg);
}

.chat-input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  background: var(--tertiary-bg);
  border: 1px solid var(--border-color);
  border-radius: 24px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  resize: none;
  max-height: 100px;
}

.chat-input:focus {
  outline: none;
  border-color: var(--user-bubble);
}

.chat-input::placeholder {
  color: var(--text-secondary);
}

.chat-send-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--user-bubble);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
}

.chat-send-button:hover:not(:disabled) {
  background: #0d8659;
  transform: scale(1.05);
}

.chat-send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ========== ERROR TOAST ========== */

.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 12px 16px;
  background: var(--error-color);
  color: white;
  border-radius: 8px;
  font-size: 14px;
  animation: slideUp 0.3s ease;
  z-index: 1000;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========== EXPANDIBLE PANELS ========== */

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--tertiary-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.panel-header:hover {
  background: #2d2d30;
}

.panel-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
}

.panel-toggle {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}

.panel-toggle.expanded {
  transform: rotate(90deg);
}

.panel-content {
  padding: 12px 16px;
  background: var(--secondary-bg);
  border: 1px solid var(--border-color);
  border-top: none;
  border-radius: 0 0 8px 8px;
  max-height: 300px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
}

.panel-content.hidden {
  display: none;
}

.status-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
}

.status-indicator.live {
  background: var(--success-color);
  animation: pulse 2s infinite;
}

.status-indicator.error {
  background: var(--error-color);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* ========== RESPONSIVE ========== */

@media (max-width: 768px) {
  .chat-sidebar {
    display: none;
  }

  .message-bubble {
    max-width: 85%;
  }
}
```

### B. Archivo: `src/components/ChatPanel.tsx`

**Nueva versión:**

```tsx
import React, { useState, useRef, useEffect } from "react";
import { sendChat } from "../services/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

type Session = {
  id: string;
  name: string;
  createdAt: string;
};

type Props = {
  onSend?: (msg: string, mode: string, metadata?: any) => Promise<void>;
  events: any[];
};

export function ChatPanel({ onSend, events }: Props) {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("chat");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const errorTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize session on mount
  useEffect(() => {
    const newSessionId = `session_${Date.now()}`;
    setSessionId(newSessionId);
    setActiveSessionId(newSessionId);
    
    // Load sessions from localStorage
    const saved = localStorage.getItem("chatSessions");
    const prevSessions: Session[] = saved ? JSON.parse(saved) : [];
    setSessions(prevSessions);
  }, []);

  // Save sessions to localStorage
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem("chatSessions", JSON.stringify(sessions));
    }
  }, [sessions]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString("es-ES", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  };

  const send = async () => {
    if (!input.trim()) return;

    setSending(true);
    setError(null);

    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    try {
      const resp = await sendChat(input, mode, { session_id: sessionId });

      if (resp?.error) {
        setError(`Error: ${resp.error}`);
      } else {
        const responseText = resp?.response || resp?.message || "No response";
        const assistantMsg: Message = {
          role: "assistant",
          content: responseText,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        if (resp?.session_id) {
          setSessionId(resp.session_id);
        }
      }
    } catch (e: any) {
      setError(`Exception: ${e.message}`);
    } finally {
      setSending(false);
    }

    // Auto-clear error after 5s
    if (errorTimeoutRef.current) {
      clearTimeout(errorTimeoutRef.current);
    }
    errorTimeoutRef.current = setTimeout(() => setError(null), 5000);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const createNewSession = () => {
    const newId = `session_${Date.now()}`;
    const newSession: Session = {
      id: newId,
      name: `Sesión ${new Date().toLocaleTimeString("es-ES")}`,
      createdAt: new Date().toISOString(),
    };
    setSessions((prev) => [newSession, ...prev]);
    setSessionId(newId);
    setActiveSessionId(newId);
    setMessages([]);
  };

  const switchSession = (id: string) => {
    setActiveSessionId(id);
    setSessionId(id);
    setMessages([]);
  };

  return (
    <div className="chat-container">
      {/* SIDEBAR */}
      <div className="chat-sidebar">
        <div className="chat-sidebar-header">
          <h2>💬 SESIONES</h2>
          <button onClick={createNewSession} title="Nueva sesión">
            ⊕
          </button>
        </div>
        <ul className="chat-sidebar-list">
          {sessions.map((session) => (
            <li
              key={session.id}
              className={`chat-sidebar-item ${
                activeSessionId === session.id ? "active" : ""
              }`}
              onClick={() => switchSession(session.id)}
            >
              {session.name}
            </li>
          ))}
        </ul>
        <div className="chat-sidebar-new" onClick={createNewSession}>
          + Nueva sesión
        </div>
      </div>

      {/* MAIN CHAT */}
      <div className="chat-main">
        {/* MESSAGES */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div style={{ textAlign: "center", color: "#999", marginTop: "auto", marginBottom: "auto" }}>
              <p>Inicia una conversación...</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-avatar">{msg.role === "user" ? "👤" : "🤖"}</div>
              <div style={{ flex: 1 }}>
                <div className="message-bubble">{msg.content}</div>
                <div className="message-timestamp">{formatTime(msg.timestamp)}</div>
              </div>
            </div>
          ))}
          {sending && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div style={{ flex: 1 }}>
                <div className="message-bubble">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* INPUT */}
        <div className="chat-input-area">
          <div className="chat-input-wrapper">
            <textarea
              className="chat-input"
              placeholder="Escribe tu mensaje aquí... (Shift+Enter para nueva línea)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sending}
              rows={1}
            />
            <button
              className="chat-send-button"
              onClick={send}
              disabled={sending || !input.trim()}
            >
              →
            </button>
          </div>
        </div>
      </div>

      {/* ERROR TOAST */}
      {error && <div className="toast">{error}</div>}
    </div>
  );
}
```

### C. Archivo: `src/components/ModulePanel.tsx` (NEW)

```tsx
import React, { useState } from "react";

type ModuleInfo = {
  name: string;
  port: number;
  status: "online" | "offline" | "degraded";
  details?: Record<string, any>;
};

type Props = {
  module: ModuleInfo;
};

export function ModulePanel({ module }: Props) {
  const [expanded, setExpanded] = useState(false);

  const statusColor =
    module.status === "online"
      ? "var(--success-color)"
      : module.status === "degraded"
      ? "#ff9800"
      : "var(--error-color)";

  return (
    <div style={{ marginBottom: "8px" }}>
      <div
        className="panel-header"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="panel-header-title">
          <div
            className={`panel-toggle ${expanded ? "expanded" : ""}`}
          >
            ▶
          </div>
          <span className="status-indicator live" style={{ background: statusColor }}></span>
          <span>{module.name}</span>
          <span style={{ color: "var(--text-secondary)", fontSize: "12px" }}>
            ({module.port})
          </span>
        </div>
        <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
          {module.status.toUpperCase()}
        </span>
      </div>
      {expanded && (
        <div className="panel-content">
          {module.details ? (
            <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordWrap: "break-word" }}>
              {JSON.stringify(module.details, null, 2)}
            </pre>
          ) : (
            <span style={{ color: "var(--text-secondary)" }}>Sin detalles</span>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 📋 IMPLEMENTACIÓN v7.1

### Paso 1: Reemplazar `src/styles.css`
✅ Copy entire CSS above

### Paso 2: Reemplazar `src/components/ChatPanel.tsx`
✅ Copy entire TSX above

### Paso 3: Crear `src/components/ModulePanel.tsx`
✅ Copy new component above

### Paso 4: Update `src/App.tsx` imports (minimal change)
```tsx
// Add import
import { ModulePanel } from "./components/ModulePanel";

// In render, replace old Dashboard with new ModulePanel map
{status?.modules && Object.entries(status.modules).map(([name, info]: [string, any]) => (
  <ModulePanel key={name} module={{ name, port: info.port || 0, status: info.status === "ok" ? "online" : "offline", details: info }} />
))}
```

### Paso 5: Update `package.json` if needed
- React 18: ✅ Already have
- TypeScript: ✅ Already have
- No new dependencies needed!

---

## ✅ VALIDACIÓN

After deploy:
```bash
# Start frontend
cd operator_backend/frontend
npm run dev

# Expect:
# ✅ Chat sidebar visible
# ✅ Dark theme applied
# ✅ Typing indicator animation works
# ✅ Messages display with avatars + timestamps
# ✅ New session button works
# ✅ Error toast appears on error
# ✅ Mobile responsive (sidebar hidden on < 768px)
```

---

## 🚀 BONUS: v7.2 Ideas (Not v7.1)

- WebSocket real-time chat
- Markdown rendering (showdown.js)
- File upload support
- Session export/import
- Voice input (Web Speech API)
- Dark/Light mode toggle
- Custom theme colors

---

**Operator UI v7.1 — READY TO IMPLEMENT (zero breaking changes)** ✅

