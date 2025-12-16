"""
Unit tests for CLI usage DB writes (Phase 3).
"""

import pytest
from datetime import datetime
from config.db_schema import get_session, CLIUsageStat as CLIUsageStatModel


@pytest.fixture
def db_session():
    """Fixture: DB session."""
    session = get_session("vx11")
    yield session
    # Cleanup
    try:
        session.close()
    except:
        pass


class TestCLIUsageDBWrites:
    """Test CLI usage statistics persistence."""

    def test_cli_usage_stat_insert(self, db_session):
        """Test inserting CLI usage stat."""
        # Arrange
        stat = CLIUsageStatModel(
            provider_id="copilot_cli",
            timestamp=datetime.utcnow(),
            success=True,
            latency_ms=150,
            cost_estimated=0.001,
            tokens_estimated=100,
            error_class=None,
        )

        # Act
        db_session.add(stat)
        db_session.commit()

        # Assert
        retrieved = (
            db_session.query(CLIUsageStatModel)
            .filter_by(provider_id="copilot_cli")
            .first()
        )
        assert retrieved is not None
        assert retrieved.latency_ms == 150
        assert retrieved.success is True

    def test_multiple_cli_usage_stats(self, db_session):
        """Test inserting multiple stats."""
        # Arrange
        stats = [
            CLIUsageStatModel(
                provider_id="copilot_cli",
                success=True,
                latency_ms=100,
            ),
            CLIUsageStatModel(
                provider_id="generic_shell",
                success=True,
                latency_ms=50,
            ),
            CLIUsageStatModel(
                provider_id="copilot_cli",
                success=False,
                error_class="timeout",
                latency_ms=5000,
            ),
        ]

        # Act
        for stat in stats:
            db_session.add(stat)
        db_session.commit()

        # Assert: check counts
        copilot_count = (
            db_session.query(CLIUsageStatModel)
            .filter_by(provider_id="copilot_cli")
            .count()
        )
        assert copilot_count >= 2

        shell_count = (
            db_session.query(CLIUsageStatModel)
            .filter_by(provider_id="generic_shell")
            .count()
        )
        assert shell_count >= 1

    def test_cli_usage_stat_query_by_success(self, db_session):
        """Test querying stats by success."""
        # Arrange
        stat_success = CLIUsageStatModel(
            provider_id="test_provider",
            success=True,
            latency_ms=100,
        )
        stat_fail = CLIUsageStatModel(
            provider_id="test_provider",
            success=False,
            error_class="error",
            latency_ms=500,
        )

        # Act
        db_session.add(stat_success)
        db_session.add(stat_fail)
        db_session.commit()

        # Assert
        successes = (
            db_session.query(CLIUsageStatModel)
            .filter_by(
                provider_id="test_provider",
                success=True,
            )
            .all()
        )
        assert len(successes) >= 1

        failures = (
            db_session.query(CLIUsageStatModel)
            .filter_by(
                provider_id="test_provider",
                success=False,
            )
            .all()
        )
        assert len(failures) >= 1

    def test_routing_event_insert(self, db_session):
        """Test inserting routing event."""
        from config.db_schema import RoutingEvent

        # Arrange
        event = RoutingEvent(
            trace_id="test-trace-123",
            route_type="cli",
            provider_id="copilot_cli",
            score=95.5,
            reasoning_short="High priority + balanced mode",
        )

        # Act
        db_session.add(event)
        db_session.commit()

        # Assert
        retrieved = (
            db_session.query(RoutingEvent).filter_by(trace_id="test-trace-123").first()
        )
        assert retrieved is not None
        assert retrieved.provider_id == "copilot_cli"
        assert retrieved.route_type == "cli"
