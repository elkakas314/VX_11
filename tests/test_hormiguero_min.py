import os
import sqlite3
import sys

SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hormiguero"))
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from hormiguero.core.scanners import fs_drift
from hormiguero.core.db.sqlite import ensure_schema
from hormiguero.core.db import repo
from hormiguero.core.actions import executor
from hormiguero.config import settings


def test_fs_drift_ignores_paths(tmp_path):
    root = tmp_path
    (root / "keep.txt").write_text("ok", encoding="utf-8")
    (root / "node_modules").mkdir()
    (root / "node_modules" / "skip.txt").write_text("skip", encoding="utf-8")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("skip", encoding="utf-8")
    (root / "docs" / "audit").mkdir(parents=True)
    (root / "docs" / "audit" / "old.txt").write_text("skip", encoding="utf-8")

    paths = fs_drift._actual_paths(str(root))
    assert "keep.txt" in paths
    assert "node_modules/skip.txt" not in paths
    assert ".git/config" not in paths
    assert "docs/audit/old.txt" not in paths


def test_incidents_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "vx11.db"
    monkeypatch.setattr(settings, "db_path", str(db_path))
    ensure_schema()

    incident_id = repo.upsert_incident(
        kind="fs_drift",
        severity="info",
        status="open",
        title="Test",
        description="Test",
        source="pytest",
        correlation_id="corr-1",
    )
    incident_id_2 = repo.upsert_incident(
        kind="fs_drift",
        severity="info",
        status="open",
        title="Test",
        description="Test",
        source="pytest",
        correlation_id="corr-1",
    )

    assert incident_id == incident_id_2
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("SELECT COUNT(*) FROM incidents WHERE incident_id='corr-1';")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 1


def test_actions_require_approval(monkeypatch):
    monkeypatch.setattr(settings, "actions_enabled", False)
    result = executor.apply_actions(
        [{"action": "cleanup_pycache", "target": "./__pycache__"}],
        correlation_id="corr-2",
    )
    assert result["status"] == "denied"
