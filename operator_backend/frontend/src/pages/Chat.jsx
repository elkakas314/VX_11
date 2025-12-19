import React, { useState, useRef, useEffect } from 'react';
import { operatorApi } from '../api/operatorClient';
import { useOperator } from '../context/OperatorContext';
import './Chat.css';

export const Chat = () => {
    const { sessionId, createSession, messages, addMessage, loading, setLoading } = useOperator();
    const [input, setInput] = useState('');
    const [sessionMessages, setSessionMessages] = useState([]);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        if (sessionId) {
            fetchSessionMessages();
        }
    }, [sessionId]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [sessionMessages]);

    const fetchSessionMessages = async () => {
        try {
            const res = await operatorApi.getSession(sessionId);
            if (res.data.status === 'service_offline') {
                setSessionMessages((prev) => [
                    ...prev,
                    { role: 'assistant', content: 'service_offline', timestamp: new Date().toISOString() },
                ]);
                return;
            }
            setSessionMessages(res.data.messages || []);
        } catch (err) {
            console.error('Failed to fetch session:', err);
        }
    };

    const handleSend = async () => {
        if (!input.trim()) return;

        try {
            setLoading(true);
            let sid = sessionId;

            if (!sid) {
                sid = 'session_' + Date.now();
                createSession(sid);
            }

            // Send message
            const res = await operatorApi.postChat(sid, input);
            if (res.data.status === 'service_offline') {
                setSessionMessages((prev) => [
                    ...prev,
                    { role: 'user', content: input, timestamp: new Date().toISOString() },
                    { role: 'assistant', content: 'service_offline', timestamp: new Date().toISOString() },
                ]);
                setInput('');
                return;
            }

            // Update session ID if new
            if (res.data.session_id) {
                createSession(res.data.session_id);
            }

            // Add messages locally
            setSessionMessages((prev) => [
                ...prev,
                { role: 'user', content: input, timestamp: new Date().toISOString() },
                { role: 'assistant', content: res.data.response, timestamp: new Date().toISOString() },
            ]);

            setInput('');
            await fetchSessionMessages();
        } catch (err) {
            console.error('Failed to send message:', err);
            alert('Error sending message: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-container">
            <h2>Chat</h2>

            {sessionId && <p className="session-id">Session: {sessionId}</p>}

            <div className="messages-area">
                {sessionMessages.map((msg, idx) => (
                    <div key={idx} className={`message ${msg.role}`}>
                        <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
                        <p>{msg.content}</p>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                    placeholder="Type your message... (Shift+Enter for newline)"
                    disabled={loading}
                    rows="3"
                />
                <button
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    className="send-btn"
                >
                    {loading ? 'Sending...' : 'Send'}
                </button>
            </div>
        </div>
    );
};
