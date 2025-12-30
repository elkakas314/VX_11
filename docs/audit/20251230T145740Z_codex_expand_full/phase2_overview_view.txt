import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface StatusData {
    policy: string
    degraded: boolean
    window?: {
        mode?: string
        services?: string[]
    }
}

interface ModuleData {
    name: string
    status: string
    version?: string
    health?: string
}

interface ScoreData {
    order_fs_pct: number
    coherencia_routing_pct: number
    automatizacion_pct: number
    autonomia_pct: number
    global_ponderado_pct: number
}

export function OverviewView() {
    const [status, setStatus] = useState<StatusData | null>(null)
    const [modules, setModules] = useState<ModuleData[]>([])
    const [scorecard, setScorecard] = useState<ScoreData | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadData()
    }, [])

    async function loadData() {
        setLoading(true)
        setError(null)

        try {
            const [statusResp, modulesResp, scorecardResp] = await Promise.all([
                apiClient.status(),
                apiClient.modules(),
                apiClient.scorecard(),
            ])

            if (statusResp.ok && statusResp.data) {
                setStatus(statusResp.data)
            }

            if (modulesResp.ok && modulesResp.data?.modules) {
                const moduleData = modulesResp.data.modules as Record<
                    string,
                    { status?: string }
                >
                const mods = Object.entries(moduleData).map(([name, info]) => ({
                    name,
                    status: info?.status || 'unknown',
                }))
                setModules(mods)
            }

            if (scorecardResp.ok && scorecardResp.data) {
                const metrics = scorecardResp.data.percentages?.metrics
                if (metrics) {
                    setScorecard({
                        order_fs_pct: metrics.Orden_fs_pct ?? 0,
                        coherencia_routing_pct: metrics.Coherencia_routing_pct ?? 0,
                        automatizacion_pct: metrics.Automatizacion_pct ?? 0,
                        autonomia_pct: metrics.Autonomia_pct ?? 0,
                        global_ponderado_pct: metrics.Global_ponderado_pct ?? 0,
                    })
                }
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load overview')
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return <div className="view-loading">⟳ Loading overview...</div>
    }

    return (
        <div className="overview-view">
            <h2>Ant View</h2>

            {error && <div className="error-banner">⚠️ {error}</div>}

            {status?.degraded && (
                <div className="degraded-banner">
                    ⚠️ Degraded Mode: Some services are unavailable (solo_madre policy active)
                </div>
            )}

            <div className="widget-grid">
                {/* Status Widget */}
                <div className="widget card">
                    <h3>System Status</h3>
                    <dl className="status-list">
                        <dt>Policy</dt>
                        <dd>{status?.policy || '—'}</dd>

                        <dt>Mode</dt>
                        <dd>{status?.window?.mode || '—'}</dd>

                        <dt>Active Modules</dt>
                        <dd>{modules.filter((m) => m.status === 'UP' || m.status === 'healthy').length}</dd>
                    </dl>
                </div>

                {/* Modules Widget */}
                <div className="widget card">
                    <h3>Active Modules</h3>
                    <div className="module-list">
                        {modules.length > 0 ? (
                            modules.map((m) => (
                                <div key={m.name} className="module-item">
                                    <span className="module-name">{m.name}</span>
                                    <span
                                        className={`module-status status-${m.status?.toLowerCase() || 'unknown'}`}
                                    >
                                        {m.status || '?'}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <p className="empty">No modules available</p>
                        )}
                    </div>
                </div>

                {/* Scorecard Widget */}
                {scorecard && (
                    <div className="widget card">
                        <h3>Performance Metrics</h3>
                        <dl className="scorecard-list">
                            <dt>Order (fs)</dt>
                            <dd>{scorecard.order_fs_pct.toFixed(1)}%</dd>

                            <dt>Routing Coherence</dt>
                            <dd>{scorecard.coherencia_routing_pct.toFixed(1)}%</dd>

                            <dt>Automation</dt>
                            <dd>{scorecard.automatizacion_pct.toFixed(1)}%</dd>

                            <dt>Autonomy</dt>
                            <dd>{scorecard.autonomia_pct.toFixed(1)}%</dd>

                            <dt className="global">Global Score</dt>
                            <dd className="global">
                                <strong>{scorecard.global_ponderado_pct.toFixed(1)}%</strong>
                            </dd>
                        </dl>
                    </div>
                )}

                {/* Recent Audits Widget */}
                <div className="widget card">
                    <h3>Recent Activity</h3>
                    <p className="empty">No recent audits yet</p>
                </div>
            </div>

            <div className="view-actions">
                <button onClick={loadData} className="btn-secondary">
                    ⟳ Refresh
                </button>
            </div>
        </div>
    )
}
