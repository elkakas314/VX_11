"""
Tests for Operator BD Schema (v7.0)
"""

import pytest
import uuid
from config.db_schema import (
    get_session,
    OperatorSession,
    OperatorMessage,
    OperatorToolCall,
    OperatorBrowserTask,
    OperatorSwitchAdjustment,
)


@pytest.fixture
def db_session():
    """Get database session for tests."""
    session = get_session("vx11")
    yield session
    session.close()


class TestOperatorSession:
    """Test OperatorSession table."""

    def test_create_session(self, db_session):
        """Create new operator session."""
        session_id = f"test-session-{uuid.uuid4().hex[:12]}"
        session = OperatorSession(
            session_id=session_id,
            user_id="test-user",
            source="web",
        )
        db_session.add(session)
        db_session.commit()
        
        retrieved = db_session.query(OperatorSession).filter_by(
            session_id=session_id
        ).first()
        assert retrieved is not None
        assert retrieved.user_id == "test-user"
        assert retrieved.source == "web"


class TestOperatorMessage:
    """Test OperatorMessage table."""

    def test_create_message(self, db_session):
        """Create message in session."""
        # First create session
        session_id = f"test-msg-session-{uuid.uuid4().hex[:12]}"
        session = OperatorSession(
            session_id=session_id,
            user_id="test-user",
        )
        db_session.add(session)
        db_session.commit()
        
        # Then create message
        msg = OperatorMessage(
            session_id=session_id,
            role="user",
            content="Hello!",
        )
        db_session.add(msg)
        db_session.commit()
        
        retrieved = db_session.query(OperatorMessage).filter_by(
            session_id=session_id
        ).first()
        assert retrieved is not None
        assert retrieved.role == "user"
        assert retrieved.content == "Hello!"


class TestOperatorToolCall:
    """Test OperatorToolCall table."""

    def test_create_tool_call(self, db_session):
        """Create tool call record."""
        # Setup
        session_id = f"test-tool-session-{uuid.uuid4().hex[:12]}"
        session = OperatorSession(session_id=session_id, user_id="user")
        db_session.add(session)
        db_session.commit()
        
        msg = OperatorMessage(
            session_id=session_id,
            role="assistant",
            content="Calling tool",
        )
        db_session.add(msg)
        db_session.commit()
        
        # Create tool call
        tool_call = OperatorToolCall(
            message_id=msg.id,
            tool_name="switch",
            status="ok",
            duration_ms=150,
        )
        db_session.add(tool_call)
        db_session.commit()
        
        retrieved = db_session.query(OperatorToolCall).filter_by(
            tool_name="switch"
        ).first()
        assert retrieved is not None
        assert retrieved.status == "ok"
        assert retrieved.duration_ms == 150


class TestOperatorBrowserTask:
    """Test OperatorBrowserTask table."""

    def test_create_browser_task(self, db_session):
        """Create browser task."""
        session_id = f"test-browser-session-{uuid.uuid4().hex[:12]}"
        session = OperatorSession(session_id=session_id, user_id="user")
        db_session.add(session)
        db_session.commit()
        
        task = OperatorBrowserTask(
            session_id=session_id,
            url="https://example.com",
            status="pending",
        )
        db_session.add(task)
        db_session.commit()
        
        retrieved = db_session.query(OperatorBrowserTask).filter_by(
            url="https://example.com"
        ).first()
        assert retrieved is not None
        assert retrieved.status == "pending"


class TestOperatorSwitchAdjustment:
    """Test OperatorSwitchAdjustment table."""

    def test_create_adjustment(self, db_session):
        """Create switch adjustment."""
        session_id = f"test-adj-session-{uuid.uuid4().hex[:12]}"
        session = OperatorSession(session_id=session_id, user_id="user")
        db_session.add(session)
        db_session.commit()
        
        adjustment = OperatorSwitchAdjustment(
            session_id=session_id,
            before_config='{"model":"local"}',
            after_config='{"model":"deepseek"}',
            reason="Local model was slow",
            applied=False,
        )
        db_session.add(adjustment)
        db_session.commit()
        
        retrieved = db_session.query(OperatorSwitchAdjustment).filter_by(
            session_id=session_id
        ).first()
        assert retrieved is not None
        assert retrieved.applied is False
        assert "deepseek" in retrieved.after_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
