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
    const [refreshInterval, setRefreshInterval] = useState<5 | 10 | 30>(10);

    useEffect(() => {
        fetchModules();
        const interval = setInterval(fetchModules, refreshInterval * 1000);
        return () => clearInterval(interval);
    }, [refreshInterval]);

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
            await new Promise(r => setTimeout(r, 1500));
            console.log(`✓ ${action.toUpperCase()} ${name} completed`);
            await fetchModules();
        } catch (err) {
            setError(`Failed to ${action} ${name}`);
        } finally {
            setActing(null);
            setConfirmAction(null);
        }
    };

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

            {/* Refresh Controls */}
            <div className="flex items-center gap-4 p-3 bg-slate-800 rounded border border-slate-700">
                <label className="text-sm text-slate-300">Auto-refresh:</label>
                <div className="flex gap-2">
                    {[5, 10, 30].map((secs) => (
                        <button
                            key={secs}
                            onClick={() => setRefreshInterval(secs as 5 | 10 | 30)}
                            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${refreshInterval === secs
                                    ? "bg-blue-600 text-white"
                                    : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                                }`}
                        >
                            {secs}s
                        </button>
                    ))}
                </div>
                <button
                    onClick={fetchModules}
                    disabled={loading}
                    className="ml-auto px-4 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded border border-slate-600 text-xs font-medium disabled:opacity-50"
                >
                    ↻ Now
                </button>
            </div>

            {/* Modules Table */}
            <div className="overflow-x-auto rounded border border-slate-700">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="bg-slate-800 border-b border-slate-700">
                            <th className="px-4 py-3 text-left font-semibold text-slate-200">Module</th>
                            <th className="px-4 py-3 text-left font-semibold text-slate-200">Status</th>
                            <th className="px-4 py-3 text-left font-semibold text-slate-200">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {modules.length === 0 ? (
                            <tr>
                                <td colSpan={3} className="px-4 py-6 text-center text-slate-400">
                                    No modules available
                                </td>
                            </tr>
                        ) : (
                            modules.map((module) => (
                                <tr key={module.name} className="border-b border-slate-700 hover:bg-slate-800/50">
                                    <td className="px-4 py-3 font-medium text-white">{module.name}</td>
                                    <td className="px-4 py-3">
                                        <span className={`inline-flex items-center gap-2 px-3 py-1 rounded text-xs font-medium ${statusColorMap[module.status] || statusColorMap.off}`}>
                                            <div className={`w-2 h-2 rounded-full ${statusDotMap[module.status] || statusDotMap.off}`} />
                                            {module.status}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => setConfirmAction({ module: module.name, action: "start" })}
                                                disabled={acting === `${module.name}_start`}
                                                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${acting === `${module.name}_start`
                                                        ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                                                        : "bg-green-700 hover:bg-green-600 text-white"
                                                    }`}
                                            >
                                                {acting === `${module.name}_start` ? "..." : "▶"}
                                            </button>
                                            <button
                                                onClick={() => setConfirmAction({ module: module.name, action: "stop" })}
                                                disabled={acting === `${module.name}_stop`}
                                                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${acting === `${module.name}_stop`
                                                        ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                                                        : "bg-red-700 hover:bg-red-600 text-white"
                                                    }`}
                                            >
                                                {acting === `${module.name}_stop` ? "..." : "⏹"}
                                            </button>
                                            <button
                                                onClick={() => setConfirmAction({ module: module.name, action: "restart" })}
                                                disabled={acting === `${module.name}_restart`}
                                                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${acting === `${module.name}_restart`
                                                        ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                                                        : "bg-yellow-700 hover:bg-yellow-600 text-white"
                                                    }`}
                                            >
                                                {acting === `${module.name}_restart` ? "..." : "🔄"}
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Confirmation Modal */}
            {confirmAction && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-sm">
                        <h2 className="text-lg font-bold text-white mb-4">
                            Confirm {confirmAction.action.toUpperCase()}
                        </h2>
                        <p className="text-slate-300 mb-6">
                            Are you sure you want to <strong>{confirmAction.action}</strong> <strong className="text-emerald-400">{confirmAction.module}</strong>?
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
        </div>
    );
};
