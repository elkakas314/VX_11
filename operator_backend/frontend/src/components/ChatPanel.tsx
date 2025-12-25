import React, { useState, useRef, useEffect } from "react";
import { sendChat } from "../services/api";
import "./ChatPanel.css";

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
              className={`chat-sidebar-item ${activeSessionId === session.id ? "active" : ""
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
            <div className="chat-empty-state">
              <p>Inicia una conversación...</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-avatar">{msg.role === "user" ? "👤" : "🤖"}</div>
              <div className="message-content">
                <div className="message-bubble">{msg.content}</div>
                <div className="message-timestamp">{formatTime(msg.timestamp)}</div>
              </div>
            </div>
          ))}
          {sending && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
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

