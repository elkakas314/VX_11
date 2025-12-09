"""
Tests para Plug-and-Play Container State Management y Switch-Hermes Integration.
Fase B y Fase C validation.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from config.container_state import (
    set_state, get_state, get_all_states, is_active, is_standby, is_off,
    should_process, get_active_modules, get_standby_modules, get_off_modules
)
from config.switch_hermes_integration import (
    AdaptiveEngineSelector, EngineMetrics, ENGINE_PROFILES, get_selector
)


class TestContainerStatePnP:
    """Test Plug-and-Play container state management."""
    
    def test_set_state_valid_transitions(self):
        """Test valid state transitions."""
        assert set_state("madre", "active") == True  # Already active, but force
        assert set_state("madre", "standby") == True
        assert get_state("madre")["state"] == "standby"
        assert set_state("madre", "off") == True
        assert get_state("madre")["state"] == "off"
    
    def test_set_state_invalid_module(self):
        """Test setting state on non-existent module."""
        result = set_state("nonexistent", "active")
        assert result == False
    
    def test_set_state_invalid_state(self):
        """Test setting invalid state."""
        result = set_state("madre", "invalid")
        assert result == False
    
    def test_state_predicates(self):
        """Test state checking predicates."""
        set_state("manifestator", "active")
        assert is_active("manifestator") == True
        assert is_standby("manifestator") == False
        assert is_off("manifestator") == False
        
        set_state("manifestator", "standby")
        assert is_active("manifestator") == False
        assert is_standby("manifestator") == True
        assert is_off("manifestator") == False
    
    def test_should_process(self):
        """Test should_process predicate."""
        set_state("switch", "active")
        assert should_process("switch") == True
        
        set_state("switch", "standby")
        assert should_process("switch") == False
        
        set_state("switch", "off")
        assert should_process("switch") == False
    
    def test_get_module_lists(self):
        """Test getting lists by state."""
        set_state("madre", "active")
        set_state("switch", "standby")
        set_state("manifestator", "off")
        
        active = get_active_modules()
        assert "madre" in active
        
        standby = get_standby_modules()
        assert "switch" in standby
        
        off = get_off_modules()
        assert "manifestator" in off
    
    def test_get_all_states(self):
        """Test getting all module states."""
        all_states = get_all_states()
        assert len(all_states) == 9  # All 9 modules
        assert all(isinstance(v, dict) for v in all_states.values())
        assert all("state" in v and "last_changed" in v for v in all_states.values())


class TestEngineMetrics:
    """Test engine metrics tracking."""
    
    def test_metrics_initialization(self):
        """Test metrics object creation."""
        m = EngineMetrics("test_engine")
        assert m.engine_name == "test_engine"
        assert m.total_requests == 0
        assert m.status == "available"
        assert m.circuit_breaker_open == False
    
    def test_record_success(self):
        """Test recording successful requests."""
        m = EngineMetrics("engine1")
        m.record_success(100)
        m.record_success(150)
        
        assert m.total_requests == 2
        assert m.successful_requests == 2
        assert m.failed_requests == 0
        assert m.consecutive_errors == 0
        assert m.get_avg_latency_ms() == 125.0
    
    def test_record_error(self):
        """Test recording failed requests."""
        m = EngineMetrics("engine1")
        m.record_error("Connection timeout")
        m.record_error("Invalid response")
        
        assert m.total_requests == 2
        assert m.successful_requests == 0
        assert m.failed_requests == 2
        assert m.consecutive_errors == 2
        assert m.status == "error"
        assert m.last_error == "Invalid response"
    
    def test_circuit_breaker_opens(self):
        """Test circuit breaker opens after 5 errors."""
        m = EngineMetrics("engine1")
        
        for i in range(4):
            m.record_error(f"Error {i}")
            assert m.circuit_breaker_open == False
        
        m.record_error("Error 5")
        assert m.circuit_breaker_open == True
        assert m.consecutive_errors == 5
    
    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset after timeout."""
        import time
        m = EngineMetrics("engine1")
        
        # Open circuit
        for _ in range(5):
            m.record_error("Error")
        assert m.circuit_breaker_open == True
        
        # Try reset immediately (should fail)
        m.try_reset_circuit_breaker(timeout_seconds=60)
        assert m.circuit_breaker_open == True
        
        # Force reset with 0 timeout
        m.try_reset_circuit_breaker(timeout_seconds=0)
        assert m.circuit_breaker_open == False
        assert m.status == "available"
    
    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        m = EngineMetrics("engine1")
        m.record_success(100)
        m.record_success(100)
        m.record_error("Error")
        
        # 1 error out of 3 = 33.33%
        error_rate = m.get_error_rate()
        assert 33 < error_rate < 34


