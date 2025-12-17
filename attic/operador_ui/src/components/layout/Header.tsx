interface HeaderProps {
    isConnected: boolean;
    error?: string | null;
}

export function Header({ isConnected, error }: HeaderProps) {
    const statusText = isConnected ? "Los tentáculos despiertan" : "Los tentáculos aguardan señales…";
    const statusColor = isConnected ? "#10b981" : "#f59e0b";

    return (
        <header
            style={{
                background: "linear-gradient(to right, #030712, #1a1a2e)",
                borderBottom: "1px solid rgba(75, 85, 99, 0.6)",
                padding: "1rem 1.5rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                backdropFilter: "blur(12px)",
            }}
        >
            <div>
                <h2 style={{ fontSize: "1.125rem", fontWeight: "bold", letterSpacing: "0.05em" }}>
                    ◇ VX11 Operator
                </h2>
                <p style={{ fontSize: "0.75rem", marginTop: "0.25rem", color: statusColor }}>{statusText}</p>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                {error && (
                    <div
                        style={{
                            fontSize: "0.75rem",
                            color: "#fca5a5",
                            background: "rgba(127, 29, 29, 0.3)",
                            padding: "0.375rem 0.75rem",
                            borderRadius: "0.375rem",
                            border: "1px solid rgba(153, 27, 27, 0.6)",
                            maxWidth: "30rem",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                        }}
                    >
                        {error}
                    </div>
                )}
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <div
                        style={{
                            width: "0.5rem",
                            height: "0.5rem",
                            borderRadius: "50%",
                            background: statusColor,
                            animation: "pulse 2s infinite",
                        }}
                    />
                    <span style={{ fontSize: "0.875rem", color: statusColor }}>
                        {isConnected ? "● Activo" : "○ Dormido"}
                    </span>
                </div>
            </div>

            <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
        </header>
    );
}
