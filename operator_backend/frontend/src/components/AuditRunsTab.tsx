import { OPERATOR_BASE_URL } from "../config";
import React, { useState, useEffect } from "react";

interface AuditRun {
    run_id: string;
    timestamp: string;
    reason: string;
    status: string;
    path?: string;
}

export function AuditRunsTab() {
    const [runs, setRuns] = useState<AuditRun[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedRun, setSelectedRun] = useState<string | null>(null);
    const [runDetail, setRunDetail] = useState<any>(null);
    const [detailLoading, setDetailLoading] = useState(false);

    useEffect(() => {
        loadAuditRuns();
        const interval = setInterval(loadAuditRuns, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const loadAuditRuns = async () => {
        try {
            setError(null);
            const res = await fetch(`${OPERATOR_BASE_URL}/api/audit/runs?limit=20&offset=0`);
            if (res.ok) {
                const data = await res.json();
                setRuns(data.data || []);
            } else {
                throw new Error(`HTTP ${res.status}`);
            }
            setLoading(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load audit runs");
            setLoading(false);
        }
    };

    const loadRunDetail = async (runId: string) => {
        try {
            setDetailLoading(true);
            setError(null);
            const res = await fetch(`${OPERATOR_BASE_URL}/api/audit/runs/${runId}`);
            if (res.ok) {
                const data = await res.json();
                setRunDetail(data.data || null);
                setSelectedRun(runId);
            } else {
                throw new Error(`HTTP ${res.status}`);
            }
            setDetailLoading(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load run detail");
            setDetailLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-slate-400">Loading audit runs...</div>
            </div>
        );
    }

    if (error && !runs.length) {
        return (
            <div className="bg-red-900/30 border border-red-700 rounded p-4 m-4">
                <div className="text-red-200">Error: {error}</div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-bold mb-2">Audit Center</h2>
                <p className="text-slate-400">Recent system audits and operational reports</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Runs List */}
                <div className="lg:col-span-1">
                    <h3 className="text-lg font-bold mb-3 text-slate-200">Recent Runs</h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {runs.length === 0 ? (
                            <div className="text-slate-400 text-sm">No audit runs found</div>
                        ) : (
                            runs.map((run) => (
                                <button
                                    key={run.run_id}
                                    onClick={() => loadRunDetail(run.run_id)}
                                    className={`w-full text-left px-3 py-2 rounded border transition-all ${selectedRun === run.run_id
                                            ? "bg-blue-900 border-blue-700"
                                            : "bg-slate-800 border-slate-700 hover:bg-slate-700"
                                        }`}
                                >
                                    <div className="font-mono text-xs text-slate-400">{run.run_id}</div>
                                    <div className="text-xs text-slate-300 mt-1">{run.reason}</div>
                                    <div className="text-xs text-slate-500 mt-1">
                                        {new Date(parseInt(run.timestamp) * 1000).toLocaleString()}
                                    </div>
                                </button>
                            ))
                        )}
                    </div>
                    <button
                        onClick={loadAuditRuns}
                        className="w-full mt-3 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded border border-slate-600 text-sm font-mono"
                    >
                        ↻ Refresh
                    </button>
                </div>

                {/* Run Detail */}
                <div className="lg:col-span-2">
                    {selectedRun ? (
                        <div>
                            <h3 className="text-lg font-bold mb-3 text-slate-200">
                                Run Details: <span className="text-blue-400 font-mono text-sm">{selectedRun}</span>
                            </h3>

                            {detailLoading ? (
                                <div className="text-slate-400">Loading details...</div>
                            ) : runDetail ? (
                                <div className="space-y-4">
                                    {/* Files Available */}
                                    {runDetail.files && (
                                        <div>
                                            <h4 className="text-sm font-bold text-slate-300 mb-2">Available Files</h4>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                {runDetail.files.map((fname: string) => (
                                                    <a
                                                        key={fname}
                                                        href={`/audit/${selectedRun}/${fname}`}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-blue-400 hover:text-blue-300 text-sm px-2 py-1 bg-slate-800 rounded border border-slate-700 truncate"
                                                    >
                                                        {fname} →
                                                    </a>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* File Previews */}
                                    {runDetail.file_previews && Object.keys(runDetail.file_previews).length > 0 && (
                                        <div>
                                            <h4 className="text-sm font-bold text-slate-300 mb-2">File Previews</h4>
                                            <div className="space-y-2 max-h-48 overflow-y-auto">
                                                {Object.entries(runDetail.file_previews).map(([fname, content]: [string, any]) => (
                                                    <div key={fname} className="bg-slate-900 rounded border border-slate-700 p-3">
                                                        <div className="text-xs font-mono text-slate-400 mb-1">{fname}</div>
                                                        <pre className="text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap break-words">
                                                            {String(content)}
                                                        </pre>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-slate-400">No details available</div>
                            )}
                        </div>
                    ) : (
                        <div className="bg-slate-800 rounded border border-slate-700 p-6 text-center">
                            <div className="text-slate-400">Select a run to view details</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
