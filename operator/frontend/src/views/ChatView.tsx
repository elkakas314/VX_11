import { useEffect, useRef, useState } from 'react'
import { apiClient } from '../services/api'
import { useWindowStatusStore } from '../stores'
import { CoDevView } from './CoDevView'

interface ChatMessage {
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp: number
    meta?: {
        correlation_id?: string
        source?: string
    }
}

interface SessionData {
    id: string
    messages: ChatMessage[]
    degraded?: boolean
}

export function ChatView() {
    const [session, setSession] = useState<SessionData>({
        id: `session_${Date.now()}`,
        messages: [],
    })
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const { windowStatus, setWindowStatus } = useWindowStatusStore()
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [session.messages])

    useEffect(() => {
        const loadWindowStatus = async () => {
            try {
                const resp = await apiClient.windows()
                if (resp.ok && resp.data) {
                    setWindowStatus(resp.data)
                }
            } catch {
                // Silent fail, status is informational
            }
        }

        if (!windowStatus) {
            loadWindowStatus()
        }
    }, [windowStatus, setWindowStatus])

    async function handleSend() {
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
                    meta: {
                        correlation_id: resp.data.correlation_id,
                        source: resp.data.fallback_source || resp.data.provider_used,
                    },
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
            const retryHint =
                err?.retryAfterMs || err?.retry_after_ms
                    ? ` Retry in ${Math.round((err.retryAfterMs || err.retry_after_ms) / 1000)}s.`
                    : ''
            setError(`${err.message || 'Failed to send message'}${retryHint}`)

            const errorMsg: ChatMessage = {
                id: `msg_${Date.now()}`,
                role: 'system',
                content: `Error: ${err.message || 'Failed to send message'}`,
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

    async function handleOpenWindow() {
        setLoading(true)
        setError(null)
        try {
            const resp = await apiClient.chatWindowOpen(['switch', 'hermes'])
            if (resp.ok && resp.data) {
                setWindowStatus(resp.data)
                setError(null)
            } else {
                // OFF_BY_POLICY is not an error, it's expected in some modes
                if (resp.data?.status === 'OFF_BY_POLICY') {
                    setError(`Window gated: ${resp.data?.message || 'solo_madre policy active'}`)
                } else {
                    setError(resp.error || 'Failed to open window')
                }
            }
        } catch (err: any) {
            setError(err.message || 'Failed to open window')
        } finally {
            setLoading(false)
        }
    }

    async function handleCloseWindow() {
        setLoading(true)
        setError(null)
        try {
            const resp = await apiClient.chatWindowClose()
            if (resp.ok && resp.data) {
                setWindowStatus(resp.data)
                setError(null)
            } else {
                setError(resp.error || 'Failed to close window')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to close window')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="chat-view">
            <div className="chat-header">
                <h2>Chat</h2>
                <div className="window-status-badge">
                    <span
                        className={
                            windowStatus?.mode === 'window_active' ? 'badge-open' : 'badge-closed'
                        }
                    >
                        {windowStatus?.mode === 'window_active' ? '✓ window_active' : '⊘ solo_madre'}
                    </span>
                    <span className="countdown">Observer mode: windows controlled by Madre.</span>
                </div>
                <div className="window-controls">
                    {windowStatus?.mode !== 'window_active' && (
                        <button
                            onClick={handleOpenWindow}
                            disabled={loading}
                            className="btn-secondary"
                            title="Open chat window (enables Switch/LLM)"
                        >
                            {loading ? '⟳' : '↑'} Open Window
                        </button>
                    )}
                    {windowStatus?.mode === 'window_active' && (
                        <button
                            onClick={handleCloseWindow}
                            disabled={loading}
                            className="btn-secondary"
                            title="Close chat window"
                        >
                            {loading ? '⟳' : '↓'} Close Window
                        </button>
                    )}
                </div>
            </div>

            <div className="chat-container">
                <div className="messages">
                    {session.messages.length === 0 && (
                        <div className="message-empty">
                            <p>💬 Send a message to route through Tentáculo → Switch.</p>
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
                                {msg.meta?.correlation_id && (
                                    <span className="message-meta">
                                        {msg.meta.correlation_id.slice(0, 8)}
                                    </span>
                                )}
                                {msg.meta?.source && (
                                    <span className="message-meta">[{msg.meta.source}]</span>
                                )}
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
                        placeholder="Type a message... (Ctrl+Enter to send)"
                        disabled={loading}
                        className="chat-input"
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading}
                        className="btn-primary"
                        title="Send message"
                    >
                        {loading ? '⟳' : '↗'}
                    </button>
                </div>
            </div>

            <CoDevView />
        </div>
    )
}
