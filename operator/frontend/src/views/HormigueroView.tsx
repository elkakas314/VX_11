import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface HormigueroStatus {
    status?: string
    actions_enabled?: boolean
    last_scan?: string
    message?: string
    [key: string]: any
}

export function HormigueroView() {
    const [status, setStatus] = useState<HormigueroStatus | null>(null)
    const [scanResult, setScanResult] = useState<any>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadStatus()
    }, [])

    async function loadStatus() {
        setLoading(true)
        setError(null)

        try {
            const resp = await apiClient.hormigueroStatus()
            if (resp.ok && resp.data) {
                setStatus(resp.data)
            } else {
                setStatus(null)
                setError(resp.error || 'Hormiguero unavailable')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load Hormiguero status')
        } finally {
            setLoading(false)
        }
    }

    async function handleScanOnce() {
        setLoading(true)
        setError(null)
        setScanResult(null)

        try {
            const resp = await apiClient.hormigueroScanOnce()
            if (resp.ok && resp.data) {
                setScanResult(resp.data)
            } else {
                setError(resp.error || 'Scan failed')
            }
        } catch (err: any) {
            setError(err.message || 'Scan failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="hormiguero-view">
            <h2>Hormiguero</h2>

            {error && <div className="error-banner">⚠️ {error}</div>}

            <div className="widget-grid">
                <div className="widget card">
                    <h3>Status</h3>
                    {status ? (
                        <dl className="status-list">
                            <dt>State</dt>
                            <dd>
                                {status.status ||
                                    (status.actions_enabled !== undefined ? 'ok' : 'unknown')}
                            </dd>

                            <dt>Actions Enabled</dt>
                            <dd>{status.actions_enabled ? 'yes' : 'no'}</dd>

                            <dt>Last Scan</dt>
                            <dd>{status.last_scan ?? '—'}</dd>
                        </dl>
                    ) : (
                        <p className="empty">No status available</p>
                    )}
                </div>

                <div className="widget card">
                    <h3>Scan Once</h3>
                    <p className="text-muted">Trigger a one-shot scan via tentaculo_link.</p>
                    <button className="btn-primary" onClick={handleScanOnce} disabled={loading}>
                        {loading ? '⟳ Running…' : 'Run scan'}
                    </button>
                    {scanResult && (
                        <pre className="detail-output">{JSON.stringify(scanResult, null, 2)}</pre>
                    )}
                </div>
            </div>

            <div className="view-actions">
                <button className="btn-secondary" onClick={loadStatus} disabled={loading}>
                    ⟳ Refresh
                </button>
            </div>
        </div>
    )
}
