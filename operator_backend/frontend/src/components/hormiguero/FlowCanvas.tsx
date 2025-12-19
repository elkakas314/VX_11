import React, { Suspense, useMemo, useState } from "react";
import ReactFlow, { Background, Controls, MiniMap, Node, Edge, useEdgesState, useNodesState } from "reactflow";
import "reactflow/dist/style.css";
import { statusColor } from "./helpers";
import { NodeDrawer } from "./NodeDrawer";

type FlowProps = {
  modules?: Record<string, any>;
  incidents?: any[];
  onScan: () => Promise<void>;
  onClean: () => Promise<void>;
};

const defaultPositions = [
  { x: 0, y: 0 },
  { x: 220, y: 0 },
  { x: 440, y: 0 },
  { x: 660, y: 0 },
  { x: 0, y: 180 },
  { x: 220, y: 180 },
  { x: 440, y: 180 },
  { x: 660, y: 180 },
];

const MODULE_ORDER = ["tentaculo_link", "madre", "switch", "hermes", "hormiguero", "manifestator", "mcp", "shub", "spawner", "operator"];

export function FlowCanvas({ modules = {}, incidents = [], onScan, onClean }: FlowProps) {
  const [drawerNode, setDrawerNode] = useState<Node | null>(null);

  const { nodes, edges } = useMemo(() => {
    const baseNodes: Node[] = MODULE_ORDER.map((name, idx) => {
      const pos = defaultPositions[idx % defaultPositions.length];
      const mod = modules[name] || {};
      const openIncidents = name === "hormiguero" ? incidents.filter((i: any) => (i.status || "open") !== "resolved") : [];
      return {
        id: name,
        data: {
          label: name,
          status: mod.status || "unknown",
          mode: mod.mode,
          incidents: mod.incidents_open ?? openIncidents.length,
          latency_ms: mod.latency_ms,
        },
        position: { x: pos.x + (idx % 2 === 0 ? 10 : -10), y: pos.y + (idx % 3) * 16 },
        style: {
          background: "#0f172a",
          color: "#e5e7eb",
          border: `2px solid ${statusColor(mod.status)}`,
          borderRadius: 12,
          padding: 12,
          boxShadow: "0 10px 30px rgba(0,0,0,0.35)",
        },
      };
    });

    const baseEdges: Edge[] = MODULE_ORDER.slice(0, -1).map((id, idx) => ({
      id: `${id}-${MODULE_ORDER[idx + 1]}`,
      source: id,
      target: MODULE_ORDER[idx + 1],
      style: { stroke: "#1f2f45", strokeWidth: 1.6 },
      animated: true,
    }));

    return { nodes: baseNodes, edges: baseEdges };
  }, [modules, incidents.length]);

  const [nodesState, , onNodesChange] = useNodesState(nodes);
  const [edgesState, , onEdgesChange] = useEdgesState(edges);

  return (
    <div style={{ height: 360, borderRadius: 12, overflow: "hidden", background: "#0b1220" }}>
      <Suspense fallback={<div style={{ padding: 12, color: "#9fb4cc" }}>Cargando mapa…</div>}>
        <ReactFlow
          nodes={nodesState}
          edges={edgesState}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          onNodeClick={(_, node) => setDrawerNode(node)}
        >
          <MiniMap pannable zoomable style={{ background: "#0f172a" }} />
          <Controls showInteractive={false} />
          <Background gap={18} color="#1f2f45" />
        </ReactFlow>
      </Suspense>
      {drawerNode && (
        <NodeDrawer
          node={drawerNode}
          incidents={incidents}
          onClose={() => setDrawerNode(null)}
          onScan={onScan}
          onClean={onClean}
        />
      )}
    </div>
  );
}
