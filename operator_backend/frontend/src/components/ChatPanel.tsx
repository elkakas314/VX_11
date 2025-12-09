import React, { useState, useRef, useEffect } from "react";
import { sendChat } from "../services/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize session ID on mount
  useEffect(() => {
    const id = `session_${Date.now()}`;
    setSessionId(id);
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim()) return;

    setSending(true);
    setError(null);

    // Add user message immediately
    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    try {
      // Call sendChat
      const resp = await sendChat(input, mode, { session_id: sessionId });

      if (resp?.error) {
        setError(`Error: ${resp.error}`);
      } else {
        // Extract response text
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
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "#1e1e1e",
        borderRadius: "8px",
        overflow: "hidden",
        boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px",
          background: "#2d2d2d",
          borderBottom: "1px solid #444",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h2 style={{ margin: 0, fontSize: "16px", color: "#fff", fontWeight: 600 }}>
          💬 Chat (Operator)
        </h2>
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          style={{
            padding: "6px 12px",
            background: "#404040",
            color: "#fff",
            border: "1px solid #555",
            borderRadius: "4px",
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          <option value="chat">General</option>
          <option value="mix">Mezcla</option>
          <option value="system">Sistema</option>
        </select>
      </div>

      {/* Session Info */}
      {sessionId && (
        <div
          style={{
            padding: "8px 16px",
            fontSize: "11px",
            color: "#888",
            background: "#252525",
            borderBottom: "1px solid #333",
          }}
        >
          Session: {sessionId.slice(-12)}
        </div>
      )}

      {/* Messages Area */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              color: "#666",
              fontSize: "14px",
              marginTop: "24px",
            }}
          >
            No messages yet. Start typing to begin.
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                gap: "8px",
              }}
            >
              <div
                style={{
                  maxWidth: "70%",
                  padding: "12px 16px",
                  background: msg.role === "user" ? "#0d7377" : "#404040",
                  color: "#fff",
                  borderRadius: "12px",
                  wordWrap: "break-word",
                  fontSize: "14px",
                  lineHeight: "1.4",
                }}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}
        {sending && (
          <div style={{ display: "flex", justifyContent: "flex-start", gap: "8px" }}>
            <div
              style={{
                padding: "12px 16px",
                background: "#404040",
                color: "#aaa",
                borderRadius: "12px",
                fontSize: "14px",
              }}
            >
              ⏳ Typing...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div
          style={{
            padding: "12px 16px",
            background: "#5d3d3d",
            color: "#ffb3b3",
            fontSize: "12px",
            borderTop: "1px solid #444",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* Input Area */}
      <div
        style={{
          padding: "16px",
          background: "#2d2d2d",
          borderTop: "1px solid #444",
          display: "flex",
          gap: "8px",
        }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (Shift+Enter for newline)"
          style={{
            flex: 1,
            padding: "10px 12px",
            background: "#404040",
            color: "#fff",
            border: "1px solid #555",
            borderRadius: "6px",
            fontSize: "14px",
            fontFamily: "inherit",
            resize: "none",
            minHeight: "40px",
            maxHeight: "80px",
          }}
          rows={1}
        />
        <button
          onClick={send}
          disabled={sending || !input.trim()}
          style={{
            padding: "10px 16px",
            background: sending || !input.trim() ? "#555" : "#0d7377",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: sending || !input.trim() ? "not-allowed" : "pointer",
            fontSize: "14px",
            fontWeight: 500,
            transition: "background 0.2s",
          }}
          onMouseOver={(e) => {
            if (!sending && input.trim()) {
              (e.target as HTMLButtonElement).style.background = "#0a5f6f";
            }
          }}
          onMouseOut={(e) => {
            if (!sending && input.trim()) {
              (e.target as HTMLButtonElement).style.background = "#0d7377";
            }
          }}
        >
          {sending ? "⏳" : "→"}
        </button>
      </div>
    </div>
  );
}

