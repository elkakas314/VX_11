import { useEffect, useRef, useState } from 'react'
import { apiClient } from '../services/api'
import { renderMarkdown, extractCodeBlocks } from '../services/markdown'

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
}

export function ChatPanel() {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [sessionId] = useState(() => `session_${Date.now()}`)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async () => {
        if (!input.trim()) return

        // Add user message
        const userMsg: Message = {
            id: `msg_${Date.now()}`,
            role: 'user',
            content: input,
            timestamp: new Date(),
        }
        setMessages((prev) => [...prev, userMsg])
        setInput('')
        setLoading(true)
        setError(null)

        // Send to API
        const resp = await apiClient.chat(input, sessionId)
        setLoading(false)

        if (resp.ok) {
            const assistantMsg: Message = {
                id: `msg_${Date.now()}_resp`,
                role: 'assistant',
                content: resp.data?.response || JSON.stringify(resp.data),
                timestamp: new Date(),
            }
            setMessages((prev) => [...prev, assistantMsg])
        } else {
            setError(resp.error || 'Failed to send message')
            // Add error message to chat
            const errorMsg: Message = {
                id: `msg_${Date.now()}_error`,
                role: 'assistant',
                content: `[ERROR] ${resp.error}`,
                timestamp: new Date(),
            }
            setMessages((prev) => [...prev, errorMsg])
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="card chat-panel">
            <div className="card-header">
                <h2>Chat (Session: {sessionId.slice(0, 20)}...)</h2>
            </div>

            <div className="chat-messages">
                {messages.length === 0 && (
                    <div className="empty-state">
                        <p>No messages yet. Send a message to get started.</p>
                    </div>
                )}

                {messages.map((msg) => {
                    const codeBlocks = extractCodeBlocks(msg.content)
                    const hasCode = codeBlocks.length > 0

                    return (
                        <div key={msg.id} className={`message message-${msg.role}`}>
                            <div className="message-meta">
                                <span className="message-role">
                                    {msg.role === 'user' ? '👤' : '🤖'} {msg.role}
                                </span>
                                <span className="message-time">{msg.timestamp.toLocaleTimeString()}</span>
                            </div>
                            <div
                                className="message-content"
                                dangerouslySetInnerHTML={renderMarkdown(msg.content)}
                            />
                            {hasCode && codeBlocks.map((block, idx) => (
                                <div key={idx} className="code-block-wrapper">
                                    <div className="code-block-header">
                                        <span className="code-lang">{block.language || 'code'}</span>
                                        <button
                                            className="btn-copy-code"
                                            onClick={() => navigator.clipboard.writeText(block.code)}
                                            title="Copy code"
                                        >
                                            📋
                                        </button>
                                    </div>
                                    <pre><code>{block.code}</code></pre>
                                </div>
                            ))}
                        </div>
                    )
                })}

                {loading && (
                    <div className="message message-loading">
                        <span>⟳ Waiting for response...</span>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {error && (
                <div className="error-box">
                    <span>⚠</span> {error}
                </div>
            )}

            <div className="chat-input">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type a message (Shift+Enter for new line, Enter to send)"
                    disabled={loading}
                    rows={3}
                />
                <button onClick={handleSend} disabled={loading || !input.trim()} className="btn-primary">
                    {loading ? '⟳' : '→'} Send
                </button>
            </div>
        </div>
    )
}
