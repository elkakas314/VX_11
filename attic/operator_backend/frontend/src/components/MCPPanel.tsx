import * as React from "react";
import { fetchJSON } from "../services/api";

export function MCPPanel() {
    const [audit, setAudit] = useState<any[]>([]);
    const [sandbox, setSandbox] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            try {
                const [auditData, sandboxData] = await Promise.all([
                    fetchJSON("/operator/mcp/audit"),
                    fetchJSON("/operator/mcp/sandbox"),
                ]);
                setAudit(auditData.logs || auditData || []);
                setSandbox(sandboxData.executions || sandboxData || []);
            } catch (e) {
                console.error("Error fetching MCP data:", e);
            } finally {
                setLoading(false);
            }
        };
        fetch();
    }, []);

    if (loading) return <div className="card"><h3>MCP (Auditoría)</h3><p>Cargando...</p></div>;

    return (
        <div className="card">
            <h3>MCP - Sandbox Auditoría</h3>
            <div style={{ marginBottom: "15px" }}>
                <h4 style={{ fontSize: "12px" }}>Ejecuciones Sandbox ({sandbox.length}):</h4>
                {sandbox.length > 0 ? (
                    <table style={{ width: "100%", fontSize: "10px" }}>
                        <thead>
                            <tr>
                                <th>Acción</th>
                                <th>Estado</th>
                                <th>Duración (ms)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sandbox.slice(0, 10).map((s, idx) => (
                                <tr key={idx}>
                                    <td>{(s.action || "?").substring(0, 20)}</td>
                                    <td>{s.status || "?"}</td>
                                    <td>{s.duration_ms || "0"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p style={{ fontSize: "11px" }}>Sin ejecuciones registradas</p>
                )}
            </div>
            <div>
                <h4 style={{ fontSize: "12px" }}>Logs de Auditoría ({audit.length}):</h4>
                {audit.length > 0 ? (
                    <div style={{ fontSize: "10px", maxHeight: "150px", overflow: "auto", background: "#f5f5f5", padding: "5px" }}>
                        {audit.slice(0, 15).map((a, idx) => (
                            <div key={idx} style={{ marginBottom: "3px" }}>
                                <strong>{a.level || "INFO"}:</strong> {(a.message || "").substring(0, 60)}...
                            </div>
                        ))}
                    </div>
                ) : (
                    <p style={{ fontSize: "11px" }}>Sin logs de auditoría</p>
                )}
            </div>
        </div>
    );
}
function useEffect(effect: React.EffectCallback, deps?: React.DependencyList): void {
    // Reexport/forward to React's implementation so the hook semantics are preserved.
    return React.useEffect(effect, deps);
}
function useState<T>(initialState: T | (() => T)): [T, React.Dispatch<React.SetStateAction<T>>] {
    return React.useState<T>(initialState as any);
}

