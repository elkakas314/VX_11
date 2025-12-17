import * as React from "react";
const { useEffect, useState } = React;
import { fetchJSON } from "../services/api";

// Ensure JSX intrinsic elements exist in environments missing React typings
declare global {
    namespace JSX {
        interface IntrinsicElements {
            [elemName: string]: any;
        }
    }
}

export function HermesPanel() {
    const [models, setModels] = useState<any[]>([]);
    const [cli, setCli] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            try {
                const [modelsData, cliData] = await Promise.all([
                    fetchJSON("/operator/hermes/models"),
                    fetchJSON("/operator/hermes/cli"),
                ]);
                setModels(modelsData.models || modelsData || []);
                setCli(cliData.cli || cliData || []);
            } catch (e) {
                console.error("Error fetching hermes data:", e);
            } finally {
                setLoading(false);
            }
        };
        fetch();
    }, []);

    if (loading) return <div className="card"><h3>Hermes (Modelos)</h3><p>Cargando...</p></div>;

    return (
        <div className="card">
            <h3>Hermes - Modelos y CLI</h3>
            <div style={{ marginBottom: "15px" }}>
                <h4 style={{ fontSize: "12px" }}>Modelos Locales ({models.length}):</h4>
                {models.length > 0 ? (
                    <table style={{ width: "100%", fontSize: "11px" }}>
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Tamaño</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {models.slice(0, 8).map((m) => (
                                <tr key={m.name || m.id}>
                                    <td>{m.name || m.id}</td>
                                    <td>{m.size_gb || m.size_mb || "?"}GB</td>
                                    <td>{m.status || "available"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p style={{ fontSize: "11px" }}>Sin modelos locales</p>
                )}
            </div>
            <div>
                <h4 style={{ fontSize: "12px" }}>CLI Registrados ({cli.length}):</h4>
                {cli.length > 0 ? (
                    <ul style={{ fontSize: "11px", margin: "5px 0", paddingLeft: "20px" }}>
                        {cli.slice(0, 8).map((c) => (
                            <li key={c.name || c.id}>
                                {c.name} ({c.cli_type || "?"}) - {c.available ? "✓" : "✗"}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p style={{ fontSize: "11px" }}>Sin CLI registrados</p>
                )}
            </div>
        </div>
    );
}
