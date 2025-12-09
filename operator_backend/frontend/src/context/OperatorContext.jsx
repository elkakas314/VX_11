import React, { createContext, useState, useCallback } from 'react';

export const OperatorContext = createContext();

export const OperatorProvider = ({ children }) => {
    const [sessionId, setSessionId] = useState(localStorage.getItem('sessionId') || null);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

    const addMessage = useCallback((role, content, metadata = {}) => {
        const msg = {
            id: Date.now(),
            role,
            content,
            metadata,
            timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, msg]);
        return msg;
    }, []);

    const createSession = useCallback((newSessionId) => {
        setSessionId(newSessionId);
        localStorage.setItem('sessionId', newSessionId);
    }, []);

    const value = {
        sessionId,
        messages,
        loading,
        setLoading,
        addMessage,
        createSession,
    };

    return (
        <OperatorContext.Provider value={value}>
            {children}
        </OperatorContext.Provider>
    );
};

export const useOperator = () => {
    const ctx = React.useContext(OperatorContext);
    if (!ctx) throw new Error('useOperator must be used within OperatorProvider');
    return ctx;
};
