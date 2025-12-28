"""
INEE + Extended Hormiguero DB Bootstrap
SQLite schema: inee_*, colony_*, builder_*, reward_*
Used by hormiguero/core/db/sqlite.py: ensure_schema()
Only creates if NOT EXISTS (idempotent).
"""

DB_SCHEMA_INEE_EXTENDED = """

-- ============ INEE TABLES ============
-- Internal NEuroBehavioral EnginE state

CREATE TABLE IF NOT EXISTS inee_colonies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colony_id TEXT UNIQUE NOT NULL,
    remote_url TEXT,
    status TEXT DEFAULT 'registered',  -- registered|active|dormant|dead
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS inee_agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT UNIQUE NOT NULL,
    colony_id TEXT NOT NULL,
    agent_type TEXT,  -- queen|worker|scout|builder
    status TEXT DEFAULT 'idle',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(colony_id) REFERENCES inee_colonies(colony_id)
);

CREATE TABLE IF NOT EXISTS inee_intents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_id TEXT UNIQUE NOT NULL,
    intent_type TEXT NOT NULL,  -- diagnose|propose|apply
    correlation_id TEXT,
    remote_colony_id TEXT,
    payload JSON,
    status TEXT DEFAULT 'pending',  -- pending|processing|approved|rejected|executed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    result JSON
);

CREATE TABLE IF NOT EXISTS inee_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    component TEXT NOT NULL,  -- inee|colony|builder|reward
    event_type TEXT,  -- register|submit|approve|reject|execute
    correlation_id TEXT,
    details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============ COLONY TABLES ============
-- Remote colony lifecycle: egg -> larva -> adult

CREATE TABLE IF NOT EXISTS colony_eggs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    egg_id TEXT UNIQUE NOT NULL,
    remote_colony_id TEXT NOT NULL,
    envelope_nonce TEXT UNIQUE,  -- For replay protection
    payload JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

CREATE TABLE IF NOT EXISTS colony_lifecycle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colony_id TEXT UNIQUE NOT NULL,
    state TEXT DEFAULT 'egg',  -- egg|larva|adult
    state_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    heartbeat_at DATETIME,
    ack_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    metadata JSON
);

CREATE TABLE IF NOT EXISTS colony_envelopes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    envelope_id TEXT UNIQUE NOT NULL,
    colony_id TEXT NOT NULL,
    nonce TEXT UNIQUE NOT NULL,
    hmac_signature TEXT NOT NULL,
    payload_json TEXT,
    replay_rejected BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(colony_id) REFERENCES colony_lifecycle(colony_id)
);

-- ============ BUILDER TABLES ============
-- Patchset generation (NO execution, only INTENT creation)

CREATE TABLE IF NOT EXISTS builder_specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spec_id TEXT UNIQUE NOT NULL,
    module_name TEXT,
    patch_type TEXT,  -- code|config|schema|diagnostic
    description TEXT,
    parameters JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS builder_patchsets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patchset_id TEXT UNIQUE NOT NULL,
    builder_spec_id TEXT NOT NULL,
    intent_id TEXT,  -- Foreign key to inee_intents for audit
    changes_json TEXT,
    status TEXT DEFAULT 'generated',  -- generated|pending_approval|approved|rejected|applied
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(builder_spec_id) REFERENCES builder_specs(spec_id),
    FOREIGN KEY(intent_id) REFERENCES inee_intents(intent_id)
);

CREATE TABLE IF NOT EXISTS builder_prompt_packs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pack_id TEXT UNIQUE NOT NULL,
    patchset_id TEXT,
    prompts_json TEXT,
    context_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patchset_id) REFERENCES builder_patchsets(patchset_id)
);

-- ============ REWARD TABLES ============
-- Internal economy for scheduling/priority (no real money)

CREATE TABLE IF NOT EXISTS reward_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT UNIQUE NOT NULL,  -- agent_id or colony_id
    account_type TEXT,  -- agent|colony|service
    balance_points INTEGER DEFAULT 0,
    rank TEXT DEFAULT 'novice',  -- novice|skilled|expert|master
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reward_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    account_id TEXT NOT NULL,
    amount_points INTEGER,
    reason TEXT,  -- task_completed|bugfix|optimization|exploration
    related_intent_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES reward_accounts(account_id),
    FOREIGN KEY(related_intent_id) REFERENCES inee_intents(intent_id)
);

CREATE TABLE IF NOT EXISTS reward_scoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scoring_id TEXT UNIQUE NOT NULL,
    account_id TEXT NOT NULL,
    task_complexity INTEGER,  -- 1-10
    success_rate REAL,  -- 0.0-1.0
    speed_multiplier REAL,
    points_earned INTEGER,
    scoring_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES reward_accounts(account_id)
);

-- ============ INDICES (for common queries) ============

CREATE INDEX IF NOT EXISTS idx_inee_colonies_status ON inee_colonies(status);
CREATE INDEX IF NOT EXISTS idx_inee_intents_status ON inee_intents(status);
CREATE INDEX IF NOT EXISTS idx_inee_intents_correlation ON inee_intents(correlation_id);
CREATE INDEX IF NOT EXISTS idx_colony_lifecycle_state ON colony_lifecycle(state);
CREATE INDEX IF NOT EXISTS idx_builder_patchsets_status ON builder_patchsets(status);
CREATE INDEX IF NOT EXISTS idx_reward_accounts_rank ON reward_accounts(rank);

"""


def bootstrap_inee_schema(db_connection):
    """
    Execute INEE schema bootstrap (idempotent).
    Called by ensure_schema() if VX11_INEE_ENABLED=1 or always (cheap).
    """
    cursor = db_connection.cursor()
    cursor.executescript(DB_SCHEMA_INEE_EXTENDED)
    db_connection.commit()
