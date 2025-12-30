import { useEffect, useMemo, useState } from 'react'
import { apiClient } from '../services/api'
import { useWindowStatusStore } from '../stores'

interface SpawnRun {
    id: number
    uuid: string
    name: string
    cmd: string
    status: string
    started_at?: string | null
    ended_at?: string | null
    exit_code?: number | null
    parent_task_id?: string | null
    created_at?: string | null
    stdout_preview?: string
    stderr_preview?: string
}

interface SpawnerStatus {
    status: string
    policy: string
    allowed: boolean
    message?: string
    summary?: {
        runs_by_status?: Record<string, number>
    }
    health?: Record<string, any>
}

export function SpawnerView() {
    const [status, setStatus] = useState<SpawnerStatus | null>(null)
    const [runs, setRuns] = useState<SpawnRun[]>([])
    const [selected, setSelected] = useState<SpawnRun | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [submitResult, setSubmitResult] = useState<string | null>(null)
    const [formState, setFormState] = useState({
        task_name: '',
        task_type: 'spawn',
        cmd: '',
        ttl_seconds: 300,
    })
    const windowStatus = useWindowStatusStore((state) => state.windowStatus)

    const actionAllowed = useMemo(() => {
        if (!windowStatus) return false
        return (
            windowStatus.mode === 'window_active' &&
            windowStatus.services?.includes('spawner')
        )
    }, [windowStatus])

    useEffect(() => {
        refreshData()
    }, [])

    async function refreshData() {
        setLoading(true)
        setError(null)
        try {
            const [statusResp, runsResp] = await Promise.all([
                apiClient.spawnerStatus(),
                apiClient.spawnerRuns(),
            ])
            if (statusResp.ok && statusResp.data) {
                setStatus(statusResp.data)
            }
            if (runsResp.ok && runsResp.data) {
                setRuns(runsResp.data.runs || [])
            }
        } catch (err: any) {
            setError(err.message || 'Failed to load spawner data')
        } finally {
            setLoading(false)
        }
    }

    async function submitSpawn() {
        setSubmitResult(null)
        setError(null)
        try {
            const resp = await apiClient.spawnerSubmit({
                task_name: formState.task_name || 'operator_spawn',
                task_type: formState.task_type || 'spawn',
                cmd: formState.cmd,
                ttl_seconds: Number(formState.ttl_seconds) || 300,
            })
            if (resp.ok) {
                setSubmitResult('Spawn request queued with Madre')
                await refreshData()
            } else {
                setSubmitResult(resp.error || 'Spawn request blocked')
            }
        } catch (err: any) {
            setError(err.message || 'Spawn submit failed')
        }
    }

    if (loading) {
        return <div className="view-loading">⟳ Loading spawner telemetry...</div>
    }

    return (
        <div className="spawner-view">
            <div className="view-header">
                <h2>Spawner</h2>
                <button onClick={refreshData} className="btn-secondary">
                    ⟳ Refresh
                </button>
            </div>

            {error && <div className="error-banner">{error}</div>}

            <div className="spawner-grid">
                <section className="card spawner-status">
                    <h3>Status</h3>
                    <dl className="status-list">
                        <dt>Policy</dt>
                        <dd>{status?.policy || 'unknown'}</dd>
                        <dt>Allowed</dt>
                        <dd>{actionAllowed ? 'Yes' : 'No'}</dd>
                        <dt>Service</dt>
                        <dd>{status?.status || 'unknown'}</dd>
                    </dl>
                    {status?.summary?.runs_by_status && (
                        <div className="status-metrics">
                            {Object.entries(status.summary.runs_by_status).map(([key, value]) => (
                                <div key={key} className="status-metric">
                                    <span className="metric-label">{key}</span>
                                    <span className="metric-value">{value}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                <section className="card spawner-actions">
                    <h3>Action Window</h3>
                    {!actionAllowed && (
                        <div className="degraded-banner">
                            Actions locked in <strong>solo_madre</strong>. Request a temporary power
                            window from Madre that includes <code>spawner</code> (TTL-bound) to
                            enable submissions.
                        </div>
                    )}
                    <div className="form-grid">
                        <label>
                            Task Name
                            <input
                                type="text"
                                value={formState.task_name}
                                disabled={!actionAllowed}
                                onChange={(e) =>
                                    setFormState((prev) => ({ ...prev, task_name: e.target.value }))
                                }
                            />
                        </label>
                        <label>
                            Task Type
                            <input
                                type="text"
                                value={formState.task_type}
                                disabled={!actionAllowed}
                                onChange={(e) =>
                                    setFormState((prev) => ({ ...prev, task_type: e.target.value }))
                                }
                            />
                        </label>
                        <label>
                            Command
                            <input
                                type="text"
                                value={formState.cmd}
                                disabled={!actionAllowed}
                                onChange={(e) =>
                                    setFormState((prev) => ({ ...prev, cmd: e.target.value }))
                                }
                            />
                        </label>
                        <label>
                            TTL (sec)
                            <input
                                type="number"
                                min={60}
                                value={formState.ttl_seconds}
                                disabled={!actionAllowed}
                                onChange={(e) =>
                                    setFormState((prev) => ({
                                        ...prev,
                                        ttl_seconds: Number(e.target.value),
                                    }))
                                }
                            />
                        </label>
                    </div>
                    <div className="view-actions">
                        <button
                            className="btn-primary"
                            disabled={!actionAllowed}
                            onClick={submitSpawn}
                        >
                            🚀 Submit Spawn (via Madre)
                        </button>
                    </div>
                    {submitResult && <div className="success-banner">{submitResult}</div>}
                </section>
            </div>

            <section className="card spawner-runs">
                <h3>Recent Runs</h3>
                {runs.length === 0 ? (
                    <p className="empty">No spawner runs recorded</p>
                ) : (
                    <div className="runs-layout">
                        <div className="runs-list">
                            {runs.map((run) => (
                                <button
                                    key={run.uuid}
                                    className={`run-row ${selected?.uuid === run.uuid ? 'selected' : ''}`}
                                    onClick={() => setSelected(run)}
                                >
                                    <div className="run-title">
                                        <span>{run.name}</span>
                                        <span className={`status-badge status-${run.status || 'unknown'}`}>
                                            {run.status || 'unknown'}
                                        </span>
                                    </div>
                                    <div className="run-meta">
                                        <span className="code">{run.uuid}</span>
                                        <span>{run.created_at || 'n/a'}</span>
                                    </div>
                                </button>
                            ))}
                        </div>

                        <div className="runs-detail">
                            {selected ? (
                                <>
                                    <h4>Run Detail</h4>
                                    <dl className="detail-list">
                                        <dt>UUID</dt>
                                        <dd className="code">{selected.uuid}</dd>
                                        <dt>Status</dt>
                                        <dd>{selected.status}</dd>
                                        <dt>Command</dt>
                                        <dd className="code">{selected.cmd || 'n/a'}</dd>
                                        <dt>Started</dt>
                                        <dd>{selected.started_at || 'n/a'}</dd>
                                        <dt>Ended</dt>
                                        <dd>{selected.ended_at || 'n/a'}</dd>
                                        <dt>Exit Code</dt>
                                        <dd>{selected.exit_code ?? 'n/a'}</dd>
                                    </dl>
                                    <div className="log-preview">
                                        <h5>Stdout</h5>
                                        <pre>{selected.stdout_preview || '—'}</pre>
                                    </div>
                                    <div className="log-preview">
                                        <h5>Stderr</h5>
                                        <pre>{selected.stderr_preview || '—'}</pre>
                                    </div>
                                </>
                            ) : (
                                <p className="empty">Select a run to inspect summary logs</p>
                            )}
                        </div>
                    </div>
                )}
            </section>
        </div>
    )
}
