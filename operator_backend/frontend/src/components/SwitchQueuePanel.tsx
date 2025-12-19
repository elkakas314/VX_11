import * as React from "react";
import { useEffect, useState } from "react";
import { fetchJSON } from "../services/api";

export function SwitchQueuePanel() {
    const [queue, setQueue] = useState<any>(null);
    const [models, setModels] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            try {
                const [queueData, modelsData] = await Promise.all([
                    fetchJSON("/operator/switch/queue"),
                    fetchJSON("/operator/switch/models"),
                ]);
                setQueue(queueData);
                setModels(modelsData.models || modelsData || []);
            } catch (e) {
                console.error("Error fetching queue:", e);
            } finally {
                setLoading(false);
            }
        };
        fetch();
        const interval = setInterval(fetch, 4000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="card"><h3>Cola (Switch)</h3><p>Cargando...</p></div>;

    return (
        <div className="card">
            <h3>Cola Prioritaria (Switch)</h3>
            {queue ? (
                <>
                    <div style={{ marginBottom: "10px", padding: "5px", background: "#f9f9f9" }}>
                        <div><strong>Modelo Activo:</strong> {queue.active_model || "ninguno"}</div>
                        <div><strong>Tamaño Cola:</strong> {queue.size || 0}</div>
                        <div><strong>Modo:</strong> {queue.mode || "BALANCED"}</div>
                    </div>
                    <div>
                        <h4 style={{ fontSize: "12px", margin: "5px 0" }}>Próximas Tareas:</h4>
                        {queue.next_tasks && queue.next_tasks.length > 0 ? (
                            <ol style={{ fontSize: "11px", margin: "5px 0", paddingLeft: "20px" }}>
                                {queue.next_tasks.slice(0, 5).map((task: any, idx: number) => (
                                    <li key={idx}>
                                        [{task.priority}] {(task.prompt_preview || task.source || "task").substring(0, 30)}... (ETA: {task.estimated_wait_s || "?"}s)
                                    </li>
                                ))}
                            </ol>
                        ) : (
                            <p style={{ fontSize: "11px" }}>Cola vacía</p>
                        )}
                    </div>
                    <div>
                        <h4 style={{ fontSize: "12px", margin: "5px 0" }}>Modelos Disponibles:</h4>
                        {models.length > 0 ? (
                            <select style={{ width: "100%", fontSize: "11px" }}>
                                <option>Seleccionar...</option>
                                {models.map((m) => (
                                    <option key={m.name || m.id}>
                                        {m.name || m.id} ({m.size || "?"}MB)
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <p style={{ fontSize: "11px" }}>Sin modelos</p>
                        )}
                    </div>
                </>
            ) : (
                <p>No hay datos de cola</p>
            )}
        </div>
    );
}
