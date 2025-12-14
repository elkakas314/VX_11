import type { CanonicalEvent } from "../../types/canonical-events";

type Props = {
  alerts: CanonicalEvent[];
  correlations: CanonicalEvent[];
  snapshots: CanonicalEvent[];
  decisions: CanonicalEvent[];
  tensions: CanonicalEvent[];
  narratives: CanonicalEvent[];
  isConnected: boolean;
};

export function DashboardView(props: Props) {
  const totalEvents =
    props.alerts.length +
    props.correlations.length +
    props.snapshots.length +
    props.decisions.length +
    props.tensions.length +
    props.narratives.length;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
      {!props.isConnected && (
        <div
          style={{
            gridColumn: "1 / -1",
            borderRadius: "0.5rem",
            border: "1px solid rgba(217, 119, 6, 0.5)",
            background: "rgba(120, 53, 15, 0.4)",
            padding: "1rem",
            backdropFilter: "blur(12px)",
          }}
        >
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <div style={{ marginTop: "0.125rem", color: "rgba(253, 224, 71, 0.9)", fontSize: "0.875rem", animation: "pulse 2s infinite" }}>
              ◆
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: "0.875rem", fontWeight: "600", color: "#fde047", letterSpacing: "0.05em" }}>
                Los tentáculos aguardan señales…
              </div>
              <div style={{ marginTop: "0.25rem", fontSize: "0.75rem", color: "rgba(253, 224, 71, 0.6)" }}>
                Backend desconectado. UI renderiza sin dependencias.
              </div>
            </div>
          </div>
        </div>
      )}

      <PanelBox title="System Alerts" icon="🚨" count={props.alerts.length} />
      <PanelBox title="Correlations" icon="🔗" count={props.correlations.length} />
      <PanelBox title="Decisions" icon="🧠" count={props.decisions.length} />
      <PanelBox title="Tensions" icon="⚡" count={props.tensions.length} />
      <PanelBox title="Forensics" icon="📸" count={props.snapshots.length} />
      <PanelBox title="Narratives" icon="🎙️" count={props.narratives.length} />

      <div
        style={{
          gridColumn: "1 / -1",
          borderRadius: "0.5rem",
          border: "1px solid rgba(75, 85, 99, 0.6)",
          background: "rgba(31, 41, 55, 0.4)",
          padding: "0.75rem 1rem",
          fontSize: "0.75rem",
          color: "#999",
          backdropFilter: "blur(12px)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <span style={{ display: "inline-block", width: "0.5rem", height: "0.5rem", borderRadius: "50%", background: props.isConnected ? "#10b981" : "#f59e0b", marginRight: "0.5rem" }} />
          <span>{props.isConnected ? "◆ Conectado" : "○ Desconectado"}</span>
        </div>
        <div style={{ fontFamily: "monospace" }}>
          {totalEvents} eventos | {new Date().toLocaleTimeString()}
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}

function PanelBox({ title, icon, count }: { title: string; icon: string; count: number }) {
  return (
    <div
      style={{
        background: "linear-gradient(to bottom, rgba(55, 65, 81, 0.7), rgba(17, 24, 39, 0.6))",
        border: "1px solid rgba(75, 85, 99, 0.6)",
        borderRadius: "0.5rem",
        padding: "1rem",
        minHeight: "16rem",
        display: "flex",
        flexDirection: "column",
        backdropFilter: "blur(12px)",
        transition: "all 0.3s",
        cursor: "default",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "rgba(75, 85, 99, 0.8)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "rgba(75, 85, 99, 0.6)";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
        <span style={{ fontSize: "1.125rem" }}>{icon}</span>
        <h3 style={{ fontSize: "0.875rem", fontWeight: "600", color: "#d1d5db" }}>{title}</h3>
        <span style={{ marginLeft: "auto", fontSize: "0.75rem", background: "rgba(75, 85, 99, 0.6)", padding: "0.25rem 0.5rem", borderRadius: "0.25rem", color: "#999", fontFamily: "monospace" }}>
          {count}
        </span>
      </div>

      <div style={{ flex: 1, overflowY: "auto", fontSize: "0.75rem", color: "#666", display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center" }}>
        <div>
          <div style={{ fontSize: "1.875rem", opacity: 0.2, marginBottom: "0.5rem" }}>◇◆◇</div>
          <div>Los tentáculos aguardan…</div>
        </div>
      </div>
    </div>
  );
}
