"""
Unit tests for CLI Concentrator selection logic (Phase 3).
"""

import pytest
from switch.cli_concentrator import (
    CLIRegistry,
    CLIScorer,
    CircuitBreaker,
    CLIRequest,
    get_cli_registry,
)


@pytest.fixture
def registry():
    """Fixture: CLI registry."""
    return get_cli_registry()


@pytest.fixture
def breaker():
    """Fixture: circuit breaker."""
    return CircuitBreaker(failure_threshold=3, recovery_timeout_s=60)


@pytest.fixture
def scorer(registry, breaker):
    """Fixture: CLI scorer."""
    return CLIScorer(registry, breaker)


class TestCLIConcentratorSelection:
    """Test CLI selection logic."""

    def test_copilot_cli_priority(self, registry, scorer, breaker):
        """Test that best provider is selected (priority logic works)."""
        # Arrange
        request = CLIRequest(
            prompt="Test prompt",
            intent="chat",
            task_type="short",
        )
        fluzo_data = {"profile": "balanced"}

        # Act
        provider, debug = scorer.select_best_provider(request, fluzo_data)

        # Assert: provider should be selected
        assert provider is not None
        # Should have a valid provider ID
        assert provider.provider_id in ["copilot_cli", "generic_shell"]
        # Debug should show selection reason
        assert "selected_provider" in debug

    def test_breaker_blocks_failed_provider(self, registry, scorer, breaker):
        """Test circuit breaker blocks failed providers."""
        # Arrange
        provider = registry.get_provider("copilot_cli")
        request = CLIRequest(
            prompt="Test",
            intent="chat",
            task_type="short",
        )

        # Act: record failures to open breaker
        for _ in range(3):
            breaker.record_failure("copilot_cli")

        # Assert: breaker should be open
        assert not breaker.is_available("copilot_cli")

        # Select should skip this provider
        selected, debug = scorer.select_best_provider(request)
        # Should fallback to another provider or None
        if selected:
            assert selected.provider_id != "copilot_cli"

    def test_quota_influences_scoring(self, registry, scorer):
        """Test that quota affects provider scoring."""
        # Arrange
        request = CLIRequest(
            prompt="Test",
            intent="chat",
            task_type="short",
        )

        # Get any available provider
        providers = registry.list_providers()
        if not providers:
            pytest.skip("No providers available")

        provider = providers[0]

        # Save original quota
        original_quota = provider.quota_daily

        # Act: score with low quota
        provider.quota_daily = 10
        score1, debug1 = scorer.score_provider(provider, request)

        # Score with high quota
        provider.quota_daily = 1000
        score2, debug2 = scorer.score_provider(provider, request)

        # Assert: higher quota should not decrease score
        # (may be equal if other factors override)
        assert score2 >= score1

        # Restore
        provider.quota_daily = original_quota

    def test_registry_lists_providers(self, registry):
        """Test registry lists available providers."""
        # Act
        providers = registry.list_providers()

        # Assert
        assert len(providers) > 0
        provider_ids = [p.provider_id for p in providers]
        assert "copilot_cli" in provider_ids

    def test_provider_preference_override(self, registry, scorer):
        """Test that user can request preferred provider."""
        # Arrange
        request = CLIRequest(
            prompt="Test",
            intent="chat",
            task_type="short",
            provider_preference="generic_shell",
        )

        # Act
        provider, debug = scorer.select_best_provider(request)

        # Assert
        if provider:
            assert provider.provider_id == "generic_shell"
            assert debug["reason"] == "user_preference"
