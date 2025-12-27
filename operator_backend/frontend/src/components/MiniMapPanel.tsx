import * as React from "react";
import "./MiniMapPanel.css";

type Props = {
    status: any;
};

export function MiniMapPanel({ status }: Props) {
    const modules = React.useMemo(() => {
        const mods = status?.modules || {};
        return [
            { name: "Tentáculo Link", port: 8000 },
            { name: "Madre", port: 8001 },
            { name: "Switch", port: 8002 },
            { name: "Hermes", port: 8003 },
            { name: "Hormiguero", port: 8004 },
            { name: "Manifestator", port: 8005 },
            { name: "MCP", port: 8006 },
            { name: "Shub", port: 8007 },
            { name: "Spawner", port: 8008 },
        ].map((mod) => {
            const key = mod.name.toLowerCase();
            const data = mods[key] || {};
            const ok = data.ok === true || data.status === "ok";
            return { ...mod, ok };
        });
    }, [status]);

    return (
        <div className="card">
            <h3>Sistema - MiniMap</h3>
            <div className="minimap-grid">
                {modules.map((mod) => (
                    <div
                        key={mod.port}
                        className={`minimap-item ${mod.ok ? "minimap-ok" : "minimap-fail"}`}
                        title={`${mod.name} (${mod.port})`}
                    >
                        <div>{mod.name}</div>
                        <div style={{ fontSize: "9px", opacity: 0.8 }}>{mod.ok ? "✓" : "✗"}</div>
                    </div>
                ))}
            </div>
            <div className="minimap-footer">
                Operador: <strong>🟢</strong> | Total módulos: <strong>{modules.length}</strong> |
                OK: <strong>{modules.filter((m) => m.ok).length}/{modules.length}</strong>
            </div>
        </div>
    );
}
