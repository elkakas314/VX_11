import React, { useMemo } from "react";
import { ManifestEditor } from "./manifestator/ManifestEditor";

type Props = {
  status?: any;
  events?: any[];
};

export function ManifestatorPanel({ status, events = [] }: Props) {
  const incidents = useMemo(
    () => (events || []).filter((e) => e.type === "incident" && (e.module === "hormiguero" || e.data?.module === "hormiguero")),
    [events]
  );
  const recentEvents = useMemo(() => (events || []).slice(0, 12), [events]);

  return (
    <div className="card">
      <h3>Manifestator Monaco</h3>
      <div style={{ fontSize: "12px", marginBottom: "10px" }}>
        <div>Drift (via Hormiguero incidentes): {incidents.length > 0 ? "detected" : "none"}</div>
        <div>Módulos observados: {status?.modules_list ? status.modules_list.length : "—"}</div>
      </div>

      <ManifestEditor defaultValue="# Escribe o pega el manifest (YAML/JSON)" />

      <div style={{ fontSize: "11px", marginTop: "10px" }}>
        <strong>Eventos relevantes (12):</strong>
        <div style={{ maxHeight: "160px", overflow: "auto", marginTop: "6px" }}>
          {recentEvents.length === 0 && <div style={{ color: "#8aa0ba" }}>Sin eventos</div>}
          {recentEvents.map((ev, idx) => (
            <div key={idx} style={{ borderBottom: "1px solid #1f2d3d", padding: "4px 0" }}>
              <div>{ev.type} · {ev.module || ev.data?.module || "n/a"}</div>
              <div style={{ color: "#9fb4cc" }}>{ev.timestamp}</div>
              <div style={{ color: "#b7c7dd" }}>{JSON.stringify(ev.data || ev.payload || {}).slice(0, 80)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
