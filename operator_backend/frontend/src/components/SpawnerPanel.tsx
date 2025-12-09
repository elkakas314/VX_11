import * as React from "react";
const { useEffect, useState } = React;
import { fetchJSON } from "../services/api";

export function SpawnerPanel() {
    const [spawns, setSpawns] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            try {
                const data = await fetchJSON("/operator/spawner/spawns");
                setSpawns(data.spawns || data || []);
            } catch (e) {
                console.error("Error fetching spawns:", e);
            } finally {
                setLoading(false);
            }
        };
        fetch();
        const interval = setInterval(fetch, 3000);
        return () => clearInterval(interval);
    }, []);

    const handleKill = async (spawnId: string) => {
        try {
            await fetchJSON(`/operator/spawner/spawns/${spawnId}/kill`, { method: "POST" });
            alert("Kill signal enviado");
        } catch (e) {
            alert("Error: " + e);
        }
    };

    if (loading) return <div className="card"><h3>Hijas (Spawner)</h3><p>Cargando...</p></div>;

    return (
        <div className="card">
            <h3>Hijas Activas (Spawner)</h3>
            {spawns.length === 0 ? (
                <p>Sin procesos activos</p>
            ) : (
                <div style={{ maxHeight: "300px", overflow: "auto" }}>
                    {spawns.slice(0, 15).map((spawn) => (
                        <div
                            key={spawn.spawn_id || spawn.id}
                            style={{
                                marginBottom: "8px",
                                padding: "5px",
                                border: "1px solid #ccc",
                                borderRadius: "3px",
                                background: spawn.status === "running" ? "#e8f5e9" : "#ffebee",
                            }}
                        >
                            <div style={{ fontSize: "12px", fontWeight: "bold" }}>
                                {spawn.cmd?.substring(0, 40) || spawn.name || "?"}
                            </div>
                            <div style={{ fontSize: "11px", color: "#666" }}>
                                PID: {spawn.pid || "?"} | Status: {spawn.status || "?"} | CPU: {spawn.cpu_percent || "?"}%
                            </div>
                            <div style={{ fontSize: "11px", color: "#666" }}>
                                Mem: {spawn.memory_mb || "?"}MB | TTL: {spawn.ttl || "?"}s
                            </div>
                            {spawn.status === "running" && (
                                <button
                                    onClick={() => handleKill(spawn.spawn_id)}
                                    style={{ fontSize: "10px", padding: "2px 5px", marginTop: "3px", background: "#f44336", color: "white" }}
                                >
                                    Kill
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
