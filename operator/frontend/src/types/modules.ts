import { ModuleStatus, ServiceName, Timestamp, PowerMode } from './index'

export interface ModuleStatusInfo {
    name: ServiceName
    status: ModuleStatus
    uptime?: string
    cpu: number
    ram: string
    memory_percent: number
    port?: number
    version?: string
    last_activity?: Timestamp
    error_count?: number
    health_status?: 'ok' | 'degraded' | 'error'
}

// Aggregated system status
export interface SystemStatus {
    mode: PowerMode
    modules: ModuleStatusInfo[]
    ia_engines: {
        active: number
        models: string[]
        avg_latency_ms: number
        tokens_today: string
    }
    memory_usage: {
        total_gb: number
        used_gb: number
        percent: number
    }
    uptime: string
    database_status?: {
        size_mb: number
        integrity: 'ok' | 'error'
    }
}

// Power control
export interface PowerStatus {
    policy_active: boolean
    running_services: ServiceName[]
    mode: PowerMode
    timestamp?: Timestamp
}

export interface ServiceControlRequest {
    service: ServiceName
}

export interface ServiceControlResponse {
    service: ServiceName
    action: 'start' | 'stop'
    status: 'starting' | 'stopping' | 'started' | 'stopped' | 'error'
    timestamp: Timestamp
    error?: string
    message?: string
}

export interface PowerPolicyRequest {
    policy: PowerMode
    apply: boolean
}

export interface PowerPolicyResponse {
    policy: string
    active: boolean
    running_services: ServiceName[]
    affected_services: ServiceName[]
    timestamp: Timestamp
}

// Health check response
export interface HealthResponse {
    status: 'ok' | 'degraded' | 'error' | 'unknown'
    version: string
    timestamp: Timestamp
    services?: {
        [key: string]: 'up' | 'down' | 'unknown'
    }
    uptime_seconds?: number
}

// Dashboard metrics
export interface DashboardMetrics {
    system_status: SystemStatus
    health: HealthResponse
    power: PowerStatus
    last_error?: string
}
