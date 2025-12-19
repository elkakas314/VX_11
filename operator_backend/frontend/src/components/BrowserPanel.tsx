import React from "react";

export function BrowserPanel() {
  return (
    <div className="card">
      <div className="card-header">
        <h3 style={{ margin: 0 }}>Browser</h3>
      </div>
      <div style={{ fontSize: "13px", color: "#9fb4cc" }}>
        Panel mínimo. Conecta con `operator_browser_task` vía backend.
      </div>
    </div>
  );
}

