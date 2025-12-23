"""
INEE DB DAO (full integration with sqlite).
Handles CRUD for colonies, agents, intents, pheromones, audit.
"""

import sqlite3
import os
from typing import List, Optional
from datetime import datetime
from ..intents.types import INEEColony, INEEAgent, INEEIntent, INEEPheromone
from .schema import INEE_SCHEMA_SQL


class INEEDBManager:
    """Manages INEE database operations."""

    def __init__(self, db_path: str = "data/runtime/vx11.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Get DB connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        """Create INEE tables if they don't exist."""
        try:
            conn = self._get_conn()
            for stmt in INEE_SCHEMA_SQL.split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(stmt)
            conn.commit()
            conn.close()
        except Exception as e:
            # Schema might already exist or be invalid; continue
            pass

    # COLONIES

    def save_colony(self, colony: INEEColony) -> bool:
        """Save or update colony."""
        try:
            conn = self._get_conn()
            now = datetime.utcnow().isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO inee_colonies
                (colony_id, remote_url, status, last_heartbeat, agent_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    colony.colony_id,
                    colony.remote_url,
                    colony.status,
                    colony.last_heartbeat,
                    colony.agent_count,
                    colony.created_at or now,
                    now,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving colony: {e}")
            return False

    def get_colonies(self) -> List[INEEColony]:
        """Get all colonies."""
        try:
            conn = self._get_conn()
            rows = conn.execute("SELECT * FROM inee_colonies").fetchall()
            conn.close()
            return [INEEColony(**dict(row)) for row in rows]
        except Exception:
            return []

    def get_colony(self, colony_id: str) -> Optional[INEEColony]:
        """Get colony by ID."""
        try:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT * FROM inee_colonies WHERE colony_id = ?", (colony_id,)
            ).fetchone()
            conn.close()
            return INEEColony(**dict(row)) if row else None
        except Exception:
            return None

    # AGENTS

    def save_agent(self, agent: INEEAgent) -> bool:
        """Save or update agent."""
        try:
            conn = self._get_conn()
            now = datetime.utcnow().isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO inee_agents
                (agent_id, colony_id, agent_type, status, last_seen, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    agent.agent_id,
                    agent.colony_id,
                    agent.agent_type,
                    agent.status,
                    agent.last_seen,
                    agent.created_at or now,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving agent: {e}")
            return False

    def get_agents(self) -> List[INEEAgent]:
        """Get all agents."""
        try:
            conn = self._get_conn()
            rows = conn.execute("SELECT * FROM inee_agents").fetchall()
            conn.close()
            return [INEEAgent(**dict(row)) for row in rows]
        except Exception:
            return []

    def get_agents_by_colony(self, colony_id: str) -> List[INEEAgent]:
        """Get agents in a colony."""
        try:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT * FROM inee_agents WHERE colony_id = ?", (colony_id,)
            ).fetchall()
            conn.close()
            return [INEEAgent(**dict(row)) for row in rows]
        except Exception:
            return []

    # INTENTS

    def save_intent(self, intent: INEEIntent) -> bool:
        """Save intent history."""
        try:
            conn = self._get_conn()
            now = datetime.utcnow().isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO inee_intents
                (intent_id, correlation_id, source, operation, remote_colony_id, context_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    intent.intent_id,
                    intent.correlation_id,
                    "inee",
                    "translate",
                    intent.remote_colony_id,
                    str(intent.payload),
                    intent.timestamp,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving intent: {e}")
            return False

    def list_intents(self, limit: int = 100) -> List[dict]:
        """List recent intents."""
        try:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT * FROM inee_intents ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []

    # PHEROMONES

    def save_pheromone(self, pheromone: INEEPheromone) -> bool:
        """Save pheromone (signal)."""
        try:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT OR REPLACE INTO inee_pheromones
                (pheromone_id, colony_id, signal_type, payload_json, ttl_seconds, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    pheromone.pheromone_id,
                    pheromone.colony_id,
                    pheromone.signal_type,
                    str(pheromone.payload),
                    pheromone.ttl_seconds,
                    pheromone.created_at,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving pheromone: {e}")
            return False

    def list_pheromones(
        self, colony_id: Optional[str] = None, limit: int = 100
    ) -> List[dict]:
        """List pheromones, optionally filtered by colony."""
        try:
            conn = self._get_conn()
            if colony_id:
                rows = conn.execute(
                    "SELECT * FROM inee_pheromones WHERE colony_id = ? ORDER BY created_at DESC LIMIT ?",
                    (colony_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM inee_pheromones ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception:
            return []

    # AUDIT

    def log_audit_event(self, component: str, event_type: str, detail: dict) -> bool:
        """Log audit event."""
        try:
            import uuid

            conn = self._get_conn()
            now = datetime.utcnow().isoformat()
            conn.execute(
                """
                INSERT INTO inee_audit_events
                (event_id, component, event_type, detail_json, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    str(uuid.uuid4()),
                    component,
                    event_type,
                    str(detail),
                    now,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error logging audit: {e}")
            return False
