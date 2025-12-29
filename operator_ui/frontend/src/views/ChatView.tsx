import { useEffect, useRef, useState } from 'react'
import { apiClient } from '../services/api'
import { CoDevView } from './CoDevView'

interface ChatMessage {
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp: number
}

interface SessionData {
    id: string
    messages: ChatMessage[]
    degraded?: boolean
}

interface WindowStatus {
    status: 'open' | 'none' | 'error'
    window_id?: string
    ttl_remaining_sec?: number
    deadline?: string
}

export function ChatView() {
    const [session, setSession] = useState<SessionData>({
        id: `session_${Date.now()}`,
        messages: [],
    })
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [windowStatus, setWindowStatus] = useState<WindowStatus>({ status: 'none' })
    const [windowLoading, setWindowLoading] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [session.messages])

    // Poll window status on mount and every 10s
    useEffect(() => {
        const checkWindowStatus = async () => {
            try {
                const resp = await apiClient.get('/operator/api/chat/window/status')
                if (resp.ok && resp.data) {
                    setWindowStatus(resp.data)
                }
            } catch (err) {
                // Silent fail, window status is informational
            }
        }

        checkWindowStatus()
        const interval = setInterval(checkWindowStatus, 10000)
        return () => clearInterval(interval)
    }, [])

    async function handleOpenWindow() {
        setWindowLoading(true)
        setError(null)

        try {
            const resp = await apiClient.post('/operator/api/chat/window/open', {
                services: ['switch'],
                ttl_sec: 600,
                mode: 'ttl',
                reason: 'operator_manual_10min',
            })

            if (resp.ok && resp.data) {
                setWindowStatus({
                    status: 'open',
                    window_id: resp.data.window_id,
                    ttl_remaining_sec: resp.data.ttl_remaining_sec,
                    deadline: resp.data.deadline,
                })
                setError(null)
            } else {
                throw new Error(resp.error || 'Failed to open window')
            }
        } catch (err: any) {
            setError(`Window error: ${err.message}`)
        } finally {
            setWindowLoading(false)
        }
    }

    async function handleCloseWindow() {
        setWindowLoading(true)
        setError(null)

        try {
            const resp = await apiClient.post('/operator/api/chat/window/close', {})

            if (resp.ok) {
                setWindowStatus({ status: 'none' })
                setError(null)
            } else {
                throw new Error(resp.error || 'Failed to close window')
            }
        } catch (err: any) {
            setError(`Close error: ${err.message}`)
        } finally {
            setWindowLoading(false)
        }
    }

    async function handleSend() {
        // P12/P13: Chat only works when window is OPEN
        if (windowStatus.status !== 'open') {
            setError('Chat window is CLOSED. Click "Open 10 min" to enable chat.')
            return
        }

        if (!input.trim()) return

        // Add user message
        const userMsg: ChatMessage = {
            id: `msg_${Date.now()}`,
            role: 'user',
            content: input,
            timestamp: Date.now(),
        }

        setSession((prev) => ({
            ...prev,
            messages: [...prev.messages, userMsg],
        }))

        setInput('')
        setLoading(true)
        setError(null)

        try {
            const resp = await apiClient.chat(input, session.id)

            if (resp.ok && resp.data) {
                const assistantMsg: ChatMessage = {
                    id: `msg_${Date.now()}`,
                    role: 'assistant',
                    content: resp.data.response || resp.data.message || 'No response',
                    timestamp: Date.now(),
                }

                setSession((prev) => ({
                    ...prev,
                    messages: [...prev.messages, assistantMsg],
                    degraded: resp.data.degraded || false,
                }))
            } else {
                throw new Error(resp.error || 'Chat request failed')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to send message')

            const errorMsg: ChatMessage = {
                id: `msg_${Date.now()}`,
                role: 'system',
                content: `Error: ${err.message}`,
                timestamp: Date.now(),
            }

            setSession((prev) => ({
                ...prev,
                messages: [...prev.messages, errorMsg],
            }))
        } finally {
            setLoading(false)
        }
    }

    const windowCountdown = windowStatus.ttl_remaining_sec
        ? Math.max(0, Math.floor(windowStatus.ttl_remaining_sec))
        : 0

    return (
        <div className="chat-view">
            <div className="chat-header">
                <h2>Chat</h2>
                <div className="window-status-badge">
                    {windowStatus.status === 'open' ? (
                        <>
                            <span className="badge-open">✓ OPEN</span>
                            <span className="countdown">({windowCountdown}s)</span>
                            <button
                                onClick={handleCloseWindow}
                                disabled={windowLoading}
                                className="btn-sm btn-danger"
                                title="Close chat window"
                            >
                                Close
                            </button>
                        </>
                    ) : (
                        <>
                            <span className="badge-closed">⊘ CLOSED</span>
                            <button
                                onClick={handleOpenWindow}
                                disabled={windowLoading}
                                className="btn-sm btn-primary"
                                title="Open chat window for 10 minutes"
                            >
                                {windowLoading ? '⟳' : 'Open 10 min'}
                            </button>
                        </>
                    )}
                </div>
            </div>

            <div className="chat-container">
                <div className="messages">
                    {session.messages.length === 0 && windowStatus.status === 'none' && (
                        <div className="message-empty">
                            <p>💬 Open a chat window to start conversing</p>
                        </div>
                    )}
                    {session.messages.map((msg) => (
                        <div key={msg.id} className={`message message-${msg.role}`}>
                            <div className="message-header">
                                <span className="message-role">
                                    {msg.role === 'user' ? '👤' : msg.role === 'assistant' ? '🤖' : '⚠️'}
                                </span>
                                <span className="message-time">
                                    {new Date(msg.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                            <div className="message-content">{msg.content}</div>
                        </div>
                    ))}
                    {loading && <div className="message-loading">⟳ Thinking...</div>}
                    <div ref={messagesEndRef} />
                </div>

                {session.degraded && (
                    <div className="degraded-notice">
                        ⚠️ Chat in degraded mode (responses may be limited)
                    </div>
                )}

                {error && <div className="error-banner">{error}</div>}

                <div className="input-area">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                handleSend()
                            }
                        }}
                        placeholder={windowStatus.status === 'open' ? "Type a message... (Ctrl+Enter to send)" : "Chat window is closed"}
                        disabled={loading || windowStatus.status !== 'open'}
                        className="chat-input"
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading || windowStatus.status !== 'open'}
                        className="btn-primary"
                        title={windowStatus.status === 'open' ? 'Send message' : 'Open window first'}
                    >
                        {loading ? '⟳' : '↗'}
                    </button>
                </div>
            </div>

            <CoDevView />
        </div>
    )
}
