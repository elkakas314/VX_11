import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface PowerState {
    status?: string
    power_window?: {
        policy: string
        window_id: string
        ttl_remaining?: number
        running_services?: string[]
    }
    circuit_breaker_active?: boolean
    solo_madre_policy?: boolean
}

export function PowerCard() {
    const [power, setPower] = useState<PowerState | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

    const fetchPower = async () => {
        setLoading(true)
        const resp = await apiClient.powerState()
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
        // Poll every 30s
        const interval = setInterval(fetchPower, 30000)
        return () => clearInterval(interval)
    }, [])

    const policyColor =
        power?.power_window?.policy === 'solo_madre' ? 'var(--accent-red)' : 'var(--accent-blue)'

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
                    {power.power_window && (
                        <>
                            <div className="status-row">
                                <span>Policy:</span>
                                <span className="policy-value">
                                    {power.power_window.policy}
                                </span>
                            </div>

                            <div className="status-row">
                                <span>Window ID:</span>
                                <code className="window-id">{power.power_window.window_id}</code>
                            </div>

                            {power.power_window.ttl_remaining !== undefined && (
                                <div className="status-row">
                                    <span>TTL Remaining:</span>
                                    <span>{power.power_window.ttl_remaining}s</span>
                                </div>
                            )}

                            {power.power_window.running_services && (
                                <div className="services-list">
                                    <strong>Running Services:</strong>
                                    {power.power_window.running_services.length > 0 ? (
                                        <ul>
                                            {power.power_window.running_services.map((svc) => (
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
                        </>
                    )}

                    {power.solo_madre_policy && (
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
