"""
RailsMap schema migrations (idempotent).
Run once at startup or manually via: python3 -m config.rails_map_migrations
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = Path("./data/runtime/vx11.db")

# Migration SQL (idempotent: CREATE TABLE IF NOT EXISTS)
MIGRATION_SQL = """
-- Rails Map Versioning
CREATE TABLE IF NOT EXISTS rails_map_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  version TEXT UNIQUE NOT NULL,
  content_hash TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  author TEXT,
  notes TEXT,
  source_canon_hash TEXT
);

-- Rails Lanes (domain + intent_type routing)
CREATE TABLE IF NOT EXISTS rails_lanes (
  lane_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  intent_type TEXT NOT NULL,
  owner_module TEXT NOT NULL,
  escalation_rule TEXT,
  constraints_json TEXT,
  invariants_json TEXT,
  map_version TEXT NOT NULL,
  FOREIGN KEY (map_version) REFERENCES rails_map_versions(version)
);

-- Flow Templates
CREATE TABLE IF NOT EXISTS rails_flow_templates (
  flow_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  triggers_json TEXT,
  steps_json TEXT,
  invariants_json TEXT,
  map_version TEXT NOT NULL,
  FOREIGN KEY (map_version) REFERENCES rails_map_versions(version)
);

-- Container Blueprints (sandbox policies)
CREATE TABLE IF NOT EXISTS rails_container_blueprints (
  blueprint_id TEXT PRIMARY KEY,
  purpose TEXT,
  sandbox_policy_json TEXT,
  mounts_json TEXT,
  network_config TEXT,
  cpu_limit_millicores INTEGER,
  mem_limit_mb INTEGER,
  ttl_sec INTEGER,
  map_version TEXT NOT NULL,
  FOREIGN KEY (map_version) REFERENCES rails_map_versions(version)
);

-- Rails Events (audit trail)
CREATE TABLE IF NOT EXISTS rails_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  who TEXT NOT NULL,
  what TEXT NOT NULL,
  when_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
  why TEXT,
  result_json TEXT,
  correlation_id TEXT
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_rails_lanes_domain_intent 
  ON rails_lanes(domain, intent_type);
CREATE INDEX IF NOT EXISTS idx_rails_flow_templates_domain 
  ON rails_flow_templates(domain);
CREATE INDEX IF NOT EXISTS idx_rails_events_correlation 
  ON rails_events(correlation_id);
CREATE INDEX IF NOT EXISTS idx_rails_events_when 
  ON rails_events(when_ts);
"""


def migrate():
    """Apply migrations (idempotent)."""
    if not DB_PATH.exists():
        logger.error(f"DB not found: {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA foreign_keys=ON;")

        cursor = conn.cursor()

        # Split SQL into individual statements
        statements = MIGRATION_SQL.split(";")
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                cursor.execute(stmt)

        conn.commit()
        logger.info(f"✓ Rails map schema migrated successfully: {DB_PATH}")

        # Log migration event
        cursor.execute(
            """
          INSERT INTO rails_events (who, what, why)
          VALUES (?, ?, ?)
        """,
            ("migration", "rails_schema_created", "initialization"),
        )
        conn.commit()

        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"Migration failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = migrate()
    exit(0 if success else 1)
