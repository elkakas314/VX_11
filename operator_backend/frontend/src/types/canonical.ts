/**
 * Canonical types for VX11 Operator Frontend
 * Used by all canonical tabs and API calls
 */

export interface AuthToken {
    access_token: string;
    token_type: string;
    user_id?: string;
    expires_in?: number;
}

export interface OperatorStatus {
    status: "operational" | "degraded" | "offline";
    mode: "low_power" | "operative_core";
    uptime_seconds: number;
    modules: {
        [key: string]: {
            status: "active" | "inactive" | "error";
            heartbeat_ms?: number;
        };
    };
    timestamp: string;
}

export interface OperatorModule {
    name: string;
    status: "active" | "inactive" | "error";
    version?: string;
    description?: string;
}

export interface AuditLog {
    id: string;
    timestamp: string;
    level: "INFO" | "WARNING" | "ERROR";
    source: string;
    message: string;
    metadata?: Record<string, any>;
}

export interface OperatorJob {
    id: string;
    intent: string;
    status: "pending" | "running" | "completed" | "failed";
    progress?: number;
    created_at: string;
    updated_at: string;
    result?: any;
}

export interface SystemEvent {
    id: string;
    timestamp: string;
    source: string;
    type: string;
    data: Record<string, any>;
}

export interface ChatMessage {
    role: "user" | "assistant";
    content: string;
    timestamp?: string;
}

export interface ChatRequest {
    message: string;
    mode?: string;
    metadata?: Record<string, any>;
}

export interface ChatResponse {
    id: string;
    response: string;
    mode: string;
    metadata?: Record<string, any>;
}

export type TabName = "dashboard" | "chat" | "modules" | "jobs" | "events" | "audit";

export interface ErrorResponse {
    detail?: string;
    status?: number;
    error?: string;
}
