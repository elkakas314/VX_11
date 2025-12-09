import * as React from "react";
const { useEffect, useState } = React;
import { fetchJSON } from "../services/api";

export function HormigueroPanel() {
    const [queenTasks, setQueenTasks] = useState<any[]>([]);
    const [events, setEvents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            try {
                const [tasksData, eventsData] = await Promise.all([
                    fetchJSON("/operator/hormiguero/queen_tasks"),
                    fetchJSON("/operator/hormiguero/events"),
                ]);
                setQueenTasks(tasksData.queen_tasks || tasksData || []);
                setEvents(eventsData.events || eventsData || []);
            } catch (e) {
                console.error("Error fetching hormiguero data:", e);
            } finally {
                setLoading(false);
            }
        };
        fetch();
        const interval = setInterval(fetch, 6000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="card"><h3>Hormiguero (Reina)</h3><p>Cargando...</p></div>;

    return (
        <div className="card">
            <h3>Hormiguero - Tareas Reina</h3>
            <div style={{ marginBottom: "15px" }}>
                <h4 style={{ fontSize: "12px" }}>Tareas Reina ({queenTasks.length}):</h4>
                {queenTasks.length > 0 ? (
                    <table style={{ width: "100%", fontSize: "11px" }}>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Tipo</th>
                                <th>Estado</th>
                                <th>Módulo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {queenTasks.slice(0, 8).map((t) => (
                                <tr key={t.task_id || t.id}>
                                    <td>{(t.task_id || t.id || "?").slice(0, 6)}...</td>
                                    <td>{t.classification || t.type || "?"}</td>
                                    <td>{t.status || "pending"}</td>
                                    <td>{t.module_origin || "?"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p style={{ fontSize: "11px" }}>Sin tareas Reina</p>
                )}
            </div>
            <div>
                <h4 style={{ fontSize: "12px" }}>Eventos Recientes ({events.length}):</h4>
                {events.length > 0 ? (
                    <ul style={{ fontSize: "10px", margin: "5px 0", paddingLeft: "20px", maxHeight: "100px", overflow: "auto" }}>
                        {events.slice(0, 8).map((e, idx) => (
                            <li key={idx}>
                                [{e.source || "?"}] {e.event_type || "?"}: {(e.payload || "").substring(0, 40)}...
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p style={{ fontSize: "11px" }}>Sin eventos</p>
                )}
            </div>
        </div>
    );
}
