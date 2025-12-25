import { useState, useRef, useEffect } from 'react'
import { useSessionStore, ChatMessage } from '../context/SessionContext'

interface ChatPanelProps {
    sessionId: string
}

export function ChatPanel({ sessionId }: ChatPanelProps) {
    const { sessions, addMessage } = useSessionStore()
    const session = sessions.find(s => s.id === sessionId)
    const messages = session?.messages || []

    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSend = async () => {
        if (!input.trim() || !sessionId) return

        const userMessage: ChatMessage = {
            id: `msg_${Date.now()}`,
            role: 'user',
            content: input,
            timestamp: new Date().toISOString(),
        }

        addMessage(sessionId, userMessage)
        setInput('')
        setLoading(true)

        // Simulate AI response
        setTimeout(() => {
            const aiMessage: ChatMessage = {
                id: `msg_${Date.now() + 1}`,
                role: 'assistant',
                content: `I received: "${input}". Real AI coming soon via tentáculo_link.`,
                module: 'madre',
                timestamp: new Date().toISOString(),
            }
            addMessage(sessionId, aiMessage)
            setLoading(false)
        }, 1000)
    }

    return (
        <div className="flex flex-col h-full">
            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map(msg => (
                    <div
                        key={msg.id}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${msg.role === 'user'
                                ? 'bg-purple-600 text-white'
                                : 'bg-gray-800 text-gray-100 border border-gray-700'
                                }`}
                        >
                            <p className="text-sm">{msg.content}</p>
                            {msg.module && (
                                <div className="text-xs text-gray-400 mt-1">@{msg.module}</div>
                            )}
                            <div className="text-xs text-gray-500 mt-1 opacity-70">
                                {new Date(msg.timestamp).toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-800 border border-gray-700 px-4 py-2 rounded-lg">
                            <div className="flex gap-2">
                                <div className="w-2 h-2 bg-purple-500 rounded-full typing-dot-1"></div>
                                <div className="w-2 h-2 bg-purple-500 rounded-full typing-dot-2"></div>
                                <div className="w-2 h-2 bg-purple-500 rounded-full typing-dot-3"></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={scrollRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-700 p-4">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Type your message..."
                        className="flex-1 bg-slate-800 text-gray-100 px-4 py-2 rounded-lg border border-gray-700 focus:border-purple-500 outline-none"
                    />
                    <button
                        onClick={handleSend}
                        disabled={loading}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg transition-colors"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    )
}
