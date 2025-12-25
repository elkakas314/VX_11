/**
 * Chat and messaging types
 * Defines structures for chat messages, responses, and conversation history
 */

import { UUID, Timestamp, ServiceName } from './index'

export type MessageRole = 'user' | 'ai' | 'system'

export interface Message {
    id: UUID
    role: MessageRole
    content: string
    module?: ServiceName        // Which module responded (if AI)
    routing?: ServiceName[]     // Modules used in routing
    metadata?: {
        tokens_input?: number
        tokens_output?: number
        latency_ms?: number
        model?: string
        engine?: string
    }
    timestamp: Timestamp
}

export interface ChatRequest {
    message: string
    mode?: 'default' | 'analyze' | 'reasoning'
    context?: string           // Optional session context
    session_id?: UUID
}

export interface ChatResponse {
    id: UUID
    response: string
    module: ServiceName
    routing: ServiceName[]
    latency_ms: number
    tokens: {
        input: number
        output: number
        total: number
    }
    model?: string
    engine?: string
    timestamp: Timestamp
    metadata?: Record<string, any>
}

export interface ChatHistory {
    id: UUID
    messages: Message[]
    created_at: Timestamp
    updated_at: Timestamp
    title?: string
    session_id?: UUID
}

export interface ChatMessage {
    id: UUID
    role: 'user' | 'ai' | 'system'
    text: string
    module?: ServiceName
    routing?: ServiceName[]
    timestamp: Timestamp
    latency_ms?: number
    tokens?: {
        input: number
        output: number
    }
    engine?: string
}

// Chat streaming response
export interface ChatStreamEvent {
    type: 'start' | 'chunk' | 'end' | 'error'
    content?: string
    module?: ServiceName
    latency_ms?: number
    error?: string
    timestamp: Timestamp
}
