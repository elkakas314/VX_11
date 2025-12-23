"""
P0 tests for Madre rails lane routing (DB-first).
"""

import json
import os
import sqlite3
from pathlib import Path

import pytest

from config.rails_map_migrations import MIGRATION_SQL
from madre import rails_router


def _init_db(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(MIGRATION_SQL)
    conn.commit()
    conn.close()


def _seed_map_version(conn: sqlite3.Connection, version: str = "v1") -> None:
    conn.execute(
        """
        INSERT INTO rails_map_versions (version, content_hash, author, notes)
        VALUES (?, ?, ?, ?)
        """,
        (version, "hash", "test", "seed"),
    )
    conn.commit()


def test_lane_routing_hit(tmp_path, monkeypatch):
    db_path = tmp_path / "vx11.db"
    _init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    _seed_map_version(conn, "v1")
    conn.execute(
        """
        INSERT INTO rails_lanes (
            lane_id, domain, intent_type, owner_module, escalation_rule,
            constraints_json, invariants_json, map_version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "lane-1",
            "execution",
            "build",
            "madre",
            "route_to_builder",
            json.dumps({"ttl_sec": 300}),
            json.dumps(["no_exec_manifestator"]),
            "v1",
        ),
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("VX11_DB_PATH", str(db_path))
    lane = rails_router.find_lane("execution", "build")

    assert lane is not None
    assert lane["owner_module"] == "madre"
    assert lane["escalation_rule"] == "route_to_builder"
    assert lane["constraints"]["ttl_sec"] == 300


def test_lane_routing_miss_records_event(tmp_path, monkeypatch):
    db_path = tmp_path / "vx11.db"
    _init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    _seed_map_version(conn, "v1")
    conn.close()

    monkeypatch.setenv("VX11_DB_PATH", str(db_path))
    result = rails_router.resolve_lane(
        domain="communication",
        intent_type="notify",
        correlation_id="cid-123",
        details={"test": True},
    )

    assert result is None

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT what, correlation_id, result_json
        FROM rails_events
        ORDER BY id DESC
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "lane_missing"
    assert row[1] == "cid-123"
    payload = json.loads(row[2])
    assert payload["domain"] == "communication"
    assert payload["intent_type"] == "notify"
