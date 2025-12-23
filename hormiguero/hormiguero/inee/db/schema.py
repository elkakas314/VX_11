"""
INEE DB Schema (additive-only).

Tables:
- inee_colonies: Remote colony registration
- inee_agents: Agents within colonies
- inee_intents: Intent history (remote -> VX11)
- inee_pheromones: Async signals/messages
- inee_audit_events: Audit trail
"""

INEE_SCHEMA_SQL = """
-- Tabla: inee_colonies
CREATE TABLE IF NOT EXISTS inee_colonies (
    colony_id TEXT PRIMARY KEY,
    remote_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, active, failed, disabled
    last_heartbeat TEXT,
    agent_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Tabla: inee_agents
CREATE TABLE IF NOT EXISTS inee_agents (
    agent_id TEXT PRIMARY KEY,
    colony_id TEXT NOT NULL,
    agent_type TEXT NOT NULL,  -- scanner, planner, executor, etc
    status TEXT NOT NULL DEFAULT 'idle',  -- idle, working, failed
    last_seen TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(colony_id) REFERENCES inee_colonies(colony_id)
);

-- Tabla: inee_intents
CREATE TABLE IF NOT EXISTS inee_intents (
    intent_id TEXT PRIMARY KEY,
    correlation_id TEXT,
    source TEXT NOT NULL,  -- "inee" or similar
    operation TEXT NOT NULL,  -- scan, notify_incident, propose_action
    remote_colony_id TEXT,
    context_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(remote_colony_id) REFERENCES inee_colonies(colony_id)
);

-- Tabla: inee_pheromones
CREATE TABLE IF NOT EXISTS inee_pheromones (
    pheromone_id TEXT PRIMARY KEY,
    colony_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,  -- pressure, alert, coordination
    payload_json TEXT,
    ttl_seconds INTEGER DEFAULT 300,
    created_at TEXT NOT NULL,
    FOREIGN KEY(colony_id) REFERENCES inee_colonies(colony_id)
);

-- Tabla: inee_audit_events
CREATE TABLE IF NOT EXISTS inee_audit_events (
    event_id TEXT PRIMARY KEY,
    component TEXT NOT NULL,  -- "inee_registry", "inee_router", etc
    event_type TEXT NOT NULL,  -- "colony_registered", "intent_submitted", etc
    detail_json TEXT,
    created_at TEXT NOT NULL
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_inee_colonies_status ON inee_colonies(status);
CREATE INDEX IF NOT EXISTS idx_inee_agents_colony_id ON inee_agents(colony_id);
CREATE INDEX IF NOT EXISTS idx_inee_agents_status ON inee_agents(status);
CREATE INDEX IF NOT EXISTS idx_inee_intents_source ON inee_intents(source);
CREATE INDEX IF NOT EXISTS idx_inee_intents_colony_id ON inee_intents(remote_colony_id);
CREATE INDEX IF NOT EXISTS idx_inee_pheromones_colony_id ON inee_pheromones(colony_id);
CREATE INDEX IF NOT EXISTS idx_inee_pheromones_signal ON inee_pheromones(signal_type);
"""
