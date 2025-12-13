/**
 * Hormiguero Canonical Types
 * Defines the data model for Queen, Ants, Incidents, and Pheromones
 * Reference: docs/VX11_HORMIGUERO_v7_COMPLETION.md
 */

export enum AntRole {
    SCANNER_DRIFT = "scanner_drift",
    SCANNER_MEMORY = "scanner_memory",
    SCANNER_IMPORTS = "scanner_imports",
    SCANNER_LOGS = "scanner_logs",
    SCANNER_DB = "scanner_db",
    SCANNER_MODULES = "scanner_modules",
    SCANNER_PROCESSES = "scanner_processes",
    SCANNER_PORTS = "scanner_ports",
}

export enum SeverityLevel {
    INFO = "info",
    WARNING = "warning",
    ERROR = "error",
    CRITICAL = "critical",
}

export enum IncidentType {
    DRIFT = "drift",
    MEMORY_LEAK = "memory_leak",
    BROKEN_IMPORT = "broken_import",
    ORPHAN_LOG = "orphan_log",
    ORPHAN_DB = "orphan_db",
    ORPHAN_MODULE = "orphan_module",
    ZOMBIE_PROCESS = "zombie_process",
    BLOCKED_PORT = "blocked_port",
}

export enum PheromoneType {
    ALERT = "alert",
    TASK = "task",
    CLEANUP = "cleanup",
    OPTIMIZE = "optimize",
    INVESTIGATE = "investigate",
}

export enum IncidentStatus {
    OPEN = "open",
    ACKNOWLEDGED = "acknowledged",
    RESOLVED = "resolved",
}

export enum AntStatus {
    IDLE = "idle",
    SCANNING = "scanning",
    REPORTING = "reporting",
}

export enum DecisionRoute {
    SPAWN_HIJA = "spawn_hija",
    SWITCH_STRATEGY = "switch_strategy",
    DIRECT_ACTION = "direct_action",
}

// ===== Core Data Types =====

export interface Ant {
    id: string;
    role: AntRole;
    status: AntStatus;
    last_scan_at: string | null;
    mutation_level: number;
    cpu_percent: number;
    ram_percent: number;
    created_at: string;
    updated_at: string;
}

export interface Incident {
    id: number;
    ant_id: string;
    incident_type: IncidentType;
    severity: SeverityLevel;
    location: string;
    details: Record<string, unknown>;
    status: IncidentStatus;
    detected_at: string;
    resolved_at: string | null;
    queen_decision: DecisionRoute | null;
}

export interface Pheromone {
    id: number;
    pheromone_type: PheromoneType;
    intensity: number; // 1-10
    source_incident_ids: number[];
    madre_intent_id: string | null;
    switch_consultation_id: string | null;
    payload: Record<string, unknown>;
    created_at: string;
    executed_at: string | null;
}

export interface QueenStatus {
    queen: {
        status: AntStatus;
        last_decision_at: string | null;
        pending_incidents: number;
        total_decisions: number;
    };
    ants: Ant[];
}

export interface HormiguerReport {
    count: number;
    incidents: Incident[];
    summary: {
        by_severity: Record<SeverityLevel, number>;
        by_type: Record<IncidentType, number>;
        by_status: Record<IncidentStatus, number>;
    };
}

// ===== UI State Types =====

export interface HormiguerUIState {
    queen: Ant | null;
    ants: Ant[];
    incidents: Incident[];
    pheromones: Pheromone[];
    selected_incident_id: number | null;
    selected_ant_id: string | null;
    is_scanning: boolean;
    error: string | null;
}

export interface GraphNode {
    id: string;
    data: {
        label: string;
        role?: AntRole;
        status?: AntStatus | SeverityLevel;
        incident_count?: number;
    };
    position: { x: number; y: number };
    type: "queen" | "ant" | "incident";
}

export interface GraphEdge {
    id: string;
    source: string;
    target: string;
    data: {
        pheromone_type?: PheromoneType;
        intensity?: number;
        incident_id?: number;
    };
    animated?: boolean;
}
