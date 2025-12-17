import { Component, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { errorMessage: string | null };

export class AppErrorBoundary extends Component<Props, State> {
  state: State = { errorMessage: null };

  static getDerivedStateFromError(error: unknown): State {
    const message =
      error instanceof Error
        ? error.message
        : typeof error === "string"
          ? error
          : "Error desconocido";
    return { errorMessage: message };
  }

  render() {
    if (this.state.errorMessage) {
      return (
        <div style={{ display: "flex", height: "100vh", background: "#030712", color: "#e5e7eb", overflow: "hidden" }}>
          <div style={{ pointerEvents: "none", position: "fixed", inset: 0, background: "radial-gradient(700px circle at 20% 0%, rgba(99,102,241,0.1), transparent 45%)" }} />

          <aside style={{ width: "16rem", background: "linear-gradient(to bottom, #030712, #1a1a2e, #000)", borderRight: "1px solid rgba(75, 85, 99, 0.7)", height: "100vh", display: "flex", flexDirection: "column", padding: "1rem", minWidth: "250px" }}>
            <div style={{ marginBottom: "2rem" }}>
              <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#6366f1" }}>VX11</h2>
              <p style={{ fontSize: "0.75rem", color: "#888", marginTop: "0.25rem" }}>Operator — observa el silencio</p>
            </div>
            <div style={{ marginTop: "auto", paddingTop: "1rem", borderTop: "1px solid #333" }}>
              <div style={{ fontSize: "0.75rem", color: "#888", marginBottom: "0.5rem" }}>STATUS</div>
              <div style={{ background: "#1a1a2e", borderRadius: "0.375rem", padding: "0.5rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <span style={{ display: "inline-block", width: "0.5rem", height: "0.5rem", borderRadius: "50%", background: "#f59e0b" }} />
                  <span style={{ fontSize: "0.75rem" }}>Modo resiliente</span>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#666", marginTop: "0.25rem" }}>Los tentáculos aguardan señales…</div>
              </div>
            </div>
          </aside>

          <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
            <header style={{ background: "linear-gradient(to right, #030712, #1a1a2e)", borderBottom: "1px solid rgba(75, 85, 99, 0.6)", padding: "1rem 1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ fontSize: "1.125rem", fontWeight: "bold" }}>◇ VX11 Operator — ERROR</h2>
                <p style={{ fontSize: "0.75rem", marginTop: "0.25rem", color: "#f59e0b" }}>El abismo observa</p>
              </div>
              <div style={{ fontSize: "0.75rem", color: "#fca5a5", background: "rgba(127, 29, 29, 0.3)", border: "1px solid rgba(153, 27, 27, 0.6)", borderRadius: "0.375rem", padding: "0.5rem 0.75rem" }}>
                {this.state.errorMessage}
              </div>
            </header>
            <main style={{ flex: 1, overflowY: "auto", padding: "1.5rem", background: "#030712", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
              <div style={{ minHeight: "16rem", borderRadius: "0.5rem", border: "1px solid rgba(75, 85, 99, 0.6)", background: "rgba(31, 41, 55, 0.4)" }} />
              <div style={{ minHeight: "16rem", borderRadius: "0.5rem", border: "1px solid rgba(75, 85, 99, 0.6)", background: "rgba(31, 41, 55, 0.4)" }} />
              <div style={{ minHeight: "16rem", borderRadius: "0.5rem", border: "1px solid rgba(75, 85, 99, 0.6)", background: "rgba(31, 41, 55, 0.4)" }} />
            </main>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
