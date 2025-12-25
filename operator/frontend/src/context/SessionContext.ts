import { create } from 'zustand'

export interface ChatMessage {
    id: string
    role: 'user' | 'assistant'
    content: string
    module?: string
    timestamp: string
}

export interface Session {
    id: string
    name: string
    messages: ChatMessage[]
    createdAt: string
    updatedAt: string
}

interface SessionStore {
    sessions: Session[]
    activeSessionId: string | null

    // Actions
    createSession: (name: string) => void
    deleteSession: (id: string) => void
    setActiveSession: (id: string) => void
    addMessage: (sessionId: string, message: ChatMessage) => void
    clearMessages: (sessionId: string) => void
}

export const useSessionStore = create<SessionStore>((set) => {
    // Load from localStorage on init
    const savedSessions = localStorage.getItem('vx11_sessions')
    const savedActive = localStorage.getItem('vx11_active_session')

    const initialSessions: Session[] = savedSessions ? JSON.parse(savedSessions) : []
    const initialActive = savedActive || (initialSessions[0]?.id ?? null)

    return {
        sessions: initialSessions,
        activeSessionId: initialActive,

        createSession: (name) =>
            set((state) => {
                const newSession: Session = {
                    id: `sess_${Date.now()}`,
                    name,
                    messages: [],
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString(),
                }
                const updated = [...state.sessions, newSession]
                localStorage.setItem('vx11_sessions', JSON.stringify(updated))
                return { sessions: updated, activeSessionId: newSession.id }
            }),

        deleteSession: (id) =>
            set((state) => {
                const updated = state.sessions.filter((s) => s.id !== id)
                const nextActive =
                    state.activeSessionId === id ? updated[0]?.id ?? null : state.activeSessionId
                localStorage.setItem('vx11_sessions', JSON.stringify(updated))
                localStorage.setItem('vx11_active_session', nextActive ?? '')
                return { sessions: updated, activeSessionId: nextActive }
            }),

        setActiveSession: (id) =>
            set(() => {
                localStorage.setItem('vx11_active_session', id)
                return { activeSessionId: id }
            }),

        addMessage: (sessionId, message) =>
            set((state) => {
                const updated = state.sessions.map((s) =>
                    s.id === sessionId
                        ? {
                            ...s,
                            messages: [...s.messages, message],
                            updatedAt: new Date().toISOString(),
                        }
                        : s
                )
                localStorage.setItem('vx11_sessions', JSON.stringify(updated))
                return { sessions: updated }
            }),

        clearMessages: (sessionId) =>
            set((state) => {
                const updated = state.sessions.map((s) =>
                    s.id === sessionId
                        ? { ...s, messages: [], updatedAt: new Date().toISOString() }
                        : s
                )
                localStorage.setItem('vx11_sessions', JSON.stringify(updated))
                return { sessions: updated }
            }),
    }
})
