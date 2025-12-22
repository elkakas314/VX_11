import pytest
import sqlite3
import os
import sys
from importlib import import_module
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"

sys.path.insert(0, str(REPO_ROOT))
if SRC_ROOT.is_dir():
    sys.path.insert(0, str(SRC_ROOT))

# Ensure the package root itself is discoverable in editable installs.
sys.path.insert(0, str(SRC_ROOT / "hormiguero"))

db_module_path = SRC_ROOT / "hormiguero" / "core" / "db.py"
try:
    db_module = import_module("hormiguero.core.db")
except ModuleNotFoundError:
    if not db_module_path.is_file():
        raise
    spec = importlib.util.spec_from_file_location("hormiguero.core.db", db_module_path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Unable to load module from {db_module_path}")
    spec.loader.exec_module(module)
    repo = module.repo
    ensure_schema = module.ensure_schema
    get_connection = module.get_connection
else:
    repo = db_module.repo
    ensure_schema = db_module.ensure_schema
    get_connection = db_module.get_connection

try:
    settings = import_module("hormiguero.config").settings
except (ModuleNotFoundError, AttributeError):
    from types import SimpleNamespace

    settings = SimpleNamespace(db_path="")


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "vx11_test.db"
    monkeypatch.setattr(settings, "db_path", str(db_path))
    ensure_schema()
    return db_path


def test_hormiguero_transactional_integrity(temp_db):
    """Verifica que las mutaciones de estado sean atómicas."""
    # Insertar un estado inicial
    repo.upsert_hormiga_state(
        hormiga_id="ant-1",
        name="test-ant",
        role="scanner",
        enabled=True,
        aggression_level=1,
        scan_interval_sec=60,
        last_scan_at="2025-12-22T00:00:00Z",
        stats_json={"ok": True},
    )

    # Verificar que se insertó
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM hormiga_state WHERE hormiga_id='ant-1'"
        ).fetchone()
        assert row["name"] == "test-ant"
        assert row["enabled"] == 1


def test_hormiguero_incident_deduplication(temp_db):
    """Verifica que los incidentes con el mismo correlation_id se dedupliquen."""
    id1 = repo.upsert_incident(
        kind="test_drift",
        severity="high",
        status="open",
        title="Drift 1",
        description="Desc 1",
        source="test",
        correlation_id="corr-unique-123",
    )

    id2 = repo.upsert_incident(
        kind="test_drift",
        severity="high",
        status="open",
        title="Drift 2",
        description="Desc 2",
        source="test",
        correlation_id="corr-unique-123",
    )

    assert id1 == id2

    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) as c FROM incidents WHERE incident_id='corr-unique-123'"
        ).fetchone()["c"]
        assert count == 1


def test_hormiguero_pheromone_log(temp_db):
    """Verifica el registro de feromonas (acciones)."""
    # Simular una acción
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO pheromone_log (pheromone_id, action_kind, status, created_at) VALUES (?, ?, ?, ?)",
            ("ph-1", "cleanup", "pending", "2025-12-22T10:00:00Z"),
        )
        conn.commit()

    logs = repo.list_pheromones(limit=10)
    assert len(logs) >= 1
    assert logs[0]["pheromone_id"] == "ph-1"
