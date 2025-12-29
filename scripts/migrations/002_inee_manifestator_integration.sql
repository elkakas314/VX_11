-- VX11 Migration 002: INEE + Manifestator + Rewards + Operator Integration
-- Generated: 2025-12-29
-- Purpose: Add all-new tables for INEE, Manifestator, Rewards, and Operator
-- Idempotent: Safe to run multiple times (IF NOT EXISTS + INSERT OR IGNORE)

-- ============================================================================
-- 1. INEE (Internal Neural Execution Environment)
-- ============================================================================

CREATE TABLE IF NOT EXISTS inee_colonies (
  colony_id TEXT PRIMARY KEY,
  name TEXT,
  status TEXT CHECK (status IN ('pending', 'active', 'suspended', 'offline')),
  beta_queen_url TEXT,
  protocol TEXT CHECK (protocol IN ('http', 'websocket', 'batch')),
  last_heartbeat DATETIME,
  last_seen DATETIME,
  max_agents INTEGER DEFAULT 1000 CHECK (max_agents > 0),
  rate_limit_per_minute INTEGER DEFAULT 100 CHECK (rate_limit_per_minute > 0),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT
);
CREATE INDEX IF NOT EXISTS idx_inee_colonies_status ON inee_colonies(status);
CREATE INDEX IF NOT EXISTS idx_inee_colonies_last_seen ON inee_colonies(last_seen);

CREATE TABLE IF NOT EXISTS inee_agents (
  agent_id TEXT,
  colony_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('egg', 'larva', 'adult', 'beta_queen')),
  status TEXT CHECK (status IN ('idle', 'processing', 'offline')),
  last_checkin DATETIME,
  telemetry_json TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (colony_id) REFERENCES inee_colonies(colony_id),
  PRIMARY KEY (agent_id, colony_id),
  UNIQUE (colony_id, agent_id)
);
CREATE INDEX IF NOT EXISTS idx_inee_agents_colony ON inee_agents(colony_id);
CREATE INDEX IF NOT EXISTS idx_inee_agents_role ON inee_agents(role);

CREATE TABLE IF NOT EXISTS inee_intents (
  intent_id TEXT PRIMARY KEY,
  colony_id TEXT NOT NULL,
  agent_id TEXT,
  phase TEXT NOT NULL CHECK (phase IN ('proposed', 'simulating', 'validated', 'approved', 'executing', 'completed', 'rejected')),
  intent_type TEXT CHECK (intent_type IN ('simulate', 'validate', 'apply', 'drift_repair', 'new_module')),
  payload_json TEXT NOT NULL,
  correlation_id TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  approver_id TEXT,
  approval_reason TEXT,
  result_json TEXT,
  FOREIGN KEY (colony_id) REFERENCES inee_colonies(colony_id)
);
CREATE INDEX IF NOT EXISTS idx_inee_intents_phase ON inee_intents(phase);
CREATE INDEX IF NOT EXISTS idx_inee_intents_colony ON inee_intents(colony_id);
CREATE INDEX IF NOT EXISTS idx_inee_intents_correlation_id ON inee_intents(correlation_id);
CREATE INDEX IF NOT EXISTS idx_inee_intents_created_at ON inee_intents(created_at);

CREATE TABLE IF NOT EXISTS inee_audit_events (
  event_id TEXT,
  correlation_id TEXT NOT NULL,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  source TEXT CHECK (source IN ('inee', 'manifestator', 'operator', 'madre')),
  event_type TEXT CHECK (event_type IN ('intent_proposed', 'simulated', 'executed', 'error', 'drift_detected', 'patch_applied')),
  severity TEXT CHECK (severity IN ('info', 'warn', 'crit')),
  message TEXT,
  structured_json TEXT,
  archive_date DATETIME,
  PRIMARY KEY (event_id, correlation_id, ts),
  UNIQUE (correlation_id, ts, event_id)
);
CREATE INDEX IF NOT EXISTS idx_inee_audit_correlation_id ON inee_audit_events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_inee_audit_created_at ON inee_audit_events(ts);
CREATE INDEX IF NOT EXISTS idx_inee_audit_archived ON inee_audit_events(archive_date) WHERE archive_date IS NULL;

CREATE TABLE IF NOT EXISTS inee_nonces (
  nonce TEXT,
  colony_id TEXT NOT NULL,
  used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  request_hash TEXT,
  FOREIGN KEY (colony_id) REFERENCES inee_colonies(colony_id),
  PRIMARY KEY (nonce, colony_id),
  UNIQUE (colony_id, nonce)
);
CREATE INDEX IF NOT EXISTS idx_inee_nonces_colony_ts ON inee_nonces(colony_id, used_at);

CREATE TABLE IF NOT EXISTS inee_policies (
  policy_id TEXT PRIMARY KEY,
  policy_type TEXT CHECK (policy_type IN ('rate_limit', 'budget', 'killswitch', 'execution_approval')),
  target_entity TEXT,
  config_json TEXT NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_by TEXT
);
CREATE INDEX IF NOT EXISTS idx_inee_policies_entity ON inee_policies(target_entity);
CREATE INDEX IF NOT EXISTS idx_inee_policies_active ON inee_policies(active);

-- ============================================================================
-- 2. REWARDS
-- ============================================================================

