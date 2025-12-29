import { useEffect, useState } from 'react'
import { apiClient } from '../services/api'

interface LeftRailProps {
    activeTab?: string
    onTabChange?: (tab: string) => void
}

export function LeftRail({ activeTab = 'overview', onTabChange }: LeftRailProps) {
    const [modules, setModules] = useState<string[]>([])
    const [searchTerm, setSearchTerm] = useState('')
    const [sessions, setSessions] = useState<Array<{ id: string; name: string }>>([])

    useEffect(() => {
        loadModules()
    }, [])

    async function loadModules() {
        try {
            const resp = await apiClient.modules()
            if (resp.ok && resp.data) {
                const mods = resp.data.modules ? Object.keys(resp.data.modules) : []
                setModules(mods)
            }
        } catch (err) {
            console.error('Failed to load modules:', err)
        }
    }

    const filteredModules = modules.filter((m) =>
        m.toLowerCase().includes(searchTerm.toLowerCase())
    )

    const sessionsData = [
        { id: 'session_1', name: 'Current Chat' },
        { id: 'session_2', name: 'Previous Audit' },
    ]

    return (
        <aside className="left-rail">
            <div className="rail-section">
                <h4>Sessions</h4>
                <div className="session-list">
                    {sessionsData.map((s) => (
                        <button
                            key={s.id}
                            className="session-item"
                            onClick={() => onTabChange?.('chat')}
                        >
                            {s.name}
                        </button>
                    ))}
                </div>
            </div>

            <div className="rail-section">
                <h4>Modules</h4>
                <input
                    type="text"
                    placeholder="Search modules..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="module-search"
                />
                <div className="module-list-rail">
                    {filteredModules.length > 0 ? (
                        filteredModules.map((mod) => (
                            <div key={mod} className="module-item-rail">
                                <span className="module-dot">●</span>
                                <span className="module-name">{mod}</span>
                            </div>
                        ))
                    ) : (
                        <p className="empty">No modules found</p>
                    )}
                </div>
            </div>

            <div className="rail-footer">
                <button onClick={loadModules} className="btn-icon" title="Refresh modules">
                    ⟳
                </button>
            </div>
        </aside>
    )
}
