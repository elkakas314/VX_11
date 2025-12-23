"""
Test P0 for Rails Orchestrator (minimal contract verification)
"""

import pytest
from fastapi.testclient import TestClient
import sqlite3
import json
from pathlib import Path

# Import Manifestator app
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from manifestator.main import app
from config.rails_map_migrations import migrate as migrate_rails

client = TestClient(app)
DB_PATH = Path("./data/runtime/vx11.db")


class TestRailsMap:
    """Test RailsMap DB schema and endpoints."""

    @pytest.fixture(scope="class", autouse=True)
    def setup(self):
        """Ensure Rails schema is migrated."""
        migrate_rails()
        yield

    def test_rails_map_tables_exist(self):
        """Verify rails_map tables exist in DB."""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute(
            """
          SELECT name FROM sqlite_master 
          WHERE type='table' AND name LIKE 'rails_%'
        """
        )

        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        expected = [
            "rails_map_versions",
            "rails_lanes",
            "rails_flow_templates",
            "rails_container_blueprints",
            "rails_events",
        ]

        for table in expected:
            assert table in tables, f"Missing table: {table}"

    def test_get_rails_map_empty(self):
        """GET /manifestator/rails/map returns 404 if no data."""
        # Clean up any existing versions (simulate "empty" state)
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rails_map_versions")
        cursor.execute("DELETE FROM rails_lanes")
        cursor.execute("DELETE FROM rails_flow_templates")
        cursor.execute("DELETE FROM rails_container_blueprints")
        conn.commit()
        conn.close()

        response = client.get("/manifestator/rails/map")
        assert response.status_code == 404

    def test_post_rails_refresh_requires_token(self):
        """POST /manifestator/rails/refresh requires maintenance token."""
        response = client.post("/manifestator/rails/refresh", json={"reason": "test"})
        assert response.status_code == 403

    def test_post_rails_refresh_with_token(self):
        """POST /manifestator/rails/refresh succeeds with valid token."""
        response = client.post(
            "/manifestator/rails/refresh",
            json={"reason": "test", "correlation_id": "test-123"},
            headers={"x-maintenance-token": "MAINTENANCE_SECRET"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "new_version" in data
        assert "duration_ms" in data
        assert data["duration_ms"] >= 0

    def test_rails_events_audit_trail(self):
        """Verify rails_events records are created."""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute(
            """
          SELECT COUNT(*) FROM rails_events
        """
        )

        count = cursor.fetchone()[0]
        conn.close()

        # Should have at least migration + refresh events
        assert count >= 1


class TestManifestatorRailsIntegration:
    """Integration tests for Rails orchestrator."""

    def test_manifestator_endpoints_no_execute(self):
        """Verify Manifestator doesn't execute (returns planning-only)."""
        # All endpoints should return 2xx, never execute FS/Docker

        # GET /health (existing endpoint)
        response = client.get("/health")
        assert response.status_code == 200

        # GET /manifestator/rails/map (new planning endpoint)
        # Should not crash even if no data
        response = client.get("/manifestator/rails/map")
        assert response.status_code in [200, 404]  # Planning-only


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