CREATE TABLE IF NOT EXISTS reward_accounts (
  account_id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('colony', 'agent', 'module')),
  entity_id TEXT NOT NULL,
  role TEXT,
  balance INTEGER DEFAULT 0,
  budget_limit INTEGER DEFAULT 10000 CHECK (budget_limit > 0),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (entity_type, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_reward_accounts_entity ON reward_accounts(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS reward_events (
  event_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  transaction_type TEXT CHECK (transaction_type IN ('earned', 'spent', 'penalty', 'adjustment')),
  amount INTEGER NOT NULL,
  reason TEXT,
  correlation_id TEXT,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (account_id) REFERENCES reward_accounts(account_id)
);
CREATE INDEX IF NOT EXISTS idx_reward_events_account_ts ON reward_events(account_id, ts);
CREATE INDEX IF NOT EXISTS idx_reward_events_correlation ON reward_events(correlation_id);

-- ============================================================================
-- 3. MANIFESTATOR
-- ============================================================================

CREATE TABLE IF NOT EXISTS manifestator_rails (
  rail_id TEXT PRIMARY KEY,
  name TEXT,
  description TEXT,
  rule_type TEXT CHECK (rule_type IN ('constraint', 'drift_threshold', 'naming_convention', 'schema_rule')),
  rule_definition_json TEXT NOT NULL,
  severity_on_violation TEXT CHECK (severity_on_violation IN ('warn', 'error', 'critical')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_manifestator_rails_active ON manifestator_rails(active);

CREATE TABLE IF NOT EXISTS manifestator_lanes (
  lane_id TEXT PRIMARY KEY,
  name TEXT,
  description TEXT,
  stage TEXT CHECK (stage IN ('detect', 'plan', 'validate', 'apply')),
  checks_json TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manifestator_audit (
  audit_id TEXT PRIMARY KEY,
  run_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  patch_plan_json TEXT,
  status TEXT CHECK (status IN ('draft', 'approved', 'applied', 'rolled_back')),
  applied_at DATETIME,
  applied_by TEXT,
  correlation_id TEXT,
  evidence_paths_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_manifestator_audit_correlation ON manifestator_audit(correlation_id);

-- ============================================================================
-- 4. OPERATOR
-- ============================================================================

CREATE TABLE IF NOT EXISTS operator_events (
  event_id TEXT PRIMARY KEY,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  event_type TEXT CHECK (event_type IN ('status', 'module', 'window', 'intent', 'audit')),
  severity TEXT CHECK (severity IN ('info', 'warn', 'crit')),
  module TEXT,
  correlation_id TEXT,
  summary TEXT,
  payload_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_operator_events_ts ON operator_events(ts);
CREATE INDEX IF NOT EXISTS idx_operator_events_module ON operator_events(module);

CREATE TABLE IF NOT EXISTS operator_settings (
  key TEXT PRIMARY KEY,
  value_json TEXT,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_by TEXT
);

CREATE TABLE IF NOT EXISTS operator_metrics (
  metric_id TEXT PRIMARY KEY,
  ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  metric_name TEXT CHECK (metric_name IN ('cpu_percent', 'ram_gib', 'latency_ms', 'chat_throughput', 'window_ttl', 'event_backlog')),
  value REAL,
  module TEXT,
  dimensions_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_operator_metrics_ts ON operator_metrics(ts);
CREATE INDEX IF NOT EXISTS idx_operator_metrics_name ON operator_metrics(metric_name);

-- ============================================================================
-- 5. SCHEMA VERSION TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS vx11_migration_log (
  migration_id TEXT PRIMARY KEY,
  applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  description TEXT,
  source_file TEXT
);

-- Record this migration (idempotent)
INSERT OR IGNORE INTO vx11_migration_log (migration_id, description, source_file)
VALUES ('002_inee_manifestator_integration', 'Add INEE + Manifestator + Rewards + Operator tables', 'migrations/002_inee_manifestator_integration.sql');

-- ============================================================================
-- 6. SEED DATA (Optional: defaults for policy rails)
-- ============================================================================

-- Add default manifestator rails if none exist (seed only on first run)
INSERT OR IGNORE INTO manifestator_rails (rail_id, name, description, rule_type, rule_definition_json, severity_on_violation, active)
VALUES (
  'rail_001_single_entrypoint',
  'Single Entrypoint Validation',
  'All external traffic must come through tentaculo_link:8000',
  'constraint',
  '{"target": "tentaculo_link", "port": 8000, "enforce": true}',
  'critical',
  TRUE
);

INSERT OR IGNORE INTO manifestator_rails (rail_id, name, description, rule_type, rule_definition_json, severity_on_violation, active)
VALUES (
  'rail_002_solo_madre_default',
  'solo_madre Default Policy',
  'Default mode: only madre + redis up. New services OFF by policy.',
  'constraint',
  '{"default_policy": "solo_madre", "services_required": ["madre", "redis"], "allowed_services_on_window": ["switch", "spawner", "hormiguero"]}',
  'critical',
  TRUE
);

INSERT OR IGNORE INTO manifestator_lanes (lane_id, name, description, stage, checks_json)
VALUES (
  'lane_001_detect',
  'Drift Detection',
  'Identify deviations from canonical state',
  'detect',
  '[{"check_id": "drift_001", "name": "File integrity check", "timeout_seconds": 30}]'
);

INSERT OR IGNORE INTO manifestator_lanes (lane_id, name, description, stage, checks_json)
VALUES (
  'lane_002_validate',
  'Patch Validation',
  'Validate patch plans before approval',
  'validate',
  '[{"check_id": "patch_001", "name": "Schema compatibility", "timeout_seconds": 60}]'
);

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
