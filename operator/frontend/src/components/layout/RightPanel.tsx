import { useEffect, useState } from 'react'
import { apiClient } from '../../api/client'

interface ModuleStatus {
    name: string
    status: 'ok' | 'degraded' | 'down'
    latency_ms?: number
}

export function RightPanel() {
    const [modules, setModules] = useState<ModuleStatus[]>([])
    const [logs] = useState<string[]>([])

    useEffect(() => {
        // Fetch module statuses
        const fetchStatus = async () => {
            try {
                const health = await apiClient.getMadreHealth()
                if (health.modules) {
                    setModules(
                        Object.entries(health.modules).map(([name, status]: any) => ({
                            name,
                            status: status.status,
                            latency_ms: status.latency_ms,
                        }))
                    )
                }
            } catch (e) {
                // Fallback
                console.error('Status fetch failed:', e)
            }
        }

        fetchStatus()
        const interval = setInterval(fetchStatus, 5000)
        return () => clearInterval(interval)
    }, [])

    return (
        <aside className="bg-slate-900 rounded-lg border border-purple-900/30 shadow-lg flex flex-col overflow-hidden">
            {/* Module Status */}
            <div className="flex-1 flex flex-col border-b border-purple-900/30">
                <div className="p-3 border-b border-purple-900/20">
                    <h3 className="text-xs font-bold text-purple-400">Module Status</h3>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {modules.map((mod) => (
                        <div
                            key={mod.name}
                            className={`p-2 rounded-lg text-xs ${mod.status === 'ok'
                                ? 'bg-green-900/30 border border-green-500/50'
                                : mod.status === 'degraded'
                                    ? 'bg-amber-900/30 border border-amber-500/50'
                                    : 'bg-red-900/30 border border-red-500/50'
                                }`}
                        >
                            <div className="flex justify-between items-center">
                                <span className="capitalize font-medium">{mod.name}</span>
                                <span className={`w-2 h-2 rounded-full ${mod.status === 'ok' ? 'bg-green-500' :
                                    mod.status === 'degraded' ? 'bg-amber-500' : 'bg-red-500'
                                    } animate-pulse`}></span>
                            </div>
                            {mod.latency_ms !== undefined && (
                                <div className="text-gray-400 text-xs mt-1">{mod.latency_ms}ms</div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Logs/Events */}
            <div className="flex-1 flex flex-col border-t border-purple-900/30">
                <div className="p-3 border-b border-purple-900/20">
                    <h3 className="text-xs font-bold text-purple-400">Recent Events</h3>
                </div>
                <div className="flex-1 overflow-y-auto p-2 font-mono text-xs text-gray-400 space-y-1 bg-slate-950/50">
                    {logs.length === 0 ? (
                        <div className="text-gray-600 text-center py-8">No events</div>
                    ) : (
                        logs.map((log, i) => (
                            <div key={i} className="text-gray-500">
                                {log}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </aside>
    )
}
