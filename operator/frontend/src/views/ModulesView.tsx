import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface ModuleStatus {
    name: string
    status: string
    reason?: string
    category?: string
}

export function ModulesView() {
    const [modules, setModules] = useState<ModuleStatus[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadModules()
    }, [])

    async function loadModules() {
        setLoading(true)
        setError(null)
        try {
            const resp = await apiClient.status()
            if (resp.ok && resp.data) {
                const coreServices = resp.data.core_services || {}
                const mapped: ModuleStatus[] = Object.entries(coreServices).map(
                    ([name, info]: [string, any]) => ({
                        name,
                        status: info.status || info.state || 'unknown',
                        reason: info.reason,
                        category: 'core',
                    })
                )

                const windowServices = new Set(resp.data.window?.services || [])
                const optional = ['switch', 'hermes', 'hormiguero', 'manifestator', 'spawner']
                optional.forEach((name) => {
                    mapped.push({
                        name,
                        status: windowServices.has(name) ? 'UP' : 'OFF_BY_POLICY',
                        reason: windowServices.has(name) ? 'window_active' : 'solo_madre',
                        category: 'optional',
                    })
                })

                setModules(mapped)
            } else {
                setError(resp.error || 'Unable to load module status')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load modules')
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return <div className="view-loading">⟳ Loading modules...</div>
    }

    return (
        <div className="modules-view">
            <div className="view-header">
                <h2>Modules</h2>
                <button onClick={loadModules} className="btn-secondary">
                    ⟳ Refresh
                </button>
            </div>

            {error && <div className="error-banner">{error}</div>}

            <div className="module-grid">
                {modules.length > 0 ? (
                    modules.map((mod) => (
                        <div key={mod.name} className="module-card">
                            <div className="module-card-header">
                                <span className="module-name">{mod.name}</span>
                                <span className={`module-status status-${mod.status.toLowerCase()}`}>
                                    {mod.status}
                                </span>
                            </div>
                            {mod.reason && <div className="module-reason">{mod.reason}</div>}
                            {mod.category && <div className="module-category">{mod.category}</div>}
                        </div>
                    ))
                ) : (
                    <p className="empty">No module data available</p>
                )}
            </div>
        </div>
    )
}
