"""
Tests for spawner service.
"""

import pytest
import httpx
import time
from config.settings import settings


@pytest.fixture
def spawner_url():
    spawner_port = settings.PORTS.get("spawner", 8008)
    return f"http://127.0.0.1:{spawner_port}"


def test_spawner_health():
    """Test spawner health endpoint."""
    with httpx.Client() as client:
        try:
            spawner_port = settings.PORTS.get("spawner", 8008)
            resp = client.get(f"http://127.0.0.1:{spawner_port}/health", timeout=2)
            assert resp.status_code == 200
            data = resp.json()
            assert data["module"] == "spawner"
            assert data["status"] == "ok"
        except httpx.ConnectError:
            pytest.skip("Spawner not running")


def test_spawner_spawn_echo():
    """Test spawning a simple echo process."""
    with httpx.Client() as client:
        try:
            spawner_port = settings.PORTS.get("spawner", 8008)
            resp = client.post(
                f"http://127.0.0.1:{spawner_port}/spawn",
                json={"name": "test-echo", "cmd": "echo", "args": ["hello"]},
                timeout=5,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "started"
            assert "id" in data
            assert data["pid"] is not None
        except httpx.ConnectError:
            pytest.skip("Spawner not running")


def test_spawner_list():
    """Test listing spawned processes."""
    with httpx.Client() as client:
        try:
            spawner_port = settings.PORTS.get("spawner", 8008)
            resp = client.get(f"http://127.0.0.1:{spawner_port}/spawns", timeout=5)
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
        except httpx.ConnectError:
            pytest.skip("Spawner not running")


def test_spawner_get_spawn():
    """Test getting spawn status."""
    with httpx.Client() as client:
        try:
            spawner_port = settings.PORTS.get("spawner", 8008)
            # Spawn first
            spawn_resp = client.post(
                f"http://127.0.0.1:{spawner_port}/spawn",
                json={"name": "test-sleep", "cmd": "sleep", "args": ["1"]},
                timeout=5,
            )
            spawn_id = spawn_resp.json()["id"]
            
            # Get status
            resp = client.get(f"http://127.0.0.1:{spawner_port}/spawn/{spawn_id}", timeout=5)
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == spawn_id
            assert "running" in data
        except httpx.ConnectError:
            pytest.skip("Spawner not running")


def test_spawner_stop():
    """Test stopping a spawned process."""
    with httpx.Client() as client:
        try:
            spawner_port = settings.PORTS.get("spawner", 8008)
            # Spawn
            spawn_resp = client.post(
                f"http://127.0.0.1:{spawner_port}/spawn",
                json={"name": "test-long", "cmd": "sleep", "args": ["10"]},
                timeout=5,
            )
            spawn_id = spawn_resp.json()["id"]
            
            # Stop
            stop_resp = client.post(
                f"http://127.0.0.1:{spawner_port}/stop/{spawn_id}",
                timeout=5,
            )
            assert stop_resp.status_code == 200
            data = stop_resp.json()
            assert data["status"] == "stopped"
        except httpx.ConnectError:
            pytest.skip("Spawner not running")
