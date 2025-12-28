import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface StatusData {
    status?: string
    components?: Record<string, boolean>
    circuit_breaker?: {
        state: string
        failure_count: number
        last_failure?: string
    }
    degraded?: boolean
    errors?: string[]
}

export function StatusCard() {
    const [status, setStatus] = useState<StatusData | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

    const fetchStatus = async () => {
        setLoading(true)
        const resp = await apiClient.status()
        if (resp.ok) {
            setStatus(resp.data as StatusData)
            setError(null)
        } else {
            setError(resp.error || 'Failed to fetch status')
        }
        setLastRefresh(new Date())
        setLoading(false)
    }

    useEffect(() => {
        fetchStatus()
        // Poll every 30s (low-power default)
        const interval = setInterval(fetchStatus, 30000)
        return () => clearInterval(interval)
    }, [])

    const statusColor =
        status?.degraded || status?.circuit_breaker?.state === 'open'
            ? 'var(--accent-red)'
            : 'var(--accent-green)'

    return (
        <div className="card">
            <div className="card-header">
                <h2>Estado Global</h2>
                <button onClick={fetchStatus} disabled={loading} className="btn-small">
                    {loading ? '⟳' : '↻'}
                </button>
            </div>

            {error && (
                <div className="error-box">
                    <span>⚠</span> {error}
                </div>
            )}

            {status && (
                <>
                    <div className="status-row">
                        <span>Status:</span>
                        <span className="status-value">
                            {status.status || 'ok'} {status.degraded ? '(degraded)' : ''}
                        </span>
                    </div>

                    {status.circuit_breaker && (
                        <div className="status-row">
                            <span>Circuit Breaker:</span>
                            <span className="circuit-breaker-state">
                                {status.circuit_breaker.state} ({status.circuit_breaker.failure_count} failures)
                            </span>
                        </div>
                    )}

                    {status.components && (
                        <div className="components-grid">
                            {Object.entries(status.components).map(([name, up]) => (
                                <div key={name} className="component-badge">
                                    <span className={up ? 'status-up' : 'status-down'}>
                                        ●
                                    </span>
                                    {name}
                                </div>
                            ))}
                        </div>
                    )}

                    {status.errors && status.errors.length > 0 && (
                        <div className="errors-list">
                            {status.errors.map((err, i) => (
                                <div key={i} className="error-item">
                                    {err}
                                </div>
                            ))}
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
