/**
 * Global type definitions for VX11 Operator Frontend
 * Type-safe definitions for all VX11 system entities
 */

export type ServiceName =
    | 'madre'
    | 'switch'
    | 'hermes'
    | 'shub'
    | 'spawner'
    | 'hormiguero'
    | 'tentaculo_link'
    | 'shubniggurath'
    | 'manifestator'
    | 'mcp'

export type ModuleStatus = 'up' | 'down' | 'idle' | 'loading' | 'error' | 'unknown'

export type PowerMode = 'solo_madre' | 'operative_core' | 'full'

export type ChatMode = 'default' | 'analyze' | 'reasoning'

export type ErrorLevel = 'info' | 'debug' | 'warning' | 'error' | 'critical'

// API Response wrapper
export interface ApiResponse<T = any> {
    success: boolean
    data?: T
    error?: {
        code: string
        message: string
        detail?: string
        timestamp?: string
    }
    timestamp: string
}

// Generic error response
export interface ApiError {
    error: string
    detail?: string
    status?: number
    timestamp?: string
}

// Timestamps & IDs
export type Timestamp = string // ISO 8601
export type UUID = string

export interface Identifiable {
    id: UUID
    created_at: Timestamp
    updated_at: Timestamp
}

export interface Timestamped {
    timestamp: Timestamp
}

// API State management
export interface ApiState<T> {
    data: T | null
    loading: boolean
    error: string | null
    isRetrying?: boolean
    lastUpdated?: Timestamp
}

// Logging
export interface LogEntry extends Timestamped {
    level: ErrorLevel
    module: ServiceName
    message: string
    details?: Record<string, any>
    request_id?: string
}
// Health & Status
export interface HealthStatus {
    status: 'ok' | 'degraded' | 'down'
    timestamp: Timestamp
    latency_ms?: number
    details?: Record<string, any>
}

export type ServiceHealth = {
    [key in ServiceName]?: HealthStatus
}

// Power Control
export interface PowerPolicy {
    policy_active: PowerMode
    running_services: ServiceName[]
    timestamp: Timestamp
}

export interface PowerCommand {
    service: ServiceName
    action: 'start' | 'stop' | 'restart'
}

export interface PowerResponse {
    success: boolean
    service: ServiceName
    action: string
    timestamp: Timestamp
    details?: string
}

// Chat & Messages
export interface ChatMessage extends Identifiable {
    role: 'user' | 'assistant' | 'system'
    content: string
    module?: ServiceName
    metadata?: Record<string, any>
    session_id?: UUID
}

export interface ChatSession extends Identifiable {
    name: string
    messages: ChatMessage[]
    mode: ChatMode
}

// Audit
export interface AuditEntry extends Identifiable {
    action: string
    resource: string
    user?: string
    details?: Record<string, any>
    status: 'success' | 'failure'
}