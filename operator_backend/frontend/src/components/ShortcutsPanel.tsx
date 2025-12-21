import React from "react";

type OnSend = (message: string, mode: string, metadata?: any) => Promise<any> | any;

const SHORTCUTS: Array<{ label: string; message: string; mode: string }> = [
  { label: "Status", message: "Dame el estado del stack VX11.", mode: "analitico" },
  { label: "DB Check", message: "Ejecuta quick_check/integrity_check/fk_check y resume.", mode: "analitico" },
  { label: "Retención (plan)", message: "Plan de retención DB (sin aplicar).", mode: "analitico" },
  { label: "Health", message: "Verifica /health de todos los servicios.", mode: "analitico" },
];

export function ShortcutsPanel({ onSend }: { onSend: OnSend }) {
  return (
    <div className="card">
      <div className="card-header">
        <h3 style={{ margin: 0 }}>Shortcuts</h3>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
        {SHORTCUTS.map((s) => (
          <button
            key={s.label}
            onClick={() => onSend(s.message, s.mode, { shortcut: s.label })}
            style={{ padding: "8px", borderRadius: "6px" }}
            title={s.message}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}

