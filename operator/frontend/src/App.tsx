import { useState } from 'react'
import { StatusCard } from './components/StatusCard'
import { PowerCard } from './components/PowerCard'
import { ChatPanel } from './components/ChatPanel'
import { HormigueroPanel } from './components/HormigueroPanel'
import { P0ChecksPanel } from './components/P0ChecksPanel'
import { DebugDrawer } from './components/DebugDrawer'
import './App.css'

type TabName = 'dashboard' | 'chat' | 'hormigas' | 'checks'

export default function App() {
    const [activeTab, setActiveTab] = useState<TabName>('dashboard')
    const [debugData] = useState({
        environment: process.env.NODE_ENV,
        apiBase: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
        version: '7.0',
    })

    return (
        <div className="app">
            <header className="app-header">
                <div className="header-title">
                    <h1>VX11 Operator</h1>
                    <span className="version">v7.0</span>
                </div>
                <nav className="tabs">
                    <button
                        className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
                        onClick={() => setActiveTab('dashboard')}
                    >
                        📊 Dashboard
                    </button>
                    <button
                        className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
                        onClick={() => setActiveTab('chat')}
                    >
                        💬 Chat
                    </button>
                    <button
                        className={`tab ${activeTab === 'hormigas' ? 'active' : ''}`}
                        onClick={() => setActiveTab('hormigas')}
                    >
                        🐜 Hormigas
                    </button>
                    <button
                        className={`tab ${activeTab === 'checks' ? 'active' : ''}`}
                        onClick={() => setActiveTab('checks')}
                    >
                        ✓ P0 Checks
                    </button>
                </nav>
            </header>

            <main className="app-main">
                {activeTab === 'dashboard' && (
                    <div className="grid-2col">
                        <StatusCard />
                        <PowerCard />
                    </div>
                )}

                {activeTab === 'chat' && <ChatPanel />}

                {activeTab === 'hormigas' && <HormigueroPanel />}

                {activeTab === 'checks' && <P0ChecksPanel />}
            </main>

            <footer className="app-footer">
                <small>Operator UI • Read-only • Consumes tentaculo_link:8000 only</small>
            </footer>

            <DebugDrawer data={debugData} title="Environment" />
        </div>
    )
}
