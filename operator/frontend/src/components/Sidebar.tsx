import { useSessionStore } from '../context/SessionContext'

const MODULES = [
    { name: 'madre', color: 'bg-purple-900/50', border: 'border-purple-500', icon: '🧠' },
    { name: 'switch', color: 'bg-blue-900/50', border: 'border-blue-500', icon: '⚡' },
    { name: 'hermes', color: 'bg-amber-900/50', border: 'border-amber-500', icon: '📡' },
    { name: 'hormiguero', color: 'bg-green-900/50', border: 'border-green-500', icon: '🐜' },
    { name: 'spawner', color: 'bg-cyan-900/50', border: 'border-cyan-500', icon: '🌊' },
    { name: 'tentaculo', color: 'bg-red-900/50', border: 'border-red-500', icon: '🧬' },
    { name: 'shubniggurath', color: 'bg-indigo-900/50', border: 'border-indigo-500', icon: '👁️' },
    { name: 'mcp', color: 'bg-pink-900/50', border: 'border-pink-500', icon: '🔮' },
]

export function Sidebar() {
    const { sessions, activeSessionId, createSession, setActiveSession, deleteSession } =
        useSessionStore()

    const activeSession = sessions.find((s) => s.id === activeSessionId)

    return (
        <aside className="bg-slate-900 rounded-lg flex flex-col border border-purple-900/50 shadow-lg">
            {/* Header */}
            <div className="p-4 border-b border-purple-900/30">
                <h2 className="text-sm font-bold text-purple-400 mb-3">Sessions</h2>
                <button
                    onClick={() => createSession(`Session ${sessions.length + 1}`)}
                    className="w-full py-2 px-3 bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 text-xs rounded-lg transition-colors border border-purple-500/50"
                >
                    + New Session
                </button>
            </div>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {sessions.length === 0 ? (
                    <div className="text-center text-gray-500 text-xs py-8">
                        No sessions yet
                    </div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.id}
                            onClick={() => setActiveSession(session.id)}
                            className={`p-2 rounded-lg cursor-pointer transition-all text-xs ${activeSessionId === session.id
                                    ? 'bg-purple-600/40 border border-purple-400'
                                    : 'bg-slate-800/50 border border-slate-700 hover:border-purple-600/50'
                                }`}
                        >
                            <div className="flex items-center justify-between">
                                <span className="font-medium text-gray-200 truncate">{session.name}</span>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        deleteSession(session.id)
                                    }}
                                    className="text-red-400 hover:text-red-300 font-bold text-xs opacity-0 group-hover:opacity-100"
                                >
                                    ✕
                                </button>
                            </div>
                            <span className="text-gray-500 text-xs">{session.messages.length} msgs</span>
                        </div>
                    ))
                )}
            </div>

            {/* Module Bubbles */}
            <div className="p-3 border-t border-purple-900/30">
                <div className="text-xs font-bold text-purple-400 mb-2">Modules</div>
                <div className="grid grid-cols-2 gap-2">
                    {MODULES.map((mod) => (
                        <div
                            key={mod.name}
                            className={`${mod.color} ${mod.border} border p-2 rounded-lg text-center cursor-pointer hover:opacity-80 transition-opacity`}
                            title={mod.name}
                        >
                            <div className="text-lg">{mod.icon}</div>
                            <div className="text-xs text-gray-300 capitalize">{mod.name}</div>
                            <div className="w-2 h-2 bg-green-500 rounded-full mx-auto mt-1 animate-pulse"></div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Footer */}
            <div className="p-2 border-t border-purple-900/30 text-center text-xs text-gray-600">
                {activeSession ? `${activeSession.messages.length} messages` : 'No session'}
            </div>
        </aside>
    )
}
