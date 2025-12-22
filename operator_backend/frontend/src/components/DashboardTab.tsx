import React, { useEffect, useState } from "react";
import { getStatus } from "../api/canonical";
import { OperatorStatus, ErrorResponse } from "../types/canonical";

export const DashboardTab: React.FC = () => {
    const [status, setStatus] = useState<OperatorStatus | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [isPolicyGated, setIsPolicyGated] = useState(false);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000); // Refresh every 5s
        return () => clearInterval(interval);
    }, []);

    const fetchStatus = async () => {
        const result = await getStatus();

        if ("error" in result) {
            const err = result as ErrorResponse;
            if (err.status === 409) {
                setIsPolicyGated(true);
                setError("⚠️ System is in low_power mode. Limited operations available.");
            } else {
                setError(err.error || `Error: ${err.status}`);
            }
            setStatus(null);
        } else {
            setStatus(result);
            setError(null);
            setIsPolicyGated(false);
        }

        setLoading(false);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-slate-300">Loading system status...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Policy Gating Warning */}
            {isPolicyGated && (
                <div className="p-4 bg-yellow-900 border-l-4 border-yellow-500 rounded">
                    <p className="text-yellow-100 font-semibold">⚠️ Low Power Mode Active</p>
                    <p className="text-yellow-200 text-sm mt-1">
                        System is operating in low_power mode. Some API endpoints are restricted (409).
                    </p>
                </div>
            )}

            {/* Error */}
            {error && !isPolicyGated && (
                <div className="p-4 bg-red-900 border-l-4 border-red-500 rounded">
                    <p className="text-red-100">{error}</p>
                </div>
            )}

            {/* Status Card */}
            {status && (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Overall Status */}
                        <div className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                            <p className="text-slate-300 text-sm font-medium mb-2">System Status</p>
                            <p className="text-2xl font-bold text-white">
                                {status.status === "operational" ? "✓" : "!"} {status.status}
                            </p>
                            <p className="text-slate-400 text-xs mt-2">Uptime: {Math.floor(status.uptime_seconds / 60)}m</p>
                        </div>

                        {/* Operating Mode */}
                        <div className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                            <p className="text-slate-300 text-sm font-medium mb-2">Operating Mode</p>
                            <p className="text-2xl font-bold text-white">{status.mode}</p>
                            <p className="text-slate-400 text-xs mt-2">
                                {status.mode === "operative_core" ? "🟢 Full operations" : "🟡 Limited mode"}
                            </p>
                        </div>

                        {/* Active Modules */}
                        <div className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                            <p className="text-slate-300 text-sm font-medium mb-2">Active Modules</p>
                            <p className="text-2xl font-bold text-white">
                                {Object.values(status.modules).filter((m) => m.status === "active").length}/
                                {Object.keys(status.modules).length}
                            </p>
                            <p className="text-slate-400 text-xs mt-2">Last update: {new Date(status.timestamp).toLocaleTimeString()}</p>
                        </div>
                    </div>

                    {/* Modules List */}
                    <div className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                        <h3 className="text-lg font-semibold text-white mb-4">Modules</h3>
                        <div className="space-y-3">
                            {Object.entries(status.modules).map(([name, module]) => (
                                <div key={name} className="flex items-center justify-between bg-slate-600 p-3 rounded">
                                    <span className="text-white font-medium">{name}</span>
                                    <div className="flex items-center gap-2">
                                        <span
                                            className={`inline-block w-3 h-3 rounded-full ${module.status === "active"
                                                    ? "bg-green-500"
                                                    : module.status === "inactive"
                                                        ? "bg-slate-400"
                                                        : "bg-red-500"
                                                }`}
                                        />
                                        <span className="text-slate-300 text-sm capitalize">{module.status}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};
