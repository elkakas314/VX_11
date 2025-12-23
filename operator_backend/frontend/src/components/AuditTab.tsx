import React, { useEffect, useState } from "react";
import { listAuditLogs, getAuditDetail, downloadAuditCSV } from "../api/canonical";
import { AuditLog, ErrorResponse } from "../types/canonical";

export const AuditTab: React.FC = () => {
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [levelFilter, setLevelFilter] = useState<string>("");
    const [skip, setSkip] = useState(0);
    const [total, setTotal] = useState(0);
    const [downloading, setDownloading] = useState(false);

    const PAGE_SIZE = 20;

    useEffect(() => {
        fetchLogs();
    }, [skip, levelFilter]);

    const fetchLogs = async () => {
        setLoading(true);
        const result = await listAuditLogs(skip, PAGE_SIZE, undefined, levelFilter || undefined);

        if ("error" in result) {
            const err = result as ErrorResponse;
            setError(err.error || "Failed to load audit logs");
            setLogs([]);
        } else {
            setLogs(result.logs || []);
            setTotal(result.total || 0);
            setError(null);
        }

        setLoading(false);
    };

    const handleLogClick = async (log: AuditLog) => {
        const result = await getAuditDetail(log.id);

        if ("error" in result) {
            setError(`Failed to load log detail: ${(result as ErrorResponse).error}`);
        } else {
            setSelectedLog(result);
        }
    };

    const handleDownload = async (logId: string) => {
        setDownloading(true);
        const result = await downloadAuditCSV(logId);

        if ("error" in result) {
            setError(`Download failed: ${(result as ErrorResponse).error}`);
        } else {
            const blob = result as Blob;
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `audit-${logId}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }

        setDownloading(false);
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Logs List */}
            <div className="lg:col-span-1">
                <div className="mb-4 space-y-3">
                    <h3 className="text-lg font-semibold text-white">Audit Logs</h3>

                    {/* Level Filter */}
                    <select
                        aria-label="Filter audit logs by level"
                        value={levelFilter}
                        onChange={(e) => {
                            setLevelFilter(e.target.value);
                            setSkip(0);
                        }}
                        className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Levels</option>
                        <option value="INFO">INFO</option>
                        <option value="WARNING">WARNING</option>
                        <option value="ERROR">ERROR</option>
                    </select>
                </div>

                {error && (
                    <div className="p-4 bg-red-900 border-l-4 border-red-500 rounded mb-4">
                        <p className="text-red-100 text-sm">{error}</p>
                    </div>
                )}

                {loading ? (
                    <div className="text-slate-400">Loading...</div>
                ) : (
                    <>
                        <div className="space-y-2 mb-4 max-h-[500px] overflow-y-auto">
                            {logs.length === 0 ? (
                                <p className="text-slate-400">No logs available</p>
                            ) : (
                                logs.map((log) => (
                                    <button
                                        key={log.id}
                                        onClick={() => handleLogClick(log)}
                                        className={`w-full text-left p-3 rounded border transition-colors ${selectedLog?.id === log.id
                                                ? "bg-blue-600 border-blue-500 text-white"
                                                : "bg-slate-700 border-slate-600 text-slate-100 hover:bg-slate-600"
                                            }`}
                                    >
                                        <p className="font-medium text-sm truncate">{log.message}</p>
                                        <div className="flex items-center justify-between mt-1">
                                            <span
                                                className={`text-xs px-2 py-0.5 rounded ${log.level === "ERROR"
                                                        ? "bg-red-900 text-red-200"
                                                        : log.level === "WARNING"
                                                            ? "bg-yellow-900 text-yellow-200"
                                                            : "bg-blue-900 text-blue-200"
                                                    }`}
                                            >
                                                {log.level}
                                            </span>
                                            <span className="text-xs text-slate-400">
                                                {new Date(log.timestamp).toLocaleTimeString()}
                                            </span>
                                        </div>
                                    </button>
                                ))
                            )}
                        </div>

                        {/* Pagination */}
                        {total > PAGE_SIZE && (
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setSkip(Math.max(0, skip - PAGE_SIZE))}
                                    disabled={skip === 0}
                                    className="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white rounded text-sm font-medium"
                                >
                                    ← Prev
                                </button>
                                <button
                                    onClick={() => setSkip(skip + PAGE_SIZE)}
                                    disabled={skip + PAGE_SIZE >= total}
                                    className="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 text-white rounded text-sm font-medium"
                                >
                                    Next →
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Log Detail */}
            <div className="lg:col-span-2">
                {selectedLog ? (
                    <div className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                        <div className="flex items-start justify-between mb-4">
                            <h4 className="text-lg font-semibold text-white">Log Detail</h4>
                            <button
                                onClick={() => handleDownload(selectedLog.id)}
                                disabled={downloading}
                                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded text-sm font-medium transition-colors"
                            >
                                {downloading ? "⬇ Downloading..." : "⬇ Export CSV"}
                            </button>
                        </div>

                        <div className="space-y-3">
                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">ID</p>
                                <p className="text-white font-mono text-sm">{selectedLog.id}</p>
                            </div>

                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">Level</p>
                                <span
                                    className={`text-xs px-2 py-0.5 rounded inline-block ${selectedLog.level === "ERROR"
                                            ? "bg-red-900 text-red-200"
                                            : selectedLog.level === "WARNING"
                                                ? "bg-yellow-900 text-yellow-200"
                                                : "bg-blue-900 text-blue-200"
                                        }`}
                                >
                                    {selectedLog.level}
                                </span>
                            </div>

                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">Source</p>
                                <p className="text-white">{selectedLog.source}</p>
                            </div>

                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">Message</p>
                                <p className="text-slate-100">{selectedLog.message}</p>
                            </div>

                            <div>
                                <p className="text-slate-300 text-xs font-medium mb-1">Timestamp</p>
                                <p className="text-slate-400 text-sm">{new Date(selectedLog.timestamp).toLocaleString()}</p>
                            </div>

                            {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
                                <div>
                                    <p className="text-slate-300 text-xs font-medium mb-2">Metadata</p>
                                    <pre className="bg-slate-900 rounded p-3 text-xs text-slate-200 overflow-x-auto">
                                        {JSON.stringify(selectedLog.metadata, null, 2)}
                                    </pre>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="bg-slate-700 rounded-lg p-6 border border-slate-600 text-slate-400 text-center py-12">
                        Select a log to view details
                    </div>
                )}
            </div>
        </div>
    );
};
