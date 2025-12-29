import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface RightDrawerProps {
    activeTab?: string
    open?: boolean
}

interface SystemStatus {
    policy: string
    window?: {
        mode?: string
        services?: string[]
    }
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
                            <dd>{status.window?.mode || 'unknown'}</dd>
                        </dl>
                    </div>

                    <div className="drawer-section">
                        <h5>Active ({status.window?.services?.length || 0})</h5>
                        <div className="active-list">
                            {status.window?.services && status.window.services.length > 0 ? (
                                status.window.services.map((mod) => (
                                    <div key={mod} className="active-item">
                                        ✓ {mod}
                                    </div>
                                ))
                            ) : (
                                <p className="empty">None</p>
                            )}
                        </div>
                    </div>
                </>
            ) : (
                <p className="empty">Unable to load status</p>
            )}
        </aside>
    )
}
