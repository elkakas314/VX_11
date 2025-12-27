import React, { useEffect, useState } from "react";
import { getModules, restartModule } from "../api/canonical";
import { ErrorResponse } from "../types/canonical";

interface Module {
    name: string;
    status: string;
}

export const ModulesTab: React.FC = () => {
    const [modules, setModules] = useState<Module[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [acting, setActing] = useState<string | null>(null);
    const [confirmAction, setConfirmAction] = useState<{ module: string; action: string } | null>(null);

    useEffect(() => {
        fetchModules();
        const interval = setInterval(fetchModules, 10000); // Auto-refresh every 10s
        return () => clearInterval(interval);
    }, []);

    const fetchModules = async () => {
        const result = await getModules();

        if ("error" in result) {
            const err = result as ErrorResponse;
            setError(err.error || "Failed to load modules");
        } else {
            setModules(result.modules || []);
            setError(null);
        }

        setLoading(false);
    };

    const handleAction = async (name: string, action: "start" | "stop" | "restart") => {
        setActing(`${name}_${action}`);
        try {
            // Simulate API call (replace with real API when available)
            await new Promise(r => setTimeout(r, 1500));

            // Show success toast
            console.log(`✓ ${action.toUpperCase()} ${name} completed`);

            // Refresh modules
            await fetchModules();
        } catch (err) {
            setError(`Failed to ${action} ${name}`);
        } finally {
            setActing(null);
            setConfirmAction(null);
        }
    };

    if (loading) {
        return <div className="text-slate-300 p-4">Loading modules...</div>;
    }

    const statusColorMap: Record<string, string> = {
        "on": "bg-emerald-900/30 border-emerald-600",
        "off": "bg-slate-800 border-slate-600",
        "active": "bg-emerald-900/30 border-emerald-600",
        "inactive": "bg-slate-800 border-slate-600",
    };

    const statusDotMap: Record<string, string> = {
        "on": "bg-emerald-500",
        "off": "bg-slate-500",
        "active": "bg-emerald-500",
        "inactive": "bg-slate-500",
    };

    return (
        <div className="space-y-4 p-4">
            {error && (
                <div className="p-4 bg-red-900/30 border border-red-600 rounded">
                    <p className="text-red-200">⚠️ {error}</p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {modules.length === 0 ? (
                    <div className="text-slate-400">No modules available</div>
                ) : (
                    modules.map((module) => (
                        <div key={module.name} className={`rounded-lg p-5 border ${statusColorMap[module.status] || statusColorMap.off}`}>
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-3 h-3 rounded-full ${statusDotMap[module.status] || statusDotMap.off}`} />
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">{module.name}</h3>
                                        <p className="text-sm text-slate-400 capitalize">Status: {module.status}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex gap-2 flex-wrap">
                                <button
                                    onClick={() => setConfirmAction({ module: module.name, action: "start" })}
                                    disabled={acting === `${module.name}_start`}
                                    className={`px-3 py-2 rounded text-xs font-medium transition-colors ${acting === `${module.name}_start`
                                            ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                                            : "bg-green-700 hover:bg-green-600 text-white"
                                        }`}
                                >
                                    {acting === `${module.name}_start` ? "Starting..." : "▶ Start"}
                                </button>

                                <button
                                    onClick={() => setConfirmAction({ module: module.name, action: "stop" })}
                                    disabled={acting === `${module.name}_stop`}
                                    className={`px-3 py-2 rounded text-xs font-medium transition-colors ${acting === `${module.name}_stop`
                                            ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                                            : "bg-red-700 hover:bg-red-600 text-white"
                                        }`}
                                >
                                    {acting === `${module.name}_stop` ? "Stopping..." : "⏹ Stop"}
                                </button>

                                <button
                                    onClick={() => setConfirmAction({ module: module.name, action: "restart" })}
                                    disabled={acting === `${module.name}_restart`}
                                    className={`px-3 py-2 rounded text-xs font-medium transition-colors ${acting === `${module.name}_restart`
                                            ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                                            : "bg-yellow-700 hover:bg-yellow-600 text-white"
                                        }`}
                                >
                                    {acting === `${module.name}_restart` ? "Restarting..." : "🔄 Restart"}
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Confirmation Modal */}
            {confirmAction && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 rounded">
                    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-sm">
                        <h2 className="text-lg font-bold text-white mb-4">
                            Confirm {confirmAction.action.toUpperCase()}
                        </h2>
                        <p className="text-slate-300 mb-6">
                            Are you sure you want to {confirmAction.action} <strong>{confirmAction.module}</strong>?
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => handleAction(confirmAction.module, confirmAction.action as "start" | "stop" | "restart")}
                                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium"
                            >
                                Confirm
                            </button>
                            <button
                                onClick={() => setConfirmAction(null)}
                                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded font-medium"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Refresh Button */}
            <button
                onClick={fetchModules}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded border border-slate-600 text-sm font-medium"
            >
                ↻ Refresh Modules
            </button>
        </div>
    );
};
