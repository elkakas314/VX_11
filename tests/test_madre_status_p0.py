"""
Tests for GET /madre/status endpoint (P0 #1).
Validates that /madre/status returns unified status with DB, canon, and services info.
"""

import pytest
import httpx
from config.settings import settings
from pathlib import Path


def test_madre_status_endpoint_exists():
    """Test that GET /madre/status endpoint exists and returns 200."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.get(f"http://127.0.0.1:{madre_port}/madre/status", timeout=3)
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            data = resp.json()
            assert isinstance(data, dict), "Response should be JSON object"
        except httpx.ConnectError:
            pytest.skip("Madre not running on port 8001")


def test_madre_status_schema():
    """Test that /madre/status response contains required keys."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.get(f"http://127.0.0.1:{madre_port}/madre/status", timeout=3)
            assert resp.status_code == 200
            data = resp.json()

            # Required top-level keys
            required_keys = [
                "module",
                "version",
                "mode",
                "services_expected",
                "services_running",
                "db",
                "canon",
                "timestamp",
            ]
            for key in required_keys:
                assert key in data, f"Missing required key: {key}"

            # Validate module name
            assert data["module"] == "madre"

            # Validate version format
            assert isinstance(data["version"], str)
            assert len(data["version"]) > 0

            # Validate mode
            assert data["mode"] in ["solo_madre", "window", "operative", "low_power"]

            # Validate db block
            assert isinstance(data["db"], dict)
            assert "path" in data["db"]
            assert "exists" in data["db"]
            assert "quick_check" in data["db"]
            assert "fk_violations" in data["db"]

            # Validate canon block
            assert isinstance(data["canon"], dict)
            assert "files" in data["canon"]
            assert isinstance(data["canon"]["files"], int)

            # Validate timestamp (ISO format with Z)
            assert "timestamp" in data
            assert data["timestamp"].endswith("Z")

        except httpx.ConnectError:
            pytest.skip("Madre not running")


def test_madre_status_db_integrity():
    """Test that DB info in /madre/status is accurate."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.get(f"http://127.0.0.1:{madre_port}/madre/status", timeout=3)
            assert resp.status_code == 200
            data = resp.json()

            db_info = data["db"]

            # DB should exist
            assert db_info["exists"] is True, "DB file should exist"

            # Quick check should return 'ok'
            assert (
                db_info["quick_check"] == "ok"
            ), f"DB quick_check failed: {db_info['quick_check']}"

            # FK violations should be 0
            assert (
                db_info["fk_violations"] == 0
            ), f"FK violations detected: {db_info['fk_violations']}"

            # DB size should be reasonable (> 100 KB)
            assert (
                db_info["size_bytes"] > 100000
            ), f"DB size too small: {db_info['size_bytes']}"

        except httpx.ConnectError:
            pytest.skip("Madre not running")


def test_madre_status_canon_files():
    """Test that canon block reflects actual docs/canon directory."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.get(f"http://127.0.0.1:{madre_port}/madre/status", timeout=3)
            assert resp.status_code == 200
            data = resp.json()

            canon_info = data["canon"]

            # Should have canon files
            assert canon_info["files"] > 0, "Should have at least 1 canon file"

            # Verify against actual directory if it exists
            canon_dir = Path("docs/canon")
            if canon_dir.exists():
                actual_files = list(canon_dir.glob("*.json"))
                assert canon_info["files"] == len(
                    actual_files
                ), f"Canon file count mismatch: reported {canon_info['files']}, actual {len(actual_files)}"

        except httpx.ConnectError:
            pytest.skip("Madre not running")


def test_madre_status_services_lists():
    """Test that services lists are present and reasonable."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.get(f"http://127.0.0.1:{madre_port}/madre/status", timeout=3)
            assert resp.status_code == 200
            data = resp.json()

            # Expected services list
            assert isinstance(data["services_expected"], list)
            assert len(data["services_expected"]) > 0

            # Running services list
            assert isinstance(data["services_running"], list)
            # In solo_madre mode, should have at least tentaculo_link or redis running

        except httpx.ConnectError:
            pytest.skip("Madre not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
