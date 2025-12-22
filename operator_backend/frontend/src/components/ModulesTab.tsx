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
    const [restarting, setRestarting] = useState<string | null>(null);

    useEffect(() => {
        fetchModules();
    }, []);

    const fetchModules = async () => {
        setLoading(true);
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

    const handleRestart = async (name: string) => {
        setRestarting(name);
        const result = await restartModule(name);

        if ("error" in result) {
            const err = result as ErrorResponse;
            setError(`Failed to restart ${name}: ${err.error}`);
        } else {
            // Refresh modules list
            await fetchModules();
        }

        setRestarting(null);
    };

    if (loading) {
        return <div className="text-slate-300">Loading modules...</div>;
    }

    return (
        <div className="space-y-4">
            {error && (
                <div className="p-4 bg-red-900 border-l-4 border-red-500 rounded">
                    <p className="text-red-100">{error}</p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {modules.length === 0 ? (
                    <div className="text-slate-400">No modules available</div>
                ) : (
                    modules.map((module) => (
                        <div key={module.name} className="bg-slate-700 rounded-lg p-6 border border-slate-600">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className="text-lg font-semibold text-white">{module.name}</h3>
                                    <div className="flex items-center gap-2 mt-2">
                                        <span
                                            className={`inline-block w-3 h-3 rounded-full ${module.status === "active" ? "bg-green-500" : "bg-slate-400"
                                                }`}
                                        />
                                        <span className="text-slate-300 text-sm capitalize">{module.status}</span>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => handleRestart(module.name)}
                                disabled={restarting === module.name}
                                className={`w-full py-2 px-4 rounded font-medium transition-colors ${restarting === module.name
                                        ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                                        : "bg-blue-600 hover:bg-blue-700 text-white"
                                    }`}
                            >
                                {restarting === module.name ? "Restarting..." : "Restart"}
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
