import React, { useState, useEffect } from "react";

interface Percentages {
    [key: string]: number | string | any;
}

interface Scorecard {
    [key: string]: number | string | any;
}

export function MetricsTab() {
    const [percentages, setPercentages] = useState<Percentages | null>(null);
    const [scorecard, setScorecard] = useState<Scorecard | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadMetrics();
        const interval = setInterval(loadMetrics, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, []);

    const loadMetrics = async () => {
        try {
            setError(null);

            // Fetch percentages
            const percRes = await fetch("http://localhost:8000/api/percentages");
            if (percRes.ok) {
                const data = await percRes.json();
                setPercentages(data.data || data);
            }

            // Fetch scorecard
            const scoreRes = await fetch("http://localhost:8000/api/scorecard");
            if (scoreRes.ok) {
                const data = await scoreRes.json();
                setScorecard(data.data || data);
            }

            setLoading(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load metrics");
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-slate-400">Loading metrics...</div>
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

    const formatValue = (val: any): string => {
        if (typeof val === "number") {
            if (val > 1000) return (val / 1000).toFixed(1) + "K";
            if (val % 1 !== 0) return val.toFixed(2);
            return val.toString();
        }
        return String(val);
    };

    const getMetricColor = (key: string, value: any): string => {
        // Percentage-like metrics: treat numeric or numeric-string values
        if (key.includes("pct") || key.includes("percent")) {
            const num = typeof value === "number" ? value : Number(String(value).replace("%", ""));
            if (Number.isNaN(num)) return "text-slate-300";
            if (num >= 90) return "text-green-400";
            if (num >= 70) return "text-yellow-400";
            return "text-red-400";
        }

        // Verdict-like metrics: treat as string (case-insensitive)
        if (key.includes("verdict")) {
            const s = String(value || "").toUpperCase();
            if (s.includes("OPERATIVE")) return "text-green-400";
            if (s.includes("DEGRADED")) return "text-yellow-400";
            return "text-red-400";
        }

        // Default fallback
        return "text-slate-300";
    };
    const getProgressBarColor = (value: number): string => {
        if (value >= 90) return "bg-green-600";
        if (value >= 70) return "bg-yellow-600";
        return "bg-red-600";
    };

    const getRowBgColor = (idx: number): string => {
        return idx % 2 === 0 ? "bg-slate-800" : "bg-slate-800/50";
    };
    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-bold mb-2">Metrics & Health</h2>
                <p className="text-slate-400">Comprehensive performance and integrity metrics</p>
            </div>

            {/* Percentages Section */}
            {percentages && (
                <div>
                    <h3 className="text-2xl font-bold mb-3 text-slate-200">Performance Metrics (%)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {Object.entries(percentages)
                            .filter(([k]) => !k.startsWith("_") && !k.startsWith("generated"))
                            .map(([key, value]) => (
                                <div key={key} className="bg-slate-800 rounded border border-slate-700 p-4">
                                    <div className="text-xs text-slate-500 uppercase mb-2">
                                        {key.replace(/_/g, " ").replace(/pct/gi, "")}
                                    </div>
                                    <div className={`text-2xl font-bold ${getMetricColor(key, value)}`}>
                                        {formatValue(value)}
                                    </div>
                                    {typeof value === "number" && key.includes("pct") && (
                                        <div className="mt-2 bg-slate-900 rounded h-1 w-full overflow-hidden">
                                            {/* webhint-disable no-inline-styles */}
                                            <div
                                                className={`h-full transition-all ${getProgressBarColor(value)}`}
                                                // eslint-disable-next-line react/style-prop-object
                                                style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
                                            />
                                        </div>
                                    )}
                                </div>
                            ))}
                    </div>
                </div>
            )}

            {/* Scorecard Section */}
            {scorecard && (
                <div>
                    <h3 className="text-2xl font-bold mb-3 text-slate-200">Database Scorecard</h3>
                    <div className="bg-slate-800 rounded border border-slate-700 overflow-hidden">
                        <table className="w-full text-sm">
                            <tbody>
                                {Object.entries(scorecard)
                                    .filter(([k]) => !k.startsWith("_") && !k.startsWith("generated"))
                                    .map(([key, value], idx) => (
                                        <tr
                                            key={key}
                                            className={`border-b border-slate-700 last:border-b-0 ${getRowBgColor(idx)}`}
                                        >
                                            <td className="px-4 py-3 text-slate-400 font-mono">
                                                {key.replace(/_/g, " ")}
                                            </td>
                                            <td className={`px-4 py-3 text-right font-mono font-bold ${getMetricColor(key, value)}`}>
                                                {typeof value === "number" && key.includes("bytes")
                                                    ? (value / 1e9).toFixed(2) + " GB"
                                                    : formatValue(value)}
                                            </td>
                                        </tr>
                                    ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Legend */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                <div className="flex items-center gap-2 text-green-400">
                    <div className="w-2 h-2 bg-green-400 rounded-full" />
                    <span>Excellent (&gt;90%)</span>
                </div>
                <div className="flex items-center gap-2 text-yellow-400">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full" />
                    <span>Good (70-90%)</span>
                </div>
                <div className="flex items-center gap-2 text-red-400">
                    <div className="w-2 h-2 bg-red-400 rounded-full" />
                    <span>Needs Attention (&lt;70%)</span>
                </div>
            </div>

            {/* Refresh Button */}
            <button
                onClick={loadMetrics}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded border border-slate-600 text-sm font-mono"
            >
                ↻ Refresh Metrics
            </button>
        </div>
    );
}
