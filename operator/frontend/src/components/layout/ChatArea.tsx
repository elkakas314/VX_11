import { useSessionStore } from '../../context/SessionContext'
import { ChatPanel } from '../ChatPanel'

export function ChatArea() {
    const activeSessionId = useSessionStore((s) => s.activeSessionId)

    if (!activeSessionId) {
        return (
            <main className="bg-slate-950 rounded-lg border border-purple-900/30 shadow-lg flex items-center justify-center">
                <div className="text-center">
                    <div className="text-6xl mb-4">💬</div>
                    <h1 className="text-2xl font-bold text-purple-400 mb-2">No Session Selected</h1>
                    <p className="text-gray-400">Create a new session to start chatting</p>
                </div>
            </main>
        )
    }

    return (
        <main className="bg-slate-950 rounded-lg border border-purple-900/30 shadow-lg flex flex-col overflow-hidden">
            <ChatPanel sessionId={activeSessionId} />
        </main>
    )
}
