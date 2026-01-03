import { useState, useEffect } from 'react'
import { OverviewView } from './views/OverviewView'
import { ChatView } from './views/ChatView'
import { AuditView } from './views/AuditView'
import { SettingsView } from './views/SettingsView'
import { ModulesView } from './views/ModulesView'
import { HormigueroView } from './views/HormigueroView'
import { SpawnerView } from './views/SpawnerView'
import { LeftRail } from './components/LeftRail'
import { RightDrawer } from './components/RightDrawer'
import { DegradedModeBanner } from './components/DegradedModeBanner'
import { DebugDrawer } from './components/DebugDrawer'
import { TokenRequiredBanner } from './components/TokenRequiredBanner'
import { apiClient, API_BASE, getCurrentToken } from './services/api'
import { useEventsStore, useWindowStatusStore } from './stores'
import './App.css'

type TabName =
    | 'overview'
    | 'chat'
    | 'modules'
    | 'topology'
    | 'hormiguero'
    | 'jobs'
    | 'spawner'
    | 'audit'
    | 'settings'

export default function App() {
    const [activeTab, setActiveTab] = useState<TabName>('overview')
    const [degraded, setDegraded] = useState(false)
    const [eventsConnected, setEventsConnected] = useState(true)
    const [tokenConfigured, setTokenConfigured] = useState(!!getCurrentToken())
    const { setEvents } = useEventsStore()
    const { setWindowStatus } = useWindowStatusStore()
    const [debugData] = useState({
        environment: (globalThis as any).process?.env?.NODE_ENV,
        apiBase: API_BASE || '(relative)',
        version: '7.0',
    })

    // Check system status on mount
    useEffect(() => {
        checkStatus()
    }, [])

    // Listen for token changes (e.g., from TokenSettings component)
    useEffect(() => {
        const handleStorageChange = () => {
            setTokenConfigured(!!getCurrentToken())
        }
        window.addEventListener('storage', handleStorageChange)
        // Also check periodically in case token was set in same tab
        const interval = setInterval(() => {
            setTokenConfigured(!!getCurrentToken())
        }, 1000)
        return () => {
            window.removeEventListener('storage', handleStorageChange)
            clearInterval(interval)
        }
    }, [])

    useEffect(() => {
        let active = true
        let intervalId: number | undefined

        const poll = async () => {
            try {
                const [eventsResp, windowResp] = await Promise.all([
                    apiClient.events(),
                    apiClient.windows(),
                ])
                if (!active) return
                if (eventsResp.ok && eventsResp.data) {
                    const events = eventsResp.data.events || eventsResp.data
                    setEvents(events)
                    setEventsConnected(true)
                } else if (eventsResp.status === 403 && eventsResp.data?.status === 'OFF_BY_POLICY') {
                    // OFF_BY_POLICY in solo_madre is expected, not an error
                    // Keep eventsConnected=true to avoid showing "Disconnected" banner
                    setEventsConnected(true)
                } else {
                    // Real error (not 403 OFF_BY_POLICY)
                    setEventsConnected(false)
                }
                if (windowResp.ok && windowResp.data) {
                    setWindowStatus(windowResp.data)
                }
            } catch (err) {
                if (active) {
                    setEventsConnected(false)
                }
            }
        }

        poll()
        intervalId = window.setInterval(poll, 15000)

        return () => {
            active = false
            if (intervalId) window.clearInterval(intervalId)
        }
    }, [setEvents, setWindowStatus])

    async function checkStatus() {
        try {
            const resp = await apiClient.status()
            if (resp.ok && resp.data) {
                setDegraded(resp.data.degraded || false)
            }
        } catch (err) {
            console.error('Failed to check status:', err)
        }
    }

    return (
        <div className="app">
            <DegradedModeBanner show={degraded} />
            <DegradedModeBanner
                show={!eventsConnected}
                message="Disconnected from events feed. Retrying…"
            />

            {!tokenConfigured && <TokenRequiredBanner />}

            <header className="app-header">
                <div className="header-title">
                    <h1>VX11 Operator</h1>
                    <span className="version">v7.0 (P0)</span>
                </div>
                <nav className="tabs">
                    <button
                        className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                        onClick={() => setActiveTab('overview')}
                    >
                        🐜 Ant View
                    </button>
                    <button
                        className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
                        onClick={() => setActiveTab('chat')}
                    >
                        💬 Chat
                    </button>
                    <button
                        className={`tab ${activeTab === 'modules' ? 'active' : ''}`}
                        onClick={() => setActiveTab('modules')}
                    >
                        🧭 Modules
                    </button>
                    <button
                        className={`tab ${activeTab === 'topology' ? 'active' : ''}`}
                        onClick={() => setActiveTab('topology')}
                    >
                        🗺️ Topology
                    </button>
                    <button
                        className={`tab ${activeTab === 'hormiguero' ? 'active' : ''}`}
                        onClick={() => setActiveTab('hormiguero')}
                    >
                        🐜 Hormiguero
                    </button>
                    <button
                        className={`tab ${activeTab === 'jobs' ? 'active' : ''}`}
                        onClick={() => setActiveTab('jobs')}
                    >
                        ⚙️ Jobs
                    </button>
                    <button
                        className={`tab ${activeTab === 'spawner' ? 'active' : ''}`}
                        onClick={() => setActiveTab('spawner')}
                    >
                        🧬 Spawner
                    </button>
                    <button
                        className={`tab ${activeTab === 'audit' ? 'active' : ''}`}
                        onClick={() => setActiveTab('audit')}
                    >
                        ✓ Audit Runs
                    </button>
                    <button
                        className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
                        onClick={() => setActiveTab('settings')}
                    >
                        ⚙️ Settings
                    </button>
                </nav>
            </header>

            <div className="app-container">
                <LeftRail activeTab={String(activeTab)} onTabChange={(tab) => setActiveTab(tab as TabName)} />

                <main className="app-main">
                    {activeTab === 'overview' && <OverviewView />}
                    {activeTab === 'chat' && <ChatView />}
                    {activeTab === 'modules' && <ModulesView />}
                    {activeTab === 'topology' && (
                        <div className="view-stub">
                            <h2>Topology (P1)</h2>
                            <p>React Flow topology visualization — coming soon</p>
                        </div>
                    )}
                    {activeTab === 'hormiguero' && <HormigueroView />}
                    {activeTab === 'jobs' && (
                        <div className="view-stub">
                            <h2>Jobs (P1)</h2>
                            <p>Background jobs and task board — coming soon</p>
                        </div>
                    )}
                    {activeTab === 'spawner' && <SpawnerView />}
                    {activeTab === 'audit' && <AuditView />}
                    {activeTab === 'settings' && <SettingsView />}
                </main>

                <RightDrawer activeTab={String(activeTab)} open={true} />
            </div >

            <footer className="app-footer">
                <small>Operator UI • Read-only • Consumes tentaculo_link:8000 only • P0 Complete</small>
            </footer>

            <DebugDrawer data={debugData} title="Environment" />
        </div >
    )
}
