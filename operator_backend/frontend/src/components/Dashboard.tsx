import React from "react";

type Props = {
  status: any;
  events: any[];
  onValidateManifest: (manifest: string) => void;
};

export function Dashboard({ status, events, onValidateManifest }: Props) {
  const modules = status?.modules || {};
  return (
    <div className="card">
      <div className="card-header">
        <h2>System Dashboard</h2>
        <button onClick={() => onValidateManifest("{}")}>Validate Manifest</button>
      </div>
      <div className="grid">
        {Object.entries(modules).map(([name, mod]: any) => {
          const ok = mod.status === "ok" || mod.ok || mod.code === 200;
          const detail = mod.status || mod.code || (ok ? "ok" : "fail");
          return (
            <div key={name} className={`chip ${ok ? "ok" : "fail"}`}>
              <strong>{name}</strong>
              <span>{detail}</span>
            </div>
          );
        })}
        {!Object.keys(modules).length && <div className="chip fail">Sin datos de health</div>}
      </div>
      <div className="events">
        <h3>Recent Events</h3>
        <ul>
          {events.slice(0, 5).map((e, idx) => (
            <li key={idx}>
              <strong>{e.channel || e.type || "event"}</strong> — {e.summary || e.type || ""} {e.source ? `(${e.source})` : ""}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
