/**
 * EventCorrelationViewer Component
 * ===============================
 * Renders event correlation graph as DAG.
 * Lightweight visualization using Canvas + React Flow (if available).
 */

import React, { useMemo } from "react";
import { useEventCorrelations } from "../hooks/useEventCorrelations";
import { CorrelationNode, CorrelationEdge } from "../types/correlation";

export interface EventCorrelationViewerProps {
    enabled?: boolean;
    height?: string;
}

/**
 * Simple Canvas-based DAG renderer (fallback if React Flow unavailable)
 */
function SimpleDAGRenderer({
    nodes,
    edges,
    height = "400px",
}: {
    nodes: CorrelationNode[];
    edges: CorrelationEdge[];
    height: string;
}) {
    const canvasRef = React.useRef<HTMLCanvasElement>(null);

    React.useEffect(() => {
        if (!canvasRef.current || nodes.length === 0) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Clear canvas
        ctx.fillStyle = "#f5f5f5";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Simple layout: arrange nodes in columns by timestamp
        const sortedNodes = [...nodes].sort((a, b) => a.timestamp - b.timestamp);
        const nodePositions: Map<string, { x: number; y: number }> = new Map();

        const colWidth = canvas.width / (sortedNodes.length + 1);
        sortedNodes.forEach((node, idx) => {
            nodePositions.set(`${node.type}_${node.timestamp}`, {
                x: (idx + 1) * colWidth,
                y: canvas.height / 2,
            });
        });

        // Draw edges
        ctx.strokeStyle = "#ccc";
        ctx.lineWidth = 1;
        edges.forEach((edge) => {
            const src = nodePositions.get(edge.source);
            const tgt = nodePositions.get(edge.target);
            if (src && tgt) {
                ctx.beginPath();
                ctx.moveTo(src.x, src.y);
                ctx.lineTo(tgt.x, tgt.y);
                ctx.stroke();
            }
        });

        // Draw nodes
        sortedNodes.forEach((node, idx) => {
            const pos = nodePositions.get(`${node.type}_${node.timestamp}`);
            if (!pos) return;

            // Node color by severity
            const severityColors: Record<string, string> = {
                L1: "#4CAF50",
                L2: "#FFC107",
                L3: "#FF9800",
                L4: "#F44336",
            };
            ctx.fillStyle = severityColors[node.severity || "L1"] || "#2196F3";
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI);
            ctx.fill();

            // Label
            ctx.fillStyle = "#000";
            ctx.font = "10px monospace";
            ctx.textAlign = "center";
            ctx.fillText(node.type.split(".")[1] || "?", pos.x, pos.y + 20);
        });
    }, [nodes, edges]);

    return (
        <canvas
            ref={canvasRef}
            width={800}
            height={parseInt(height)}
            style={{
                border: "1px solid #ddd",
                borderRadius: "4px",
                backgroundColor: "#f5f5f5",
            }}
        />
    );
}

export function EventCorrelationViewer({
    enabled = false,
    height = "400px",
}: EventCorrelationViewerProps) {
    const { graph, loading, error, lastFetch } = useEventCorrelations(enabled);

    const stats = useMemo(() => {
        if (!graph) return null;
        return {
            nodes: graph.total_nodes,
            edges: graph.total_edges,
            density: graph.total_nodes > 0 ? (graph.total_edges / graph.total_nodes).toFixed(2) : "0",
        };
    }, [graph]);

    if (!enabled) {
        return (
            <div className="p-4 bg-gray-50 rounded border border-gray-300">
                <p className="text-sm text-gray-500">Correlation visualization disabled</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-red-50 rounded border border-red-300">
                <p className="text-sm text-red-700">Error loading correlations: {error}</p>
            </div>
        );
    }

    if (!graph) {
        return (
            <div className="p-4 bg-blue-50 rounded border border-blue-300">
                <p className="text-sm text-blue-700">
                    {loading ? "Loading correlation graph..." : "No correlation data yet"}
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            <div className="flex justify-between items-center text-xs text-gray-600">
                <span>
                    Nodes: {stats?.nodes} | Edges: {stats?.edges} | Density: {stats?.density}
                </span>
                <span>Updated {lastFetch > 0 ? new Date(lastFetch).toLocaleTimeString() : "never"}</span>
            </div>

            <SimpleDAGRenderer
                nodes={graph.nodes}
                edges={graph.edges}
                height={height}
            />

            <div className="text-xs text-gray-500 space-y-1">
                <p>
                    <strong>Legend:</strong> Green=L1 (info), Yellow=L2 (warning), Orange=L3 (error),
                    Red=L4 (critical)
                </p>
                <p>
                    <strong>Data source:</strong> /debug/events/correlations (polls every 10s)
                </p>
            </div>
        </div>
    );
}
