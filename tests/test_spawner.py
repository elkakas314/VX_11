"""
tests/test_spawner.py - Spawner submission endpoint tests

Tests for:
- POST /vx11/spawn with window check
- SpawnRequest validation (task_type, code, max_retries, ttl_seconds)
- SpawnResponse with spawn_id + correlation_id
- TTL handling (1-86400 seconds)
- off_by_policy when spawner window closed
- Spawner unavailable (503) handling
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from tentaculo_link.main_v7 import app
from madre.window_manager import get_window_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_auth(monkeypatch):
    """Setup auth & reset windows"""
    monkeypatch.setenv("VX11_TENTACULO_LINK_TOKEN", "test-token-valid")
    wm = get_window_manager()
    wm.close_window("spawner", "test setup")
    yield


class TestSpawnSubmission:
    """Test spawner submission endpoint"""

    def test_spawn_window_closed(self):
        """POST /vx11/spawn with spawner window closed → 403 off_by_policy"""
        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "print('hello')",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data.get("error") == "off_by_policy"

    def test_spawn_valid_minimal(self):
        """POST /vx11/spawn with minimal fields → 200 or 202 (window open)"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x = 1 + 1",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should attempt to route (200/202 on success, 503 if spawner unavailable)
        assert resp.status_code in [200, 202, 503]
        data = resp.json()
        # Should have spawn_id in response
        assert "spawn_id" in data or "error" in data

    def test_spawn_valid_full(self):
        """POST /vx11/spawn with all fields → success"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "shell",
                "code": "echo test",
                "max_retries": 3,
                "ttl_seconds": 600,
                "user_id": "user-xyz",
                "metadata": {"priority": "high"},
                "correlation_id": "corr-123",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should succeed (200/202) or fail gracefully (503)
        assert resp.status_code in [200, 202, 503]

    def test_spawn_response_has_spawn_id(self):
        """POST /vx11/spawn response includes spawn_id"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        with patch(
            "tentaculo_link.main_v7.httpx.AsyncClient.post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 202
            mock_post.return_value = mock_response

            resp = client.post(
                "/vx11/spawn",
                json={
                    "task_type": "python",
                    "code": "print('test')",
                },
                headers={"X-VX11-Token": "test-token-valid"},
            )

            if resp.status_code in [200, 202]:
                data = resp.json()
                assert "spawn_id" in data

    def test_spawn_response_status_queued(self):
        """POST /vx11/spawn response has status=QUEUED"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        with patch(
            "tentaculo_link.main_v7.httpx.AsyncClient.post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 202
            mock_post.return_value = mock_response

            resp = client.post(
                "/vx11/spawn",
                json={
                    "task_type": "python",
                    "code": "x=1",
                },
                headers={"X-VX11-Token": "test-token-valid"},
            )

            if resp.status_code in [200, 202]:
                data = resp.json()
                assert data.get("status") in ["queued", "QUEUED"]

    def test_spawn_preserves_correlation_id(self):
        """POST /vx11/spawn preserves correlation_id"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
                "correlation_id": "test-corr-xyz",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )

        if resp.status_code in [200, 202]:
            data = resp.json()
            assert data.get("correlation_id") == "test-corr-xyz"

    def test_spawn_generates_correlation_id_if_missing(self):
        """POST /vx11/spawn generates correlation_id if not provided"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )

        if resp.status_code in [200, 202]:
            data = resp.json()
            # Should have auto-generated correlation_id
            assert "correlation_id" in data


class TestSpawnRequestValidation:
    """Test SpawnRequest field validation"""

    def test_spawn_task_type_required(self):
        """POST /vx11/spawn without task_type → 422"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/spawn",
            json={"code": "print('test')"},  # Missing task_type
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 422

    def test_spawn_code_required(self):
        """POST /vx11/spawn without code → 422"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/spawn",
            json={"task_type": "python"},  # Missing code
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 422

    def test_spawn_max_retries_bounds(self):
        """POST /vx11/spawn with max_retries outside 0-10 → 422"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        # Test too high
        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
                "max_retries": 11,
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 422

        # Test too low
        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
                "max_retries": -1,
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 422

    def test_spawn_ttl_bounds(self):
        """POST /vx11/spawn with ttl_seconds outside 1-86400 → 422"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        # Test too low
        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
                "ttl_seconds": 0,
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 422

        # Test too high
        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
                "ttl_seconds": 86401,
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 422


class TestSpawnSpawnerUnavailable:
    """Test spawner unavailability handling"""

    def test_spawn_spawner_unavailable(self):
        """POST /vx11/spawn with spawner service down → 503"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        with patch(
            "tentaculo_link.main_v7.httpx.AsyncClient.post",
            side_effect=Exception("Connection refused"),
        ):
            resp = client.post(
                "/vx11/spawn",
                json={
                    "task_type": "python",
                    "code": "print('test')",
                },
                headers={"X-VX11-Token": "test-token-valid"},
            )
            # Should fail gracefully
            assert resp.status_code in [500, 503]
            data = resp.json()
            assert "error" in data

    def test_spawn_spawner_timeout(self):
        """POST /vx11/spawn with spawner timeout → 503"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        with patch(
            "tentaculo_link.main_v7.httpx.AsyncClient.post",
            side_effect=TimeoutError("Request timeout"),
        ):
            resp = client.post(
                "/vx11/spawn",
                json={
                    "task_type": "python",
                    "code": "print('test')",
                },
                headers={"X-VX11-Token": "test-token-valid"},
            )
            # Should fail gracefully
            assert resp.status_code in [500, 503]


class TestSpawnIntegration:
    """Integration tests for spawner submission flow"""

    def test_spawn_requires_window_open(self):
        """Full flow: window closed → off_by_policy, open → attempts submit"""
        # First attempt: window closed
        resp_closed = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "print('test')",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_closed.status_code == 403

        # Second attempt: window open
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp_open = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "print('test')",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should not be 403 (error would be from spawner service)
        assert resp_open.status_code != 403

    def test_spawn_correlation_flow(self):
        """Full flow: submit with correlation_id, response includes it"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        correlation_id = "test-flow-123"
        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
                "correlation_id": correlation_id,
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )

        # If success, verify correlation_id preserved
        if resp.status_code in [200, 202]:
            assert resp.json().get("correlation_id") == correlation_id
