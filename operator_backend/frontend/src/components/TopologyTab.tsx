import React, { useState, useEffect } from "react";

interface Node {
    id: string;
    label: string;
    status: "healthy" | "down" | "dormant" | "window-only";
    port?: number;
}

interface Edge {
    from: string;
    to: string;
    label: string;
}

interface Topology {
    nodes: Node[];
    edges: Edge[];
    metadata?: {
        policy?: string;
        entrypoint?: string;
        [key: string]: any;
    };
}

export function TopologyTab() {
    const [topology, setTopology] = useState<Topology | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadTopology();
        const interval = setInterval(loadTopology, 15000); // Refresh every 15s
        return () => clearInterval(interval);
    }, []);

    const loadTopology = async () => {
        try {
            setError(null);
            const res = await fetch("http://localhost:8000/api/topology");
            if (res.ok) {
                const data = await res.json();
                setTopology(data.data || data);
            } else {
                throw new Error(`HTTP ${res.status}`);
            }
            setLoading(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load topology");
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-slate-400">Loading topology...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-900/30 border border-red-700 rounded p-4 m-4">
                <div className="text-red-200">Error: {error}</div>
            </div>
        );
    }

    const statusColorMap = {
        healthy: "text-green-400",
        down: "text-red-400",
        dormant: "text-gray-400",
        "window-only": "text-yellow-400",
    };

    const statusBgMap = {
        healthy: "bg-green-900/20 border-green-700",
        down: "bg-red-900/20 border-red-700",
        dormant: "bg-gray-900/20 border-gray-700",
        "window-only": "bg-yellow-900/20 border-yellow-700",
    };

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-bold mb-2">System Topology</h2>
                <p className="text-slate-400">VX11 service architecture and connections</p>
            </div>

            {/* Policy Badge */}
            {topology?.metadata?.policy && (
                <div className="bg-blue-900/20 border border-blue-700 rounded p-3">
                    <div className="text-sm text-blue-200">
                        <strong>Policy:</strong> {topology.metadata.policy}
                    </div>
                    {topology.metadata.entrypoint && (
                        <div className="text-xs text-blue-300 mt-1">
                            Entrypoint: <span className="font-mono">{topology.metadata.entrypoint}</span>
                        </div>
                    )}
                </div>
            )}

            {/* Nodes */}
            <div>
                <h3 className="text-xl font-bold mb-3 text-slate-200">Services</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {topology?.nodes?.map((node) => (
                        <div
                            key={node.id}
                            className={`rounded border p-3 ${statusBgMap[node.status as keyof typeof statusBgMap]}`}
                        >
                            <div className="flex items-center justify-between mb-2">
                                <div className="font-mono text-sm font-bold text-slate-300">{node.id}</div>
                                <span className={`text-xs font-bold ${statusColorMap[node.status as keyof typeof statusColorMap]}`}>
                                    {node.status.toUpperCase()}
                                </span>
                            </div>
                            <div className="text-sm text-slate-400">{node.label}</div>
                            {node.port && (
                                <div className="text-xs text-slate-500 mt-2">
                                    Port: <span className="font-mono">{node.port}</span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Edges / Connections */}
            {topology?.edges && topology.edges.length > 0 && (
                <div>
                    <h3 className="text-xl font-bold mb-3 text-slate-200">Allowed Flows</h3>
                    <div className="bg-slate-800 rounded border border-slate-700 p-4">
                        <div className="space-y-2">
                            {topology.edges.map((edge, idx) => (
                                <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-b-0">
                                    <div className="font-mono text-sm">
                                        <span className="text-blue-400">{edge.from}</span>
                                        <span className="text-slate-500"> → </span>
                                        <span className="text-blue-400">{edge.to}</span>
                                    </div>
                                    <div className="text-xs text-slate-400 bg-slate-900/50 px-2 py-1 rounded">
                                        {edge.label}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Single Entrypoint Notice */}
            <div className="bg-green-900/20 border border-green-700 rounded p-4">
                <div className="text-sm text-green-200">
                    <strong>✓ Single Entrypoint Enforced:</strong> All external access routes through tentaculo_link:8000. No direct calls to internal services.
                </div>
            </div>

            {/* Refresh Button */}
            <button
                onClick={loadTopology}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded border border-slate-600 text-sm font-mono"
            >
                ↻ Refresh Topology
            </button>
        </div>
    );
}
