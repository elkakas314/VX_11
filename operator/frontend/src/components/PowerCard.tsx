import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface PowerState {
    mode?: string
    window_id?: string | null
    ttl_seconds?: number | null
    services?: string[]
    degraded?: boolean
    reason?: string | null
}

export function PowerCard() {
    const [power, setPower] = useState<PowerState | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

    const fetchPower = async () => {
        setLoading(true)
        const resp = await apiClient.windows()
        if (resp.ok) {
            setPower(resp.data as PowerState)
            setError(null)
        } else {
            setError(resp.error || 'Failed to fetch power state')
        }
        setLastRefresh(new Date())
        setLoading(false)
    }

    useEffect(() => {
        fetchPower()
    }, [])

    return (
        <div className="card">
            <div className="card-header">
                <h2>Power Window</h2>
                <button onClick={fetchPower} disabled={loading} className="btn-small">
                    {loading ? '⟳' : '↻'}
                </button>
            </div>

            {error && (
                <div className="error-box">
                    <span>⚠</span> {error}
                </div>
            )}

            {power && (
                <>
                    <div className="status-row">
                        <span>Policy:</span>
                        <span className="policy-value">{power.mode || 'unknown'}</span>
                    </div>

                    {power.window_id && (
                        <div className="status-row">
                            <span>Window ID:</span>
                            <code className="window-id">{power.window_id}</code>
                        </div>
                    )}

                    {power.ttl_seconds !== undefined && power.ttl_seconds !== null && (
                        <div className="status-row">
                            <span>TTL Remaining:</span>
                            <span>{Math.floor(power.ttl_seconds)}s</span>
                        </div>
                    )}

                    {power.services && (
                        <div className="services-list">
                            <strong>Running Services:</strong>
                            {power.services.length > 0 ? (
                                <ul>
                                    {power.services.map((svc) => (
                                        <li key={svc}>
                                            <span className="service-indicator">●</span> {svc}
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <em className="text-secondary">None</em>
                            )}
                        </div>
                    )}

                    {power.mode === 'solo_madre' && (
                        <div className="warning-box">
                            <span>🔒</span> SOLO_MADRE policy active (Madre only)
                        </div>
                    )}

                    <div className="card-footer">
                        <small>Last refresh: {lastRefresh.toLocaleTimeString()}</small>
                    </div>
                </>
            )}
        </div>
    )
}
