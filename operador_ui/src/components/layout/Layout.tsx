import type { ReactNode } from "react";
import { Header } from "./Header";

interface LayoutProps {
    children: ReactNode;
    isConnected: boolean;
    error?: string | null;
}

function Sidebar({ isConnected }: { isConnected: boolean }) {
    return (
        <aside
            style={{
                width: "16rem",
                background: "linear-gradient(to bottom, #030712, #1a1a2e, #000)",
                borderRight: "1px solid #1a1a2e",
                padding: "1.5rem",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
                minHeight: "100vh",
            }}
        >
            <div
                style={{
                    fontSize: "1.25rem",
                    fontWeight: "bold",
                    background: "linear-gradient(135deg, #8b5cf6, #ec4899)",
                    backgroundClip: "text",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    marginBottom: "1rem",
                }}
            >
                Tentáculos de Dagón
            </div>

            <nav style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <div style={{ fontSize: "0.875rem", color: "#999", textTransform: "uppercase", marginTop: "1rem" }}>
                    Narrativa
                </div>
                <div
                    style={{
                        padding: "0.5rem 1rem",
                        background: "rgba(139, 92, 246, 0.1)",
                        borderLeft: "3px solid #8b5cf6",
                        borderRadius: "0.25rem",
                    }}
                >
                    Dashboard
                </div>
            </nav>

            <div style={{ marginTop: "auto", fontSize: "0.875rem", color: "#666" }}>
                {isConnected ? (
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <div
                            style={{
                                width: "0.5rem",
                                height: "0.5rem",
                                background: "#10b981",
                                borderRadius: "50%",
                                animation: "pulse 2s infinite",
                            }}
                        />
                        Conectado
                    </div>
                ) : (
                    <div>Desconectado</div>
                )}
            </div>

            <style>{`
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            `}</style>
        </aside>
    );
}

export function Layout({ children, isConnected, error }: LayoutProps) {
    return (
        <div
            style={{
                display: "flex",
                height: "100vh",
                width: "100%",
                background: "#030712",
                color: "#e5e7eb",
                overflow: "hidden",
            }}
        >
            <Sidebar isConnected={isConnected} />
            <div style={{ flex: 1, display: "flex", flexDirection: "column", width: "100%" }}>
                <Header isConnected={isConnected} error={error} />
                <main
                    style={{
                        flex: 1,
                        overflowY: "auto",
                        padding: "1.5rem",
                        background: "#030712",
                    }}
                >
                    {children}
                </main>
            </div>
        </div>
    );
}
