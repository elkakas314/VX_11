import React, { useState, useEffect } from "react";

interface Node {
    id: string;
    label: string;
    state: "up" | "down" | "unknown";
    port?: number;
}

interface Edge {
    from: string;
    to: string;
    label: string;
}

interface MapData {
    nodes: Node[];
    edges: Edge[];
    counts: Record<string, number>;
    timestamp: string;
}

export function MapTab() {
    const [mapData, setMapData] = useState<MapData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchMap = async () => {
        setLoading(true);
        setError(null);
        try {
            // Try to fetch from operator_backend (if running)
            // Fallback: fetch through tentaculo_link proxy
            const res = await fetch("http://localhost:8011/api/map", {
                headers: { "X-VX11-Token": "vx11-local-token" },
            }).catch(async () => {
                // Fallback to tentaculo_link proxy if operator_backend not available
                return fetch("http://localhost:8000/api/map", {
                    headers: { "X-VX11-Token": "vx11-local-token" },
                });
            });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const data: MapData = await res.json();
            setMapData(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        } finally {
            setLoading(false);
        }
    };

    // Poll every 3 seconds
    useEffect(() => {
        fetchMap();
        const interval = setInterval(fetchMap, 3000);
        return () => clearInterval(interval);
    }, []);

    if (loading && !mapData) {
        return (
            <div className="p-6 space-y-4">
                <h2 className="text-2xl font-bold">System Map</h2>
                <p className="text-slate-400">Loading...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 space-y-4">
                <h2 className="text-2xl font-bold">System Map</h2>
                <div className="bg-red-900/30 border border-red-700 rounded p-4 text-red-200">
                    Error: {error}
                </div>
                <button
                    onClick={fetchMap}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (!mapData) {
        return (
            <div className="p-6 space-y-4">
                <h2 className="text-2xl font-bold">System Map</h2>
                <p className="text-slate-400">No data</p>
            </div>
        );
    }

    const nodeStateColor = (state: string) => {
        switch (state) {
            case "up":
                return "bg-green-600";
            case "down":
                return "bg-red-600";
            default:
                return "bg-gray-600";
        }
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">System Map</h2>
                <span className="text-slate-400 text-sm">
                    {new Date(mapData.timestamp).toLocaleTimeString()}
                </span>
            </div>

            {/* Services Status */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="font-semibold mb-4">Services ({mapData.counts.services_up || 0}/{mapData.counts.total_services || 0})</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                    {mapData.nodes.map((node) => (
                        <div
                            key={node.id}
                            className="bg-slate-700 rounded p-3 border border-slate-600 flex items-center justify-between"
                        >
                            <div className="flex-1">
                                <p className="text-sm font-medium">{node.label}</p>
                                <p className="text-xs text-slate-400">{node.id}</p>
                            </div>
                            <div className={`w-3 h-3 rounded-full ${nodeStateColor(node.state)}`} />
                        </div>
                    ))}
                </div>
            </div>

            {/* Connections */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="font-semibold mb-4">Connections</h3>
                <div className="space-y-2">
                    {mapData.edges.map((edge, idx) => (
                        <div
                            key={idx}
                            className="flex items-center justify-between p-2 bg-slate-700 rounded text-sm"
                        >
                            <span className="text-slate-300">
                                <span className="font-medium">{edge.from}</span>
                                {" → "}
                                <span className="font-medium">{edge.to}</span>
                            </span>
                            <span className="text-slate-500 text-xs">{edge.label}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Counts */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="font-semibold mb-3">Metrics</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(mapData.counts).map(([key, value]) => (
                        <div key={key} className="bg-slate-700 rounded p-3">
                            <p className="text-xs text-slate-400">{key.replace(/_/g, " ")}</p>
                            <p className="text-lg font-bold">{value}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Canvas-based SVG Map (Minimal) */}
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                <h3 className="font-semibold mb-4">Architecture Diagram</h3>
                <svg
                    viewBox="0 0 800 300"
                    className="w-full bg-slate-700/30 rounded max-h-96"
                >
                    {/* Nodes */}
                    {mapData.nodes.map((node, idx) => {
                        const x = 100 + (idx % 2) * 300;
                        const y = 100 + Math.floor(idx / 2) * 100;
                        const color = node.state === "up" ? "#22c55e" : node.state === "down" ? "#ef4444" : "#6b7280";

                        return (
                            <g key={node.id}>
                                <circle cx={x} cy={y} r="40" fill={color} opacity="0.3" stroke={color} strokeWidth="2" />
                                <text x={x} y={y} textAnchor="middle" dy="0.3em" fill="white" fontSize="12" fontWeight="bold">
                                    {node.id}
                                </text>
                            </g>
                        );
                    })}

                    {/* Edges */}
                    {mapData.edges.map((edge, idx) => {
                        const nodeFrom = mapData.nodes.find((n) => n.id === edge.from);
                        const nodeTo = mapData.nodes.find((n) => n.id === edge.to);

                        if (!nodeFrom || !nodeTo) return null;

                        const fromIdx = mapData.nodes.indexOf(nodeFrom);
                        const toIdx = mapData.nodes.indexOf(nodeTo);

                        const x1 = 100 + (fromIdx % 2) * 300;
                        const y1 = 100 + Math.floor(fromIdx / 2) * 100;
                        const x2 = 100 + (toIdx % 2) * 300;
                        const y2 = 100 + Math.floor(toIdx / 2) * 100;

                        return (
                            <line key={`edge-${idx}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#64748b" strokeWidth="2" markerEnd="url(#arrowhead)" />
                        );
                    })}

                    {/* Arrow marker */}
                    <defs>
                        <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                            <polygon points="0 0, 10 3, 0 6" fill="#64748b" />
                        </marker>
                    </defs>
                </svg>
            </div>
        </div>
    );
}
