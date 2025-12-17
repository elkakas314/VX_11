import React, { useMemo, useState } from "react";
import type { Node } from "reactflow";

type Props = {
  node: Node;
  incidents: any[];
  onClose: () => void;
  onScan: () => Promise<void>;
  onClean: () => Promise<void>;
};

export function NodeDrawer({ node, incidents, onClose, onScan, onClean }: Props) {
  const [loading, setLoading] = useState<"scan" | "clean" | null>(null);
  const scopedIncidents = useMemo(() => incidents.filter((i: any) => (i.module || i.service || "").includes(node.id)), [incidents, node.id]);

  const trigger = async (action: "scan" | "clean") => {
    setLoading(action);
    try {
      if (action === "scan") await onScan();
      else await onClean();
    } finally {
      setLoading(null);
    }
  };

  return (
    <div
      role="dialog"
      aria-label={`Detalle ${node.data?.label || node.id}`}
      style={{
        position: "absolute",
        right: 0,
        top: 0,
        height: "100%",
        width: 320,
        background: "#0f172a",
        borderLeft: "1px solid #1f2f45",
        boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ color: "#9fb4cc", fontSize: 12 }}>Nodo</div>
          <div style={{ color: "#e5e7eb", fontWeight: 700 }}>{node.data?.label || node.id}</div>
        </div>
        <button onClick={onClose} style={{ color: "#9fb4cc", background: "transparent", border: "none", cursor: "pointer" }}>
          ✕
        </button>
      </div>
      <div style={{ fontSize: 12, color: "#9fb4cc" }}>
        Estado: <span style={{ color: "#e5e7eb" }}>{node.data?.status || "unknown"}</span>
        <br />
        Incidentes: {node.data?.incidents ?? 0}
        <br />
        Latencia: {node.data?.latency_ms ? `${node.data.latency_ms} ms` : "—"}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button className="chip" disabled={loading === "scan"} onClick={() => trigger("scan")}>
          {loading === "scan" ? "Escaneando..." : "Scan"}
        </button>
        <button className="chip" disabled={loading === "clean"} onClick={() => trigger("clean")}>
          {loading === "clean" ? "Limpiando..." : "Clean"}
        </button>
      </div>
      <div style={{ fontSize: 12, color: "#9fb4cc", flex: 1, overflowY: "auto", border: "1px solid #1f2f45", borderRadius: 8, padding: 8 }}>
        <div style={{ fontWeight: 700, color: "#e5e7eb", marginBottom: 6 }}>Incidentes relacionados</div>
        {scopedIncidents.length === 0 && <div style={{ color: "#7c92b0" }}>Sin incidentes para este nodo.</div>}
        {scopedIncidents.slice(0, 20).map((inc, idx) => (
          <div key={idx} style={{ borderBottom: "1px solid #1f2f45", padding: "6px 0" }}>
            <div style={{ color: "#e5e7eb" }}>{inc.type || inc.incident_type || "incidente"}</div>
            <div style={{ color: "#f59e0b" }}>Sev: {inc.severity || "n/a"} · {inc.detected_at || inc.timestamp || ""}</div>
            <div style={{ color: "#9fb4cc" }}>{(inc.detail || inc.details || "").toString().slice(0, 120)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
