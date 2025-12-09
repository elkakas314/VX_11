"""
Tests for mode transitions and adaptive optimization endpoints.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from config.settings import settings


@pytest.fixture
def client():
    """Fixture to create test client for switch module."""
    from switch.main import app
    return TestClient(app)


@pytest.fixture
def madre_client():
    """Fixture to create test client for madre module."""
    from madre.main import app
    return TestClient(app)


@pytest.fixture
def hormiguero_client():
    """Fixture to create test client for hormiguero module."""
    from hormiguero.main import app
    return TestClient(app)


class TestSwitchModeControl:
    """Test switch module mode control endpoint."""
    
    def test_switch_control_set_mode_eco(self, client):
        """Test setting switch to ECO mode."""
        response = client.post(
            "/switch/control",
            json={"action": "set_mode", "mode": "ECO"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["mode"] == "ECO"
        assert "profile" in data
    
    def test_switch_control_set_mode_balanced(self, client):
        """Test setting switch to BALANCED mode."""
        response = client.post(
            "/switch/control",
            json={"action": "set_mode", "mode": "BALANCED"}
        )
        assert response.status_code == 200
        assert response.json()["mode"] == "BALANCED"
    
    def test_switch_control_set_mode_high_perf(self, client):
        """Test setting switch to HIGH-PERF mode."""
        response = client.post(
            "/switch/control",
            json={"action": "set_mode", "mode": "HIGH-PERF"}
        )
        assert response.status_code == 200
        assert response.json()["mode"] == "HIGH-PERF"
    
    def test_switch_control_set_mode_critical(self, client):
        """Test setting switch to CRITICAL mode."""
        response = client.post(
            "/switch/control",
            json={"action": "set_mode", "mode": "CRITICAL"}
        )
        assert response.status_code == 200
        assert response.json()["mode"] == "CRITICAL"
    
    def test_switch_control_invalid_mode(self, client):
        """Test error on invalid mode."""
        response = client.post(
            "/switch/control",
            json={"action": "set_mode", "mode": "INVALID_MODE"}
        )
        assert response.status_code == 200  # FastAPI returns 200 with error in body
        data = response.json()
        assert data["status"] == "error"
    
    def test_switch_control_get_mode(self, client):
        """Test getting current switch mode."""
        response = client.post(
            "/switch/control",
            json={"action": "get_mode"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "mode" in data
        assert "profile" in data
    
    def test_switch_control_list_modes(self, client):
        """Test listing all available modes."""
        response = client.post(
            "/switch/control",
            json={"action": "list_modes"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        assert "ECO" in data["modes"]
        assert "BALANCED" in data["modes"]
        assert "HIGH-PERF" in data["modes"]
        assert "CRITICAL" in data["modes"]


class TestHormigueroWorkerScaling:
    """Test hormiguero worker scaling control."""
    
    def test_hormiguero_scale_up(self, hormiguero_client):
        """Test scaling up worker count."""
        response = hormiguero_client.post(
            "/control",
            json={"action": "scale_workers", "target_count": 8}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["action"] == "scale_workers"
        assert data["target_count"] == 8
    
    def test_hormiguero_scale_down(self, hormiguero_client):
        """Test scaling down worker count."""
        response = hormiguero_client.post(
            "/control",
            json={"action": "scale_workers", "target_count": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["target_count"] == 2
    
    def test_hormiguero_get_metrics(self, hormiguero_client):
        """Test getting hormiguero metrics."""
        response = hormiguero_client.post(
            "/control",
            json={"action": "get_metrics"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "ants_count" in data
        assert "tasks_pending" in data
        assert "tasks_active" in data


class TestMetricsEndpoints:
    """Test metrics endpoints on all modules."""
    
    def test_switch_metrics_cpu(self, client):
        """Test switch CPU metrics endpoint."""
        response = client.get("/metrics/cpu")
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "cpu"
        assert "value" in data
        assert data["unit"] == "percent"
        assert 0 <= data["value"] <= 100
    
    def test_switch_metrics_memory(self, client):
        """Test switch memory metrics endpoint."""
        response = client.get("/metrics/memory")
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "memory"
        assert "value" in data
        assert data["unit"] == "percent"
        assert "available_mb" in data
    
    def test_switch_metrics_queue(self, client):
        """Test switch queue metrics endpoint."""
        response = client.get("/metrics/queue")
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "queue"
        assert "value" in data
        assert data["unit"] == "items"
    
    def test_switch_metrics_throughput(self, client):
        """Test switch throughput metrics endpoint."""
        response = client.get("/metrics/throughput")
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "throughput"
        assert "value" in data
        assert data["unit"] == "requests"
    
    def test_madre_metrics_endpoints(self, madre_client):
        """Test madre metrics endpoints are accessible."""
        endpoints = ["/metrics/cpu", "/metrics/memory", "/metrics/queue", "/metrics/throughput"]
        for endpoint in endpoints:
            response = madre_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert "metric" in data
            assert "value" in data
    
    def test_hormiguero_metrics_endpoints(self, hormiguero_client):
        """Test hormiguero metrics endpoints are accessible."""
        endpoints = ["/metrics/cpu", "/metrics/memory", "/metrics/queue", "/metrics/throughput"]
        for endpoint in endpoints:
            response = hormiguero_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert "metric" in data
            assert "value" in data


class TestModeProfileStructure:
    """Test mode profile structure and consistency."""
    
    def test_all_modes_have_profiles(self):
        """Test that all modes have defined profiles."""
        from switch.main import MODE_PROFILES
        
        modes = ["ECO", "BALANCED", "HIGH-PERF", "CRITICAL"]
        for mode in modes:
            assert mode in MODE_PROFILES
    
    def test_profile_keys(self):
        """Test that each profile has required keys."""
        from switch.main import MODE_PROFILES
        
        required_keys = {"preferred_providers", "timeout_ms", "max_workers"}
        for mode, profile in MODE_PROFILES.items():
            assert isinstance(profile, dict)
            assert required_keys.issubset(profile.keys())
    
    def test_profile_values_valid(self):
        """Test that profile values are valid types."""
        from switch.main import MODE_PROFILES
        
        for mode, profile in MODE_PROFILES.items():
            assert isinstance(profile["preferred_providers"], list)
            assert len(profile["preferred_providers"]) > 0
            assert isinstance(profile["timeout_ms"], int)
            assert profile["timeout_ms"] > 0
            assert isinstance(profile["max_workers"], int)
            assert profile["max_workers"] > 0
    
    def test_mode_progression_values(self):
        """Test that values progress logically from ECO to CRITICAL."""
        from switch.main import MODE_PROFILES
        
        modes = ["ECO", "BALANCED", "HIGH-PERF", "CRITICAL"]
        prev_timeout = 0
        prev_workers = 0
        
        for mode in modes:
            profile = MODE_PROFILES[mode]
            assert profile["timeout_ms"] >= prev_timeout
            assert profile["max_workers"] >= prev_workers
            prev_timeout = profile["timeout_ms"]
            prev_workers = profile["max_workers"]


class TestAdaptiveOptimizationIntegration:
    """Integration tests for the adaptive optimization cycle."""
    
    def test_mode_control_workflow(self, client):
        """Test complete mode control workflow."""
        # Get current mode
        get_response = client.post(
            "/switch/control",
            json={"action": "get_mode"}
        )
        assert get_response.status_code == 200
        original_mode = get_response.json()["mode"]
        
        # Change mode
        set_response = client.post(
            "/switch/control",
            json={"action": "set_mode", "mode": "HIGH-PERF"}
        )
        assert set_response.status_code == 200
        assert set_response.json()["mode"] == "HIGH-PERF"
        
        # Verify mode changed
        verify_response = client.post(
            "/switch/control",
            json={"action": "get_mode"}
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["mode"] == "HIGH-PERF"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
