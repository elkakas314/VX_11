/**
 * VX11 v8.1 Extensions — Type Definitions
 * Canonical event types aligned with VX11 Operator v8.0
 * 
 * WHITELIST CANÓNICO (7 eventos permitidos en Operator):
 * 1. system.alert
 * 2. system.correlation.updated
 * 3. system.state.summary
 * 4. forensic.snapshot.created
 * 5. madre.decision.explained
 * 6. switch.system.tension
 * 7. shub.action.narrated
 */

export type CanonicalEventType =
    | "system.alert"
    | "system.correlation.updated"
    | "system.state.summary"
    | "forensic.snapshot.created"
    | "madre.decision.explained"
    | "switch.system.tension"
    | "shub.action.narrated";

/**
 * Base canonical event structure.
 * All events must conform to: <module>.<action>.<result> (past tense)
 */
export interface CanonicalEvent {
    type: CanonicalEventType;
    timestamp: number;
    severity?: "critical" | "error" | "warning" | "info";
    data?: Record<string, unknown>;
}

// Specific event interfaces below

export interface SystemAlertEvent extends CanonicalEvent {
    type: "system.alert";
    severity: "critical" | "error" | "warning" | "info";
    message: string;
    source: string; // module that raised alert
}

export interface SystemCorrelationUpdatedEvent extends CanonicalEvent {
    type: "system.correlation.updated";
    data: {
        nodes: Array<{ id: string; label: string; module: string }>;
        edges: Array<{ source: string; target: string; weight: number }>;
    };
}

export interface SystemStateSummaryEvent extends CanonicalEvent {
    type: "system.state.summary";
    data: {
        madre: { status: string };
        switch: { routing: string };
        hormiguero: { queen_alive: boolean; ant_count: number };
        [key: string]: unknown;
    };
}

export interface ForensicSnapshotCreatedEvent extends CanonicalEvent {
    type: "forensic.snapshot.created";
    data: {
        snapshot_id: string;
        timestamp: number;
        state: Record<string, unknown>;
    };
}

export interface MadreDecisionExplainedEvent extends CanonicalEvent {
    type: "madre.decision.explained";
    data: {
        decision: string;
        reasoning: string;
        path: Array<{ step: number; action: string }>;
        alternatives: Array<{
            option: string;
            pros: string[];
            cons: string[];
            confidence: number;
        }>;
        confidence: number;
    };
}

export interface SwitchSystemTensionEvent extends CanonicalEvent {
    type: "switch.system.tension";
    data: {
        value: number; // 0-100
        components: Record<string, number>; // per-component tension
    };
}

export interface ShubActionNarratedEvent extends CanonicalEvent {
    type: "shub.action.narrated";
    data: {
        action: string;
        narrative: string; // human-readable explanation
        audio_url?: string;
    };
}

/**
 * Union of all canonical events allowed in Operator.
 * Only these 7 types can be received via WebSocket.
 */
export type VX11CanonicalEvent =
    | SystemAlertEvent
    | SystemCorrelationUpdatedEvent
    | SystemStateSummaryEvent
    | ForensicSnapshotCreatedEvent
    | MadreDecisionExplainedEvent
    | SwitchSystemTensionEvent
    | ShubActionNarratedEvent;

/**
 * Bookmark interface for local timeline markers (no backend required).
 */
export interface Bookmark {
    id: string;
    event_id: string;
    timestamp: number;
    label?: string;
    created_at: number;
}
