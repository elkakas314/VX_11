import { useEffect, useRef, useState } from 'react'
import { apiClient } from '../services/api'

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

export function ChatView() {
    const [session, setSession] = useState<SessionData>({
        id: `session_${Date.now()}`,
        messages: [],
    })
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [session.messages])

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

    return (
        <div className="chat-view">
            <h2>Chat</h2>

            <div className="chat-container">
                <div className="messages">
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
                        placeholder="Type a message... (Ctrl+Enter to send)"
                        disabled={loading}
                        className="chat-input"
                    />
                    <button onClick={handleSend} disabled={loading} className="btn-primary">
                        {loading ? '⟳' : '↗'}
                    </button>
                </div>
            </div>
        </div>
    )
}
