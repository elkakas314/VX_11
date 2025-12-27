import { OPERATOR_BASE_URL } from "../config";
import React, { useState, useEffect } from "react";

interface HealthStatus {
    status: string;
    module?: string;
    version?: string;
    uptime?: number;
    mode?: string;
}

interface Percentages {
    autonomy_verdict?: string;
    Estabilidad_operativa_pct?: number;
    tests_p0_pct?: number;
    contract_coherence_pct?: number;
    [key: string]: any;
}

interface Scorecard {
    integrity?: string;
    total_tables?: number;
    total_rows?: number;
    db_size_bytes?: number;
    [key: string]: any;
}

export function OverviewTab() {
    const [status, setStatus] = useState<HealthStatus | null>(null);
    const [percentages, setPercentages] = useState<Percentages | null>(null);
    const [scorecard, setScorecard] = useState<Scorecard | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadOverviewData();
        const interval = setInterval(loadOverviewData, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, []);

    const loadOverviewData = async () => {
        try {
            setError(null);

            // Fetch status
            const statusRes = await fetch(`${OPERATOR_BASE_URL}/api/status`);
            if (statusRes.ok) {
                setStatus(await statusRes.json());
            }

            // Fetch percentages
            const percRes = await fetch(`${OPERATOR_BASE_URL}/api/percentages`);
            if (percRes.ok) {
                const data = await percRes.json();
                setPercentages(data.data || data);
            }

            // Fetch scorecard
            const scoreRes = await fetch(`${OPERATOR_BASE_URL}/api/scorecard`);
            if (scoreRes.ok) {
                const data = await scoreRes.json();
                setScorecard(data.data || data);
            }

            setLoading(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load overview");
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-slate-400">Loading overview...</div>
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

    const autonomyVerdictColor = percentages?.autonomy_verdict === "OPERATIVE" ? "text-green-400" : "text-yellow-400";

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-bold mb-2">VX11 System Overview</h2>
                <p className="text-slate-400">Real-time status and metrics snapshot</p>
            </div>

            {/* Core Health Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Status Card */}
                <div className="bg-slate-800 rounded border border-slate-700 p-4">
                    <div className="text-sm text-slate-400 mb-2">Module Status</div>
                    <div className="text-2xl font-bold text-green-400">
                        {status?.status === "operational" ? "✓ Operational" : "⚠ Checking"}
                    </div>
                    <div className="text-xs text-slate-500 mt-2">
                        {status?.module} v{status?.version}
                    </div>
                </div>

                {/* Autonomy Verdict */}
                <div className="bg-slate-800 rounded border border-slate-700 p-4">
                    <div className="text-sm text-slate-400 mb-2">Autonomy Verdict</div>
                    <div className={`text-2xl font-bold ${autonomyVerdictColor}`}>
                        {percentages?.autonomy_verdict || "—"}
                    </div>
                    <div className="text-xs text-slate-500 mt-2">System autonomy level</div>
                </div>

                {/* SOLO_MADRE Policy */}
                <div className="bg-slate-800 rounded border border-slate-700 p-4">
                    <div className="text-sm text-slate-400 mb-2">Runtime Policy</div>
                    <div className="text-2xl font-bold text-blue-400">SOLO_MADRE</div>
                    <div className="text-xs text-slate-500 mt-2">Default safe mode</div>
                </div>
            </div>

            {/* Metrics Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Stability */}
                <div className="bg-slate-800 rounded border border-slate-700 p-4">
                    <div className="text-sm text-slate-400 mb-3">Stability Metrics</div>
                    <div className="space-y-2">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Operational Stability</span>
                            <span className="font-mono bg-green-900/30 text-green-200 px-2 py-1 rounded text-sm">
                                {percentages?.Estabilidad_operativa_pct?.toFixed(1) || "—"}%
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">P0 Tests</span>
                            <span className="font-mono bg-green-900/30 text-green-200 px-2 py-1 rounded text-sm">
                                {percentages?.tests_p0_pct?.toFixed(1) || "—"}%
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Contract Coherence</span>
                            <span className="font-mono bg-green-900/30 text-green-200 px-2 py-1 rounded text-sm">
                                {percentages?.contract_coherence_pct?.toFixed(1) || "—"}%
                            </span>
                        </div>
                    </div>
                </div>

                {/* Database Health */}
                <div className="bg-slate-800 rounded border border-slate-700 p-4">
                    <div className="text-sm text-slate-400 mb-3">Database Health</div>
                    <div className="space-y-2">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Integrity</span>
                            <span className="font-mono bg-blue-900/30 text-blue-200 px-2 py-1 rounded text-sm">
                                {scorecard?.integrity === "5000" || scorecard?.integrity === "ok" ? "✓ OK" : "⚠ Check"}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Tables</span>
                            <span className="font-mono text-slate-300">{scorecard?.total_tables || "—"}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Rows</span>
                            <span className="font-mono text-slate-300">
                                {scorecard?.total_rows ? (scorecard.total_rows / 1e6).toFixed(1) + "M" : "—"}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Size</span>
                            <span className="font-mono text-slate-300">
                                {scorecard?.db_size_bytes ? (scorecard.db_size_bytes / 1e9).toFixed(2) + "GB" : "—"}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
                <button
                    onClick={loadOverviewData}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded border border-slate-600 text-sm font-mono"
                >
                    ↻ Refresh
                </button>
                <button
                    onClick={() => {
                        const link = document.createElement("a");
                        link.href = `${OPERATOR_BASE_URL}/api/audit/runs`;
                        link.target = "_blank";
                        link.click();
                    }}
                    className="px-4 py-2 bg-blue-900/30 hover:bg-blue-900/50 rounded border border-blue-700 text-blue-200 text-sm font-mono"
                >
                    View Recent Audits →
                </button>
            </div>
        </div>
    );
}
