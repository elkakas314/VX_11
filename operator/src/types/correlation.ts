/**
 * Types for Event Correlation Graph
 * ===================================
 * Support for DAG visualization in Operator timeline
 */

export interface CorrelationNode {
    type: string;          // Event type (e.g., "system.alert")
    timestamp: number;     // Milliseconds
    severity?: string;     // L1-L4
    nature?: string;       // "incident", "meta", "forensic", etc.
}

export interface CorrelationEdge {
    source: string;        // Event ID
    target: string;        // Event ID
    strength: string;      // 0.0-1.0 (normalized correlation strength)
}

export interface CorrelationGraph {
    nodes: CorrelationNode[];
    edges: CorrelationEdge[];
    total_nodes: number;
    total_edges: number;
}

export interface CorrelationResponse {
    status: string;
    timestamp: number;
    graph: CorrelationGraph;
}

export interface EventNature {
    incident: "incident";
    meta: "meta";
    forensic: "forensic";
    decision: "decision";
    state: "state";
    narration: "narration";
}
