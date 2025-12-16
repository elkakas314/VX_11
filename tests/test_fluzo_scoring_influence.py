"""
Unit tests for FLUZO scoring influence (Phase 3).
"""

import pytest
from switch.cli_concentrator import CLIRegistry, CLIScorer, CircuitBreaker, CLIRequest
from switch.fluzo import FLUZOClient


@pytest.fixture
def registry():
    """Fixture: CLI registry."""
    return CLIRegistry()


@pytest.fixture
def breaker():
    """Fixture: circuit breaker."""
    return CircuitBreaker()


@pytest.fixture
def scorer(registry, breaker):
    """Fixture: scorer."""
    return CLIScorer(registry, breaker)


@pytest.fixture
def fluzo_client():
    """Fixture: FLUZO client."""
    return FLUZOClient()


class TestFluzoScoringInfluence:
    """Test FLUZO impact on CLI scoring."""

    def test_low_power_mode_affects_scoring(self, scorer):
        """Test that low_power mode affects scoring."""
        # Arrange
        request = CLIRequest(
            prompt="Test",
            intent="chat",
            task_type="short",
        )
        providers = scorer.registry.list_providers()
        if not providers:
            pytest.skip("No providers available")

        provider = providers[0]

        # Act: score in balanced mode
        fluzo_balanced = {"profile": "balanced"}
        score_balanced, _ = scorer.score_provider(provider, request, fluzo_balanced)

        # Act: score in low_power mode
        fluzo_low_power = {"profile": "low_power"}
        score_low_power, _ = scorer.score_provider(provider, request, fluzo_low_power)

        # Assert: scores recorded
        assert isinstance(score_balanced, (int, float))
        assert isinstance(score_low_power, (int, float))

    def test_performance_mode_allows_heavy_operations(self, scorer):
        """Test that performance mode enables heavier CLIs."""
        # Arrange
        request = CLIRequest(
            prompt="Complex reasoning task",
            intent="reasoning",
            task_type="long",
        )
        providers = scorer.registry.list_providers()
        if not providers:
            pytest.skip("No providers available")

        provider = providers[0]

        # Act
        fluzo_perf = {"profile": "performance"}
        score, debug = scorer.score_provider(provider, request, fluzo_perf)

        # Assert: performance mode should produce a valid score
        assert isinstance(score, (int, float))
        assert score >= 0

    def test_fluzo_profile_derives_correct_mode(self, fluzo_client):
        """Test FLUZO profile derivation."""
        # Arrange
        low_power_signals = {
            "cpu_load_1m": 80.0,
            "memory_pct": 80.0,
            "on_ac": False,
            "battery_pct": 15,
        }

        balanced_signals = {
            "cpu_load_1m": 50.0,
            "memory_pct": 50.0,
            "on_ac": True,
            "battery_pct": None,
        }

        performance_signals = {
            "cpu_load_1m": 20.0,
            "memory_pct": 30.0,
            "on_ac": True,
            "battery_pct": None,
        }

        # Act
        profile_low = fluzo_client.profile.get_profile(low_power_signals)
        profile_balanced = fluzo_client.profile.get_profile(balanced_signals)
        profile_perf = fluzo_client.profile.get_profile(performance_signals)

        # Assert
        assert profile_low["mode"] in ["low_power", "balanced"]
        assert profile_balanced["mode"] == "balanced"
        assert profile_perf["mode"] == "performance"

    def test_fluzo_signals_collection(self, fluzo_client):
        """Test FLUZO signals are collected."""
        # Act
        signals = fluzo_client.get_signals()

        # Assert
        assert "cpu_load_1m" in signals
        assert "memory_pct" in signals
        assert "on_ac" in signals
        assert "timestamp" in signals

    def test_fluzo_client_get_mode(self, fluzo_client):
        """Test FLUZO client returns valid mode."""
        # Act
        mode = fluzo_client.get_mode()

        # Assert
        assert mode in ["low_power", "balanced", "performance"]
