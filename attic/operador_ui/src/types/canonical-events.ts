/**
 * Eventos canónicos de VX11 (Whitelist v8.1 FINAL)
 * Solo 6 eventos permitidos según arquitectura canonical
 */

export type EventType =
    | "system.alert"
    | "system.correlation.updated"
    | "forensic.snapshot.created"
    | "madre.decision.explained"
    | "switch.tension.updated"
    | "shub.action.narrated";

export type SeverityLevel = "L1" | "L2" | "L3" | "L4";

// ============ system.alert ============
export interface SystemAlertEvent {
    type: "system.alert";
    alert_id: string;
    severity: SeverityLevel;
    message: string;
    component?: string;
    timestamp: number;
    metadata?: Record<string, unknown>;
}

// ============ system.correlation.updated ============
export interface CorrelationNode {
    id: string;
    label: string;
    type: "task" | "decision" | "event" | "resource";
}

export interface SystemCorrelationEvent {
    type: "system.correlation.updated";
    correlation_id: string;
    nodes: CorrelationNode[];
    edges: Array<{ source: string; target: string }>;
    summary: string;
    timestamp: number;
}

// ============ forensic.snapshot.created ============
export interface ForensicSnapshot {
    type: "forensic.snapshot.created";
    snapshot_id: string;
    module: string;
    hash: string;
    timestamp: number;
    details?: Record<string, unknown>;
}

// ============ madre.decision.explained ============
export interface MadreDecision {
    type: "madre.decision.explained";
    decision_id: string;
    action: string;
    rationale: string;
    confidence: number;
    timestamp: number;
    affected_modules?: string[];
}

// ============ switch.tension.updated ============
export interface SwitchTension {
    type: "switch.tension.updated";
    tension_id: string;
    model_name: string;
    score: number; // 0-1
    reason: string;
    timestamp: number;
}

// ============ shub.action.narrated ============
export interface ShubNarrative {
    type: "shub.action.narrated";
    narrative_id: string;
    action: string;
    narrative_text: string;
    audio_domain?: string;
    timestamp: number;
}

// Union de todos los eventos canónicos
export type CanonicalEvent =
    | SystemAlertEvent
    | SystemCorrelationEvent
    | ForensicSnapshot
    | MadreDecision
    | SwitchTension
    | ShubNarrative;

// Helper para validar tipo de evento
export function isCanonicalEvent(event: any): event is CanonicalEvent {
    const validTypes: EventType[] = [
        "system.alert",
        "system.correlation.updated",
        "forensic.snapshot.created",
        "madre.decision.explained",
        "switch.tension.updated",
        "shub.action.narrated",
    ];
    return validTypes.includes(event?.type);
}
