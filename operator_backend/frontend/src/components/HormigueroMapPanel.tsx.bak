import React, { useMemo, useState } from "react";
import { scanHormiguero, cleanHormiguero } from "../services/api";
import { FlowCanvas } from "./hormiguero/FlowCanvas";
import { D3Overlay } from "./hormiguero/D3Overlay";
import { statusColor } from "./hormiguero/helpers";

type Props = {
  status?: any;
  events?: any[];
};

export function HormigueroMapPanel({ status, events = [] }: Props) {
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const incidents = status?.hormiguero?.incidents || [];
  const incidentTypes = status?.hormiguero?.types || [];
  const severity: "ok" | "warn" | "critical" =
    incidents.some((i: any) => (i.severity || "").includes("critical"))
      ? "critical"
      : incidents.some((i: any) => (i.severity || "").includes("warning"))
      ? "warn"
      : "ok";

  const moduleMap = useMemo(() => {
    const collected: Record<string, any> = {};
    (status?.modules_list || []).forEach((m: any) => {
      if (m?.name) collected[m.name] = m;
    });
    Object.assign(collected, status?.modules || {});
    return collected;
  }, [status]);

  const handleHormigueroAction = async (action: "scan" | "clean") => {
    setActionLoading(true);
    setActionMsg(null);
    try {
      const res = action === "scan" ? await scanHormiguero() : await cleanHormiguero();
      setActionMsg(res?.ok ? `${action} lanzado` : res?.error || "Error");
    } catch (e: any) {
      setActionMsg(e?.message || "Error");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="card" style={{ position: "relative", overflow: "hidden" }}>
      <div className="card-header">
        <h3 style={{ margin: 0 }}>Mapa VX11 + Hormiguero</h3>
        <div style={{ fontSize: "11px", color: "#9fb4cc" }}>
          Incidentes: {incidents.length} · Tipos: {incidentTypes.length || "0"}
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <FlowCanvas modules={moduleMap} incidents={incidents} onScan={() => handleHormigueroAction("scan")} onClean={() => handleHormigueroAction("clean")} />
        <D3Overlay severity={severity} />
      </div>
      {actionMsg && <div style={{ color: "#9fb4cc", fontSize: "12px", marginTop: "4px" }}>{actionMsg}</div>}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "8px", marginTop: "8px", fontSize: "12px" }}>
        <div className="chip">
          <span>Incidentes</span>
          <strong>{incidents.length}</strong>
        </div>
        <div className="chip">
          <span>Tipos</span>
          <strong>{incidentTypes.length || "—"}</strong>
        </div>
        <div className="chip" style={{ borderColor: statusColor(severity) }}>
          <span>Severidad</span>
          <strong style={{ color: statusColor(severity) }}>{severity}</strong>
        </div>
        <div className="chip" style={{ justifyContent: "space-between" }}>
          <button className="chip" onClick={() => handleHormigueroAction("scan")} disabled={actionLoading}>
            {actionLoading ? "..." : "Scan"}
          </button>
          <button className="chip" onClick={() => handleHormigueroAction("clean")} disabled={actionLoading}>
            {actionLoading ? "..." : "Clean"}
          </button>
        </div>
      </div>
    </div>
  );
}
