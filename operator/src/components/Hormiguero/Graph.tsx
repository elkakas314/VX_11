/**
 * Hormiguero Graph Canvas
 * Displays Queen (center), Ants (nodes), Incidents (edges), Pheromones (animated flows)
 * Uses React Flow for DAG layout
 */

import React, { useCallback, useMemo } from "react";
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";

import { GraphNode as GraphNodeData, GraphEdge as GraphEdgeData } from "../../types/hormiguero";
import { GraphNodeComponent } from "./GraphNode";
import { HormiguerUIState } from "../../types/hormiguero";

interface HormiguerGraphProps {
  state: HormiguerUIState;
  onNodeClick?: (nodeId: string) => void;
}

const nodeTypes = {
  custom: GraphNodeComponent,
};

export const HormiguerGraph: React.FC<HormiguerGraphProps> = ({ state, onNodeClick }) => {
  // Build graph from state
  const graphData = useMemo(() => {
    const nodes: Node<GraphNodeData>[] = [];
    const edges: Edge<GraphEdgeData>[] = [];

    if (!state.queen) return { nodes, edges };

    // Queen node (center)
    nodes.push({
      id: "queen",
      data: {
        label: "QUEEN",
        entity: state.queen,
        status: state.queen.status,
      },
      position: { x: 0, y: 0 },
      type: "custom",
    });

    // Ant nodes (arranged in circle around Queen)
    const antCount = state.ants.length;
    const radius = 200;
    state.ants.forEach((ant, idx) => {
      const angle = (idx / antCount) * 2 * Math.PI;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      nodes.push({
        id: ant.id,
        data: {
          label: ant.role.split("_").pop() || "ANT",
          entity: ant,
          role: ant.role as any,
          status: ant.status,
          incident_count: state.incidents.filter((i) => i.ant_id === ant.id).length,
        },
        position: { x, y },
        type: "custom",
      });

      // Edge: Queen ↔ Ant
      edges.push({
        id: `queen-${ant.id}`,
        source: "queen",
        target: ant.id,
        data: {},
        animated: false,
      });
    });

    // Incident edges (Ant → Queen feedback)
    state.incidents.forEach((incident) => {
      if (incident.status === "open") {
        edges.push({
          id: `incident-${incident.id}`,
          source: incident.ant_id,
          target: "queen",
          data: {
            incident_id: incident.id,
          },
          animated: true,
          style: {
            stroke:
              incident.severity === "critical"
                ? "#ef4444"
                : incident.severity === "error"
                  ? "#f97316"
                  : incident.severity === "warning"
                    ? "#eab308"
                    : "#6b7280",
            strokeWidth: 2,
          },
        });
      }
    });

    return { nodes, edges };
  }, [state]);

  const [nodes, setNodes, onNodesChange] = useNodesState(graphData.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(graphData.edges);

  const handleNodeClick = useCallback(
    (event: any, node: Node) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

  return (
    <div className="w-full h-full" style={{ minHeight: "400px" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#aaa" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
};
