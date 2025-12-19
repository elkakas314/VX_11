import React from "react";

export function SimpleApp() {
  return (
    <div style={{ padding: "12px", fontFamily: "system-ui, sans-serif" }}>
      <h2 style={{ marginTop: 0 }}>Operator (Simple Mode)</h2>
      <p style={{ color: "#546b86" }}>
        UI mínima: desactiva el modo simple quitando `?simple=1` o
        `VITE_OPERATOR_SIMPLE_MODE=true`.
      </p>
    </div>
  );
}

