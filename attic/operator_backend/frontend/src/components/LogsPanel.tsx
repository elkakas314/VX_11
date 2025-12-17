import * as React from "react";

export function LogsPanel() {
    const [logs, setLogs] = React.useState<any[]>([]);
    const [filter, setFilter] = React.useState("all");

    React.useEffect(() => {
        const ws = new WebSocket("ws://127.0.0.1:8000/ws/events");

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setLogs((prev) => [data, ...prev].slice(0, 100));
        };

        return () => ws.close();
    }, []);

    const filtered = filter === "all" ? logs : logs.filter((l) => l.channel === filter || l.source === filter);

    return (
        <div className="card">
            <h3>Stream Eventos</h3>
            <div style={{ marginBottom: "5px" }}>
                <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    style={{ fontSize: "11px", padding: "3px" }}
                >
                    <option value="all">Todos</option>
                    <option value="madre">Madre</option>
                    <option value="switch">Switch</option>
                    <option value="hermes">Hermes</option>
                    <option value="mcp">MCP</option>
                    <option value="spawner">Spawner</option>
                    <option value="hormiguero">Hormiguero</option>
                </select>
            </div>
            <div style={{ fontSize: "10px", maxHeight: "250px", overflow: "auto", background: "#1e1e1e", color: "#00ff00", padding: "5px", fontFamily: "monospace" }}>
                {filtered.length === 0 ? (
                    <div>Esperando eventos...</div>
                ) : (
                    filtered.map((log, idx) => (
                        <div key={idx} style={{ marginBottom: "2px", opacity: 1 - idx * 0.02 }}>
                            <span style={{ color: "#888" }}>
                                [{new Date(log.timestamp || Date.now()).toLocaleTimeString()}]
                            </span>
                            {" "}
                            <span style={{ color: "#ffff00" }}>{log.source || log.channel || "?"}</span>
                            {": "}
                            {log.message || JSON.stringify(log).substring(0, 60)}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
