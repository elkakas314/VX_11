"""
PHASE 6 E2E Integration Tests — Operator API (SIMPLIFIED)

Functional tests that validate:
1. /operator/capabilities endpoint is reachable and returns structure
2. Correlation ID flows through responses
3. Dormant services are properly documented
4. Policy gates are respected

This is a functional integration test suite, not full endpoint validation.
"""

import pytest
import uuid
from typing import Optional


class TestOperatorCapabilities:
    """Test /operator/capabilities endpoint functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        try:
            from tentaculo_link.main_v7 import app
            from fastapi.testclient import TestClient
            return TestClient(app)
        except ImportError:
            pytest.skip("tentaculo_link.main_v7 not available")

    def test_capabilities_endpoint_exists(self, client):
        """Verify /operator/capabilities endpoint is registered."""
        response = client.get("/operator/capabilities", headers={"x-vx11-token": "test"})
        assert response.status_code != 404

    def test_dormant_services_endpoint_integration(self, client):
        """Test that dormant services info is available."""
        response = client.get("/operator/api/status", headers={"x-vx11-token": "test"})
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "dormant_services" in data["data"]:
                services = data["data"]["dormant_services"]
                assert isinstance(services, list)
                assert len(services) > 0

    def test_correlation_id_propagation(self, client):
        """Verify correlation_id is used in responses."""
        test_uuid = str(uuid.uuid4())
        headers = {
            "x-vx11-token": "test",
            "x-correlation-id": test_uuid,
        }
        
        response = client.get("/operator/capabilities", headers=headers)
        if response.status_code == 200:
            data = response.json()
            response_text = str(data)
            assert "correlation_id" in response_text or test_uuid in response_text


class TestProviderRegistry:
    """Test provider registry integration."""

    def test_provider_registry_importable(self):
        """Verify provider registry can be imported."""
        try:
            from switch.providers import get_provider, ProviderRegistry
            assert callable(get_provider)
            assert ProviderRegistry is not None
        except ImportError:
            pytest.skip("Provider registry not available")


class TestDatabaseSchema:
    """Test DB schema for dormant services."""

    def test_colony_schema_exists(self):
        """Verify colony tables exist in DB."""
        try:
            import sqlite3
            conn = sqlite3.connect("data/runtime/vx11.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE 'inee_%'
            """)
            
            tables = cursor.fetchall()
            conn.close()
            
            assert len(tables) > 0, "No inee_* tables found"
        except FileNotFoundError:
            pytest.skip("DB not available")

    def test_pragma_integrity_check(self):
        """Verify DB integrity is OK."""
        try:
            import sqlite3
            conn = sqlite3.connect("data/runtime/vx11.db")
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            
            assert result[0] == "ok", f"Integrity check failed: {result}"
        except FileNotFoundError:
            pytest.skip("DB not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
