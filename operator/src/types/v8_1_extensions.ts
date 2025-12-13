/**
 * VX11 v8.1 Extensions — Type Definitions
 * Minimal, passive types for Timeline, System Tension, Hormiguero levels, etc.
 */

export enum HormigueroLevel {
    MACRO = "macro",
    MESO = "meso",
    MICRO = "micro",
}

export interface SystemTensionEvent {
    type: "switch.system_tension";
    value: number; // 0-100
    timestamp: number;
}

export interface TimelineEvent {
    id: string;
    timestamp: number;
    module: string; // "madre", "switch", "hermes", etc.
    severity: "critical" | "error" | "warning" | "info";
    message: string;
    context?: Record<string, unknown>;
}

export interface CorrelationUpdate {
    type: "system.correlation_update";
    nodes: Array<{ id: string; label: string; module: string }>;
    edges: Array<{ source: string; target: string; weight: number }>;
    timestamp: number;
}

export interface SnapshotRequest {
    timestamp: number;
}

export interface SnapshotResponse {
    type: "timeline.snapshot_ready";
    timestamp: number;
    state: {
        madre?: Record<string, unknown>;
        switch?: Record<string, unknown>;
        hormiguero?: Record<string, unknown>;
        [key: string]: unknown;
    };
}

export interface HormigueroAbstractionLevel {
    type: "hormiguero.abstraction_level";
    level: HormigueroLevel;
    data: Record<string, unknown>;
    timestamp: number;
}

export interface MadreExplanationStructured {
    type: "madre.explanation_structured";
    decision_tree: {
        decision: string;
        reasoning: string;
        path: Array<{ step: number; action: string }>;
    };
    alternatives: Array<{
        option: string;
        pros: string[];
        cons: string[];
        confidence: number;
    }>;
    confidence: number;
    timestamp: number;
}

export type VX11WebSocketEvent =
    | SystemTensionEvent
    | CorrelationUpdate
    | SnapshotResponse
    | HormigueroAbstractionLevel
    | MadreExplanationStructured
    | { type: "echo"; data: string }; // Fallback

export interface Bookmark {
    id: string;
    event_id: string;
    timestamp: number;
    label?: string;
    created_at: number;
}
