import React, { useState } from "react";

type OnSend = (message: string, mode: string, metadata?: any) => Promise<any> | any;

export function DeepSeekHelper({ onSend }: { onSend: OnSend }) {
  const [message, setMessage] = useState("");

  return (
    <div className="card">
      <div className="card-header">
        <h3 style={{ margin: 0 }}>DeepSeek Helper</h3>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Prompt rápido..."
          style={{ minHeight: "70px", padding: "8px", borderRadius: "6px" }}
        />
        <button
          onClick={() => onSend(message, "analitico", { profile: "deepseek-helper" })}
          disabled={!message.trim()}
          style={{ padding: "8px", borderRadius: "6px" }}
        >
          Enviar
        </button>
      </div>
    </div>
  );
}

