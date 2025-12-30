import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface AuditRun {
    id: string
    timestamp: string
    status: string
    summary: string
    correlationId?: string | null
    details?: string
}

export function AuditView() {
    const [runs, setRuns] = useState<AuditRun[]>([])
    const [selected, setSelected] = useState<AuditRun | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadAudits()
    }, [])

    async function loadAudits() {
        setLoading(true)
        setError(null)

        try {
            // Try to fetch audit list from API
            const resp = (await apiClient.audit?.()) || Promise.resolve({ ok: false })

            if (resp.ok && resp.data) {
                const auditList = Array.isArray(resp.data) ? resp.data : resp.data.runs || []
                const mapped = auditList.map((run: any) => ({
                    id: run.audit_id || run.run_id || run.id,
                    timestamp: run.run_ts || run.timestamp || new Date().toISOString(),
                    status: run.status || 'unknown',
                    summary: run.summary || 'Audit run',
                    correlationId: run.correlation_id ?? null,
                }))
                setRuns(mapped)
            } else {
                // Fallback: show placeholder
                setRuns([
                    {
                        id: 'placeholder_1',
                        timestamp: new Date().toISOString(),
                        status: 'unavailable',
                        summary: 'Audit service unavailable',
                    },
                ])
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load audits')
        } finally {
            setLoading(false)
        }
    }

    async function downloadAudit(id: string) {
        try {
            if (apiClient.downloadAudit) {
                const resp = await apiClient.downloadAudit(id)
                if (resp.ok) {
                    // Handle file download
                    console.log('Download:', resp.data)
                }
            }
        } catch (err: any) {
            setError(err.message || 'Download failed')
        }
    }

    if (loading) {
        return <div className="view-loading">⟳ Loading audits...</div>
    }

    return (
        <div className="audit-view">
            <h2>Audit Runs</h2>

            {error && <div className="error-banner">{error}</div>}

            <div className="audit-layout">
                <div className="audit-list">
                    <h3>Recent Runs</h3>
                    {runs.length > 0 ? (
                        <div className="run-items">
                            {runs.map((run) => (
                                <div
                                    key={run.id}
                                    className={`run-item ${selected?.id === run.id ? 'selected' : ''}`}
                                    onClick={() => setSelected(run)}
                                >
                                    <div className="run-header">
                                        <span className={`status-badge status-${run.status}`}>
                                            {run.status.toUpperCase()}
                                        </span>
                                        <span className="run-time">
                                            {new Date(run.timestamp).toLocaleString()}
                                        </span>
                                    </div>
                                    <div className="run-summary">
                                        {run.summary}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="empty">No audit runs available</p>
                    )}
                </div>

                <div className="audit-detail">
                    {selected ? (
                        <>
                            <h3>Run Details</h3>
                            <dl className="detail-list">
                                <dt>ID</dt>
                                <dd className="code">{selected.id}</dd>

                                <dt>Status</dt>
                                <dd>
                                    <span className={`status-badge status-${selected.status}`}>
                                        {selected.status}
                                    </span>
                                </dd>

                                <dt>Summary</dt>
                                <dd>{selected.summary}</dd>

                                <dt>Timestamp</dt>
                                <dd>{new Date(selected.timestamp).toISOString()}</dd>
                                {selected.correlationId && (
                                    <>
                                        <dt>Correlation</dt>
                                        <dd className="code">{selected.correlationId}</dd>
                                    </>
                                )}
                            </dl>

                            {selected.details && (
                                <>
                                    <h4>Details</h4>
                                    <pre className="detail-output">{selected.details}</pre>
                                </>
                            )}

                            <div className="detail-actions">
                                <button
                                    onClick={() => downloadAudit(selected.id)}
                                    className="btn-secondary"
                                >
                                    ⬇ Download
                                </button>
                            </div>
                        </>
                    ) : (
                        <p className="empty">Select a run to view details</p>
                    )}
                </div>
            </div>
        </div>
    )
}