class TestAdaptiveEngineSelector:
    """Test adaptive engine selection."""
    
    def test_selector_initialization(self):
        """Test selector creation."""
        selector = AdaptiveEngineSelector()
        assert selector.current_mode == "BALANCED"
        assert selector.available_engines == []
    
    def test_register_engine(self):
        """Test engine registration."""
        selector = AdaptiveEngineSelector()
        selector.register_engine("hermes_local")
        
        assert "hermes_local" in selector.metrics
        assert isinstance(selector.metrics["hermes_local"], EngineMetrics)
    
    def test_set_mode(self):
        """Test mode setting."""
        selector = AdaptiveEngineSelector()
        selector.set_mode("CRITICAL")
        assert selector.current_mode == "CRITICAL"
        
        selector.set_mode("ECO")
        assert selector.current_mode == "ECO"
    
    def test_select_engine_basic(self):
        """Test basic engine selection."""
        selector = AdaptiveEngineSelector()
        selector.set_available_engines(["hermes_local", "cli_bash"])
        selector.set_mode("ECO")
        
        selection = selector.select_engine()
        
        assert selection["status"] == "ok"
        assert selection["engine"] in ["hermes_local", "cli_bash"]
        assert selection["mode"] == "ECO"
        assert "profile" in selection
    
    def test_select_engine_respects_mode(self):
        """Test that selection respects mode preferences."""
        selector = AdaptiveEngineSelector()
        selector.set_available_engines(["hermes_local", "deepseek", "openrouter_text"])
        
        # In ECO mode, prefer local
        selector.set_mode("ECO")
        selection_eco = selector.select_engine()
        # Should prefer local engines in ECO
        
        # In CRITICAL mode, prefer deepseek
        selector.set_mode("CRITICAL")
        selection_crit = selector.select_engine()
        # Profile should reflect CRITICAL timeout and concurrent limits
        assert selection_crit["profile"]["timeout_ms"] == 30000
        assert selection_crit["profile"]["max_concurrent"] == 16
    
    def test_engine_profiles_defined(self):
        """Test all engine profiles are defined."""
        modes = ["ECO", "BALANCED", "HIGH-PERF", "CRITICAL"]
        
        for mode in modes:
            assert mode in ENGINE_PROFILES
            profile = ENGINE_PROFILES[mode]
            assert "preferred_engines" in profile
            assert "timeout_ms" in profile
            assert "max_concurrent" in profile
            assert "fallback_chain" in profile
    
    def test_record_engine_result(self):
        """Test recording engine results."""
        selector = AdaptiveEngineSelector()
        selector.register_engine("hermes_local")
        
        selector.record_engine_result("hermes_local", success=True, latency_ms=100)
        metrics = selector.metrics["hermes_local"]
        assert metrics.successful_requests == 1
        
        selector.record_engine_result("hermes_local", success=False, error="Failed")
        assert metrics.failed_requests == 1
    
    def test_get_status(self):
        """Test getting selector status."""
        selector = AdaptiveEngineSelector()
        selector.register_engine("engine1")
        selector.register_engine("engine2")
        selector.set_available_engines(["engine1", "engine2"])
        
        status = selector.get_status()
        
        assert status["status"] == "ok"
        assert status["mode"] == "BALANCED"
        assert "metrics" in status
        assert "available_engines" in status
        assert "healthy_engines" in status


class TestSwitchHermesEndpoints:
    """Test switch-hermes integration endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client for switch module."""
        from switch.main import app
        return TestClient(app)
    
    def test_select_engine_endpoint(self, client):
        """Test /switch/hermes/select_engine endpoint."""
        response = client.post(
            "/switch/hermes/select_engine",
            json={
                "query": "Calculate sum of 1+1",
                "available_engines": ["hermes_local", "cli_bash"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "engine" in data
        assert "mode" in data
        assert "profile" in data
    
    def test_record_result_endpoint(self, client):
        """Test /switch/hermes/record_result endpoint."""
        response = client.post(
            "/switch/hermes/record_result",
            json={
                "engine": "hermes_local",
                "success": True,
                "latency_ms": 150
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["engine"] == "hermes_local"
        assert data["recorded"] == True
    
    def test_hermes_status_endpoint(self, client):
        """Test /switch/hermes/status endpoint."""
        response = client.get("/switch/hermes/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "mode" in data
        assert "available_engines" in data
        assert "healthy_engines" in data
        assert "metrics" in data


class TestCrossModuleIntegration:
    """Test cross-module integration (P&P + Switch-Hermes)."""
    
    def test_madre_orchestration_endpoints(self):
        """Test madre can query all module states."""
        from madre.main import app
        client = TestClient(app)
        
        # Get all module states
        response = client.get("/orchestration/module_states")
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert len(data["modules"]) == 9
    
    def test_set_module_state_via_madre(self):
        """Test madre can set module states."""
        from madre.main import app
        client = TestClient(app)
        
        response = client.post(
            "/orchestration/set_module_state",
            json={"module": "manifestator", "state": "standby"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "manifestator"
        assert data["state"] == "standby"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
