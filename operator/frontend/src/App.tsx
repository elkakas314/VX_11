import { useState, useEffect } from 'react'
import { OverviewView } from './views/OverviewView'
import { ChatView } from './views/ChatView'
import { AuditView } from './views/AuditView'
import { SettingsView } from './views/SettingsView'
import { LeftRail } from './components/LeftRail'
import { RightDrawer } from './components/RightDrawer'
import { DegradedModeBanner } from './components/DegradedModeBanner'
import { DebugDrawer } from './components/DebugDrawer'
import { apiClient } from './services/api'
import './App.css'

type TabName = 'overview' | 'chat' | 'topology' | 'hormiguero' | 'jobs' | 'audit' | 'explorer' | 'settings'

export default function App() {
    const [activeTab, setActiveTab] = useState<TabName>('overview')
    const [degraded, setDegraded] = useState(false)
    const [debugData] = useState({
        environment: process.env.NODE_ENV,
        apiBase: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
        version: '7.0',
    })

    // Check system status on mount
    useEffect(() => {
        checkStatus()
    }, [])

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
                        📊 Overview
                    </button>
                    <button
                        className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
                        onClick={() => setActiveTab('chat')}
                    >
                        💬 Chat
                    </button>
                    <button
                        className={`tab ${activeTab === 'topology' ? 'active' : ''}`}
                        onClick={() => setActiveTab('topology')}
                    >
                        🔗 Topology
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
                        className={`tab ${activeTab === 'audit' ? 'active' : ''}`}
                        onClick={() => setActiveTab('audit')}
                    >
                        ✓ Audit
                    </button>
                    <button
                        className={`tab ${activeTab === 'explorer' ? 'active' : ''}`}
                        onClick={() => setActiveTab('explorer')}
                    >
                        🔍 Explorer
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
                    {activeTab === 'topology' && (
                        <div className="view-stub">
                            <h2>Topology (P1)</h2>
                            <p>React Flow topology visualization — coming soon</p>
                        </div>
                    )}
                    {activeTab === 'hormiguero' && (
                        <div className="view-stub">
                            <h2>Hormiguero (P1)</h2>
                            <p>Incident visualization and management — coming soon</p>
                        </div>
                    )}
                    {activeTab === 'jobs' && (
                        <div className="view-stub">
                            <h2>Jobs (P1)</h2>
                            <p>Background jobs and task board — coming soon</p>
                        </div>
                    )}
                    {activeTab === 'audit' && <AuditView />}
                    {activeTab === 'explorer' && (
                        <div className="view-stub">
                            <h2>Explorer (P1)</h2>
                            <p>File and data explorer — coming soon</p>
                        </div>
                    )}
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
