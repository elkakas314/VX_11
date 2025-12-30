import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface HormigueroStatus {
    status?: string
    actions_enabled?: boolean
    last_scan?: string
}

export function HormigueroPanel() {
    const [hormiguero, setHormiguero] = useState<HormigueroStatus | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
    const [debugMode, setDebugMode] = useState(false)

    const fetchHormiguero = async () => {
        setLoading(true)
        const resp = await apiClient.hormigueroStatus()
        if (resp.ok) {
            setHormiguero(resp.data as HormigueroStatus)
            setError(null)
        } else {
            setError(resp.error || 'Endpoint not available')
        }
        setLastRefresh(new Date())
        setLoading(false)
    }

    useEffect(() => {
        fetchHormiguero()
        // Poll every 60s for hormiguero (low-power, optional feature)
        const interval = setInterval(fetchHormiguero, 60000)
        return () => clearInterval(interval)
    }, [])

    if (error === 'Endpoint not available' || error?.includes('timeout')) {
        return (
            <div className="card">
                <div className="card-header">
                    <h2>Hormigas (Ants)</h2>
                </div>
                <div className="info-box">
                    <span>ℹ</span> NO_VERIFICADO - Endpoint not available. Confirm the hormiguero window is open.
                </div>
            </div>
        )
    }

    return (
        <div className="card">
            <div className="card-header">
                <h2>Hormigas (Ants) - Read-Only</h2>
                <button onClick={fetchHormiguero} disabled={loading} className="btn-small">
                    {loading ? '⟳' : '↻'}
                </button>
            </div>

            {error && (
                <div className="warning-box">
                    <span>⚠</span> {error}
                </div>
            )}

            {hormiguero && (
                <>
                    <div className="status-row">
                        <span>Status:</span>
                        <span className="status-ok">
                            {hormiguero.status || 'ok'}
                        </span>
                    </div>

                    <div className="status-row">
                        <span>Actions Enabled:</span>
                        <span className={hormiguero.actions_enabled ? 'actions-enabled' : 'actions-disabled'}>
                            {hormiguero.actions_enabled ? 'Yes' : 'No'}
                        </span>
                    </div>

                    {hormiguero.last_scan && (
                        <div className="status-row">
                            <span>Last Scan:</span>
                            <code className="last-scan">{hormiguero.last_scan}</code>
                        </div>
                    )}

                    {debugMode && (
                        <div className="debug-box">
                            <pre>{JSON.stringify(hormiguero, null, 2)}</pre>
                        </div>
                    )}

                    <div className="card-footer">
                        <small>Last refresh: {lastRefresh.toLocaleTimeString()}</small>
                        <button
                            onClick={() => setDebugMode(!debugMode)}
                            className="btn-small btn-auto-margin"
                        >
                            {debugMode ? 'Hide' : 'Show'} JSON
                        </button>
                    </div>
                </>
            )}
        </div>
    )
}
