"""
tests/test_contracts.py - Contract validation tests (Pydantic models & JSON schema)

Tests for:
- CoreIntent/Response JSON schema compliance
- WindowOpen/Status/Close contracts
- SpawnRequest/Response contracts
- TTL bounds validation (1-3600 seconds)
- max_retries bounds validation (0-10)
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from tentaculo_link.models_core_mvp import (
    CoreIntent,
    CoreIntentResponse,
    WindowOpen,
    WindowStatus,
    WindowClose,
    SpawnRequest,
    SpawnResponse,
    StatusEnum,
)


class TestCoreIntentContract:
    """Test CoreIntent contract validation"""

    def test_valid_intent_minimal(self):
        """CoreIntent with minimal fields → valid"""
        intent = CoreIntent(
            intent_type="chat",
            text="test question",
        )
        assert intent.intent_type == "chat"
        assert intent.text == "test question"

    def test_valid_intent_full(self):
        """CoreIntent with all fields → valid"""
        intent = CoreIntent(
            intent_type="chat",
            text="complex task",
            payload={"nested": {"data": 123}},
            user_id="user-123",
            priority="P0",
            metadata={"source": "test"},
        )
        assert intent.user_id == "user-123"
        assert intent.priority == "P0"

    def test_intent_schema_to_dict(self):
        """CoreIntent.model_dump() → valid dict"""
        intent = CoreIntent(intent_type="chat", text="test")
        data = intent.model_dump()
        assert "intent_type" in data
        assert "text" in data
        assert data["intent_type"] == "chat"


class TestCoreIntentResponseContract:
    """Test CoreIntentResponse contract"""

    def test_valid_response(self):
        """CoreIntentResponse with required fields → valid"""
        from tentaculo_link.models_core_mvp import StatusEnum, ModeEnum
        resp = CoreIntentResponse(
            correlation_id="corr-123",
            status=StatusEnum.DONE,
            mode=ModeEnum.MADRE,
        )
        assert resp.correlation_id == "corr-123"
        assert resp.status == StatusEnum.DONE

    def test_response_schema(self):
        """CoreIntentResponse.model_json_schema() → valid JSON schema"""
        schema = CoreIntentResponse.model_json_schema()
        assert "properties" in schema
        assert "correlation_id" in schema["properties"]


class TestWindowOpenContract:
    """Test WindowOpen contract"""

    def test_valid_window_open_minimal(self):
        """WindowOpen with ttl_seconds=300 → valid"""
        window = WindowOpen(target="spawner", ttl_seconds=300)
        assert window.target == "spawner"
        assert window.ttl_seconds == 300

    def test_valid_window_open_min_ttl(self):
        """WindowOpen with ttl_seconds=1 → valid"""
        window = WindowOpen(target="switch", ttl_seconds=1)
        assert window.ttl_seconds == 1

    def test_valid_window_open_max_ttl(self):
        """WindowOpen with ttl_seconds=3600 → valid"""
        window = WindowOpen(target="spawner", ttl_seconds=3600)
        assert window.ttl_seconds == 3600

    def test_window_open_ttl_too_low(self):
        """WindowOpen with ttl_seconds=0 → ValidationError"""
        with pytest.raises(ValidationError):
            WindowOpen(target="spawner", ttl_seconds=0)

    def test_window_open_ttl_too_high(self):
        """WindowOpen with ttl_seconds=3601 → ValidationError"""
        with pytest.raises(ValidationError):
            WindowOpen(target="spawner", ttl_seconds=3601)

    def test_window_open_negative_ttl(self):
        """WindowOpen with ttl_seconds=-1 → ValidationError"""
        with pytest.raises(ValidationError):
            WindowOpen(target="spawner", ttl_seconds=-1)


class TestWindowStatusContract:
    """Test WindowStatus contract"""

    def test_valid_window_status_open(self):
        """WindowStatus for open window → valid"""
        status = WindowStatus(
            target="spawner",
            is_open=True,
            ttl_remaining_seconds=250,
            window_id="w-123",
            opened_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
        )
        assert status.is_open is True
        assert status.ttl_remaining_seconds == 250

    def test_valid_window_status_closed(self):
        """WindowStatus for closed window → valid"""
        status = WindowStatus(
            target="switch",
            is_open=False,
            ttl_remaining_seconds=0,
        )
        assert status.is_open is False

    def test_window_status_schema(self):
        """WindowStatus.model_dump() includes all fields"""
        status = WindowStatus(
            target="spawner",
            is_open=True,
            ttl_remaining_seconds=100,
        )
        data = status.model_dump()
        assert data["is_open"] is True
        assert data["ttl_remaining_seconds"] == 100


class TestWindowCloseContract:
    """Test WindowClose contract"""

    def test_valid_window_close(self):
        """WindowClose with target → valid"""
        close = WindowClose(target="spawner", reason="manual")
        assert close.target == "spawner"
        assert close.reason == "manual"

    def test_window_close_missing_target(self):
        """WindowClose without target → ValidationError"""
        with pytest.raises(ValidationError):
            WindowClose(reason="manual")


class TestSpawnRequestContract:
    """Test SpawnRequest contract"""

    def test_valid_spawn_minimal(self):
        """SpawnRequest with task_type + code → valid"""
        req = SpawnRequest(
            task_type="python",
            code="print('hello')",
        )
        assert req.task_type == "python"
        assert req.max_retries == 0  # default
        assert req.ttl_seconds == 3600  # default

    def test_valid_spawn_full(self):
        """SpawnRequest with all fields → valid"""
        req = SpawnRequest(
            task_type="shell",
            code="echo test",
            max_retries=3,
            ttl_seconds=600,
            user_id="user-xyz",
            metadata={"priority": "high"},
            correlation_id="corr-456",
        )
        assert req.max_retries == 3
        assert req.ttl_seconds == 600

    def test_spawn_max_retries_min(self):
        """SpawnRequest with max_retries=0 → valid"""
        req = SpawnRequest(
            task_type="python",
            code="x=1",
            max_retries=0,
        )
        assert req.max_retries == 0

    def test_spawn_max_retries_max(self):
        """SpawnRequest with max_retries=10 → valid"""
        req = SpawnRequest(
            task_type="python",
            code="x=1",
            max_retries=10,
        )
        assert req.max_retries == 10

    def test_spawn_max_retries_too_low(self):
        """SpawnRequest with max_retries=-1 → ValidationError"""
        with pytest.raises(ValidationError):
            SpawnRequest(
                task_type="python",
                code="x=1",
                max_retries=-1,
            )

    def test_spawn_max_retries_too_high(self):
        """SpawnRequest with max_retries=11 → ValidationError"""
        with pytest.raises(ValidationError):
            SpawnRequest(
                task_type="python",
                code="x=1",
                max_retries=11,
            )

    def test_spawn_ttl_min(self):
        """SpawnRequest with ttl_seconds=1 → valid"""
        req = SpawnRequest(task_type="python", code="x=1", ttl_seconds=1)
        assert req.ttl_seconds == 1

    def test_spawn_ttl_max(self):
        """SpawnRequest with ttl_seconds=86400 → valid"""
        req = SpawnRequest(task_type="python", code="x=1", ttl_seconds=86400)
        assert req.ttl_seconds == 86400

    def test_spawn_ttl_too_low(self):
        """SpawnRequest with ttl_seconds=0 → ValidationError"""
        with pytest.raises(ValidationError):
            SpawnRequest(task_type="python", code="x=1", ttl_seconds=0)

    def test_spawn_ttl_too_high(self):
        """SpawnRequest with ttl_seconds=86401 → ValidationError"""
        with pytest.raises(ValidationError):
            SpawnRequest(task_type="python", code="x=1", ttl_seconds=86401)


class TestSpawnResponseContract:
    """Test SpawnResponse contract"""

    def test_valid_spawn_response(self):
        """SpawnResponse with all fields → valid"""
        resp = SpawnResponse(
            spawn_id="spawn-123",
            correlation_id="corr-456",
            status="QUEUED",
            task_type="python",
        )
        assert resp.spawn_id == "spawn-123"
        assert resp.status == "QUEUED"

    def test_spawn_response_default_status(self):
        """SpawnResponse status defaults to QUEUED"""
        resp = SpawnResponse(
            spawn_id="spawn-xyz",
            task_type="shell",
        )
        assert resp.status == "QUEUED"

    def test_spawn_response_schema(self):
        """SpawnResponse.model_dump() includes datetime"""
        resp = SpawnResponse(
            spawn_id="s1",
            status="RUNNING",
            task_type="python",
        )
        data = resp.model_dump()
        assert "created_at" in data
        assert isinstance(data["created_at"], datetime)

    def test_spawn_response_json(self):
        """SpawnResponse.model_dump_json() produces valid JSON"""
        resp = SpawnResponse(
            spawn_id="s2",
            correlation_id="c2",
            task_type="python",
        )
        json_str = resp.model_dump_json()
        assert "spawn_id" in json_str
        assert "queued" in json_str.lower()
