"""
Tests for DB schema and models.
"""

import pytest
from pathlib import Path
import uuid as uuid_lib


def test_db_schema_exists():
    """Test that db_schema.py can be imported."""
    from config import db_schema
    assert hasattr(db_schema, 'Task')
    assert hasattr(db_schema, 'Context')
    assert hasattr(db_schema, 'Report')
    assert hasattr(db_schema, 'Spawn')
    assert hasattr(db_schema, 'IADecision')
    assert hasattr(db_schema, 'ModuleHealth')


def test_db_tables_created():
    """Test that unified DB (vx11.db) is created on module import."""
    from config import db_schema
    # VX11 v6.4: BD unificada en data/runtime/vx11.db
    db_path = Path("./data/runtime/vx11.db")
    assert db_path.exists(), f"Unified DB file {db_path} should exist"


def test_get_session():
    """Test getting a DB session."""
    from config import db_schema
    try:
        session = db_schema.get_session("madre")
        assert session is not None
        session.close()
    except Exception as e:
        pytest.fail(f"get_session failed: {e}")


def test_task_model():
    """Test Task ORM model with unique UUID."""
    from config import db_schema
    try:
        session = db_schema.get_session("madre")
        unique_uuid = f"test-task-{uuid_lib.uuid4().hex[:8]}"
        task = db_schema.Task(
            uuid=unique_uuid,
            name="test-task",
            module="spawner",
            action="spawn",
            status="pending",
        )
        session.add(task)
        session.commit()
        fetched = session.query(db_schema.Task).filter_by(uuid=unique_uuid).first()
        assert fetched is not None
        assert fetched.name == "test-task"
        session.close()
    except Exception as e:
        pytest.fail(f"Task model test failed: {e}")


def test_spawn_model():
    """Test Spawn ORM model with unique UUID."""
    from config import db_schema
    try:
        session = db_schema.get_session("madre")
        unique_uuid = f"spawn-{uuid_lib.uuid4().hex[:8]}"
        spawn = db_schema.Spawn(
            uuid=unique_uuid,
            name="test-spawn",
            cmd="echo test",
            status="pending",
        )
        session.add(spawn)
        session.commit()
        fetched = session.query(db_schema.Spawn).filter_by(uuid=unique_uuid).first()
        assert fetched is not None
        assert fetched.name == "test-spawn"
        session.close()
    except Exception as e:
        pytest.fail(f"Spawn model test failed: {e}")
