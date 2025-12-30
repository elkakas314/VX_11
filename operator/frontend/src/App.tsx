import { useState, useEffect } from 'react'
import { OverviewView } from './views/OverviewView'
import { ChatView } from './views/ChatView'
import { AuditView } from './views/AuditView'
import { SettingsView } from './views/SettingsView'
import { ModulesView } from './views/ModulesView'
import { HormigueroView } from './views/HormigueroView'
import { LeftRail } from './components/LeftRail'
import { RightDrawer } from './components/RightDrawer'
import { DegradedModeBanner } from './components/DegradedModeBanner'
import { DebugDrawer } from './components/DebugDrawer'
import { apiClient, API_BASE, buildApiUrl } from './services/api'
import { useEventsStore, useWindowStatusStore } from './stores'
import './App.css'

type TabName = 'overview' | 'chat' | 'modules' | 'hormiguero' | 'audit' | 'settings'

export default function App() {
    const [activeTab, setActiveTab] = useState<TabName>('overview')
    const [degraded, setDegraded] = useState(false)
    const [eventsConnected, setEventsConnected] = useState(true)
    const { setEvents } = useEventsStore()
    const { setWindowStatus } = useWindowStatusStore()
    const [debugData] = useState({
        environment: process.env.NODE_ENV,
        apiBase: API_BASE || '(relative)',
        version: '7.0',
    })

    // Check system status on mount
    useEffect(() => {
        checkStatus()
    }, [])

    useEffect(() => {
        let eventSource: EventSource | null = null
        let retryMs = 1000
        let retryTimeout: number | undefined

        const connect = () => {
            const eventsUrl = buildApiUrl('/operator/api/v1/events/stream')
            eventSource = new EventSource(eventsUrl)

            eventSource.onopen = () => {
                setEventsConnected(true)
                retryMs = 1000
            }

            eventSource.addEventListener('snapshot', (event) => {
                try {
                    const data = JSON.parse((event as MessageEvent).data)
                    if (data.events) {
                        setEvents(data.events)
                    }
                    if (data.window) {
                        setWindowStatus(data.window)
                    }
                } catch (err) {
                    console.error('Failed to parse snapshot:', err)
                }
            })

            eventSource.onerror = () => {
                setEventsConnected(false)
                eventSource?.close()
                eventSource = null
                retryTimeout = window.setTimeout(connect, retryMs)
                retryMs = Math.min(retryMs * 2, 30000)
            }
        }

        connect()

        return () => {
            eventSource?.close()
            if (retryTimeout) window.clearTimeout(retryTimeout)
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
                message="Disconnected from events stream. Reconnecting…"
            />

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
                        className={`tab ${activeTab === 'hormiguero' ? 'active' : ''}`}
                        onClick={() => setActiveTab('hormiguero')}
                    >
                        🐜 Hormiguero
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
                    {activeTab === 'hormiguero' && <HormigueroView />}
                    {activeTab === 'audit' && <AuditView />}
                    {activeTab === 'settings' && <SettingsView />}
                </main>

                <RightDrawer activeTab={String(activeTab)} open={true} />
            </div>

            <footer className="app-footer">
                <small>Operator UI • Read-only • Consumes tentaculo_link:8000 only • P0 Complete</small>
            </footer>

            <DebugDrawer data={debugData} title="Environment" />
        </div>
    )
}
