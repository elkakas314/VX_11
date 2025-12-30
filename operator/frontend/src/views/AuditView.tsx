import { useEffect, useState } from 'react'
import { apiClient, buildApiUrl } from '../services/api'

interface AuditRun {
    run_id: string
    run_ts?: string | null
    status?: string
    files_count?: number
    size_bytes?: number
    source?: string
}

interface AuditDetail {
    run_id: string
    run_ts?: string | null
    status?: string
    files?: { path: string; size_bytes: number }[]
    findings?: { severity: string; title?: string; detail?: string }[]
    artifacts?: string[]
}

export function AuditView() {
    const [runs, setRuns] = useState<AuditRun[]>([])
    const [selected, setSelected] = useState<AuditRun | null>(null)
    const [detail, setDetail] = useState<AuditDetail | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadAudits()
    }, [])

    async function loadAudits() {
        setLoading(true)
        setError(null)

        try {
            const resp = await apiClient.auditRuns()
            if (resp.ok && resp.data?.runs) {
                setRuns(resp.data.runs as AuditRun[])
            } else {
                setRuns([])
                setError(resp.error || 'No audit runs available')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load audits')
        } finally {
            setLoading(false)
        }
    }

    async function loadDetail(run: AuditRun) {
        setSelected(run)
        setDetail(null)
        setError(null)

        try {
            const resp = await apiClient.auditDetail(run.run_id)
            if (resp.ok && resp.data) {
                setDetail(resp.data as AuditDetail)
            } else {
                setError(resp.error || 'Failed to load audit detail')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load audit detail')
        }
    }

    function downloadAudit(runId: string) {
        window.open(buildApiUrl(`/operator/api/audit/${runId}/download`), '_blank')
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
                                    key={run.run_id}
                                    className={`run-item ${selected?.run_id === run.run_id ? 'selected' : ''}`}
                                    onClick={() => loadDetail(run)}
                                >
                                    <div className="run-header">
                                        <span className={`status-badge status-${run.status || 'ok'}`}>
                                            {(run.status || 'available').toUpperCase()}
                                        </span>
                                        <span className="run-time">
                                            {run.run_ts
                                                ? new Date(run.run_ts).toLocaleString()
                                                : run.run_id}
                                        </span>
                                    </div>
                                    <div className="run-summary">
                                        {run.files_count ?? 0} files • {Math.round((run.size_bytes || 0) / 1024)} KB
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="empty">No audit runs available</p>
                    )}
                </div>

                <div className="audit-detail">
                    {detail ? (
                        <>
                            <h3>Run Details</h3>
                            <dl className="detail-list">
                                <dt>ID</dt>
                                <dd className="code">{detail.run_id}</dd>

                                <dt>Status</dt>
                                <dd>
                                    <span className={`status-badge status-${detail.status || 'ok'}`}>
                                        {detail.status || 'available'}
                                    </span>
                                </dd>

                                <dt>Timestamp</dt>
                                <dd>{detail.run_ts ? new Date(detail.run_ts).toISOString() : '—'}</dd>

                                <dt>Files</dt>
                                <dd>{detail.files?.length ?? detail.artifacts?.length ?? 0}</dd>
                            </dl>

                            {detail.files && detail.files.length > 0 && (
                                <>
                                    <h4>Artifacts</h4>
                                    <pre className="detail-output">
                                        {detail.files
                                            .slice(0, 20)
                                            .map((file) => `${file.path} (${file.size_bytes} bytes)`)
                                            .join('\n')}
                                    </pre>
                                </>
                            )}

                            <div className="detail-actions">
                                <button onClick={() => downloadAudit(detail.run_id)} className="btn-secondary">
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
