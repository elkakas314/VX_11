import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface StatusData {
    policy: string
    mode: string
    active_modules: string[]
    off_by_policy: string[]
    degraded: boolean
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
                apiClient.scorecard?.() || Promise.resolve({ ok: false }),
            ])

            if (statusResp.ok && statusResp.data) {
                setStatus(statusResp.data)
            }

            if (modulesResp.ok && modulesResp.data) {
                const mods = Array.isArray(modulesResp.data.modules)
                    ? modulesResp.data.modules
                    : []
                setModules(mods)
            }

            if (scorecardResp.ok && scorecardResp.data) {
                setScorecard(scorecardResp.data)
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
            <h2>Overview</h2>

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
                        <dd>{status?.mode || '—'}</dd>

                        <dt>Active Modules</dt>
                        <dd>{status?.active_modules?.length || 0}</dd>

                        <dt>Off by Policy</dt>
                        <dd>{status?.off_by_policy?.length || 0}</dd>
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
