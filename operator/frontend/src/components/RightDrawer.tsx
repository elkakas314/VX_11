import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface RightDrawerProps {
    activeTab?: string
    open?: boolean
}

interface SystemStatus {
    policy: string
    mode: string
    active_modules: string[]
    daughters: string[]
    recent_events: Array<{
        timestamp: number
        type: string
        message: string
    }>
}

export function RightDrawer({ activeTab = 'overview', open = true }: RightDrawerProps) {
    const [status, setStatus] = useState<SystemStatus | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        loadStatus()
    }, [])

    async function loadStatus() {
        setLoading(true)
        try {
            const resp = await apiClient.status()
            if (resp.ok && resp.data) {
                setStatus(resp.data)
            }
        } catch (err) {
            console.error('Failed to load status:', err)
        } finally {
            setLoading(false)
        }
    }

    if (!open) return null

    return (
        <aside className="right-drawer">
            <div className="drawer-header">
                <h4>System</h4>
                <button onClick={loadStatus} className="btn-icon" title="Refresh">
                    ⟳
                </button>
            </div>

            {loading ? (
                <div className="drawer-loading">⟳ Loading...</div>
            ) : status ? (
                <>
                    <div className="drawer-section">
                        <h5>Mode & Policy</h5>
                        <dl className="drawer-list">
                            <dt>Policy</dt>
                            <dd className="badge">{status.policy}</dd>

                            <dt>Mode</dt>
                            <dd>{status.mode}</dd>
                        </dl>
                    </div>

                    <div className="drawer-section">
                        <h5>Active ({status.active_modules.length})</h5>
                        <div className="active-list">
                            {status.active_modules.length > 0 ? (
                                status.active_modules.map((mod) => (
                                    <div key={mod} className="active-item">
                                        ✓ {mod}
                                    </div>
                                ))
                            ) : (
                                <p className="empty">None</p>
                            )}
                        </div>
                    </div>

                    {status.daughters && status.daughters.length > 0 && (
                        <div className="drawer-section">
                            <h5>Daughters ({status.daughters.length})</h5>
                            <div className="daughters-list">
                                {status.daughters.map((d) => (
                                    <div key={d} className="daughter-item">
                                        🔗 {d}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {status.recent_events && status.recent_events.length > 0 && (
                        <div className="drawer-section">
                            <h5>Recent Events</h5>
                            <div className="events-list">
                                {status.recent_events.slice(0, 3).map((evt, idx) => (
                                    <div key={idx} className="event-item">
                                        <span className="event-type">[{evt.type}]</span>
                                        <span className="event-msg">{evt.message}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <p className="empty">Unable to load status</p>
            )}
        </aside>
    )
}
