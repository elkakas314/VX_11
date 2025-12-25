import { useEffect } from 'react'
import './styles/App.css'
import { Sidebar } from './components/Sidebar'
import { ChatArea } from './components/layout/ChatArea'
import { RightPanel } from './components/layout/RightPanel'
import { useSessionStore } from './context/SessionContext'

export default function App() {
    const sessions = useSessionStore((s) => s.sessions)

    // Create default session if none exists
    useEffect(() => {
        if (sessions.length === 0) {
            useSessionStore.getState().createSession('Default Session')
        }
        document.documentElement.classList.add('dark')
    }, [])

    return (
        <div className="grid grid-cols-[280px_1fr_320px] h-screen bg-slate-950 gap-2 p-2 overflow-hidden">
            {/* LEFT: Sessions + Module Bubbles */}
            <Sidebar />

            {/* CENTER: Chat Interface */}
            <ChatArea />

            {/* RIGHT: Logs + JSON + ModuleStatus */}
            <RightPanel />
        </div>
    )
}
