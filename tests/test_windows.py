"""
tests/test_windows.py - Window management tests

Tests for:
- Opening windows (TTL tracking)
- Closing windows
- Checking window status
- TTL expiration
- Auto-cleanup on expired windows
- Window persistence checks
"""

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from tentaculo_link.main_v7 import app
from madre.window_manager import get_window_manager, Window

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_auth(monkeypatch):
    """Setup auth & reset windows"""
    monkeypatch.setenv("VX11_TENTACULO_LINK_TOKEN", "test-token-valid")
    wm = get_window_manager()
    wm.close_window("switch", "test setup")
    wm.close_window("spawner", "test setup")
    yield


class TestWindowOpen:
    """Test opening windows"""

    def test_open_window_spawner(self):
        """POST /vx11/window/open spawner → 200 with window state"""
        resp = client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 300},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_open") is True
        assert data.get("window_id") is not None
        # TTL can be 299-300 due to timing
        assert 299 <= data.get("ttl_remaining_seconds", 0) <= 300

    def test_open_window_switch(self):
        """POST /vx11/window/open switch → 200 with window state"""
        resp = client.post(
            "/vx11/window/open",
            json={"target": "switch", "ttl_seconds": 600},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_open") is True
        # TTL can be 599-600 due to timing
        assert 599 <= data.get("ttl_remaining_seconds", 0) <= 600

    def test_open_window_min_ttl(self):
        """POST /vx11/window/open with ttl_seconds=1 → 200"""
        resp = client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 1},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_open") is True

    def test_open_window_max_ttl(self):
        """POST /vx11/window/open with ttl_seconds=3600 → 200"""
        resp = client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 3600},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # TTL can be 3599-3600 due to timing
        assert 3599 <= data.get("ttl_remaining_seconds", 0) <= 3600

    def test_open_window_invalid_ttl_low(self):
        """POST /vx11/window/open with ttl_seconds=0 → 422"""
        resp = client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 0},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 422  # Validation error

    def test_open_window_invalid_ttl_high(self):
        """POST /vx11/window/open with ttl_seconds=3601 → 422"""
        resp = client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 3601},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 422  # Validation error

    def test_reopen_window_extends_ttl(self):
        """POST /vx11/window/open twice → second call extends TTL"""
        # First open
        resp1 = client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 100},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        ttl1 = resp1.json().get("ttl_remaining_seconds")

        # Second open with longer TTL
        resp2 = client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 500},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        ttl2 = resp2.json().get("ttl_remaining_seconds")

        # Second TTL should be closer to 500
        assert ttl2 > ttl1


class TestWindowClose:
    """Test closing windows"""

    def test_close_window_spawner(self):
        """POST /vx11/window/close spawner → 200 closed"""
        # First open
        client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 300},
            headers={"X-VX11-Token": "test-token-valid"},
        )

        # Then close
        resp = client.post(
            "/vx11/window/close",
            json={"target": "spawner", "reason": "manual"},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("closed") is True
        assert data.get("was_open") is True

    def test_close_window_already_closed(self):
        """POST /vx11/window/close already closed → 200 (idempotent)"""
        resp = client.post(
            "/vx11/window/close",
            json={"target": "spawner", "reason": "cleanup"},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # was_open should be False (already closed)
        assert data.get("was_open") is False

    def test_close_window_switch(self):
        """POST /vx11/window/close switch → 200 closed"""
        # Open first
        client.post(
            "/vx11/window/open",
            json={"target": "switch", "ttl_seconds": 200},
            headers={"X-VX11-Token": "test-token-valid"},
        )

        # Close
        resp = client.post(
            "/vx11/window/close",
            json={"target": "switch", "reason": "done"},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        assert resp.json().get("closed") is True


class TestWindowStatus:
    """Test querying window status"""

    def test_status_closed_window(self):
        """GET /vx11/window/status/spawner closed → is_open=false"""
        resp = client.get(
            "/vx11/window/status/spawner",
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_open") is False
        # ttl_remaining_seconds can be 0 or None when closed
        ttl = data.get("ttl_remaining_seconds")
        assert ttl == 0 or ttl is None

    def test_status_open_window(self):
        """GET /vx11/window/status/spawner open → is_open=true + ttl"""
        # Open first
        client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 250},
            headers={"X-VX11-Token": "test-token-valid"},
        )

        resp = client.get(
            "/vx11/window/status/spawner",
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_open") is True
        # TTL should be close to 250 (or less if time passed)
        assert data.get("ttl_remaining_seconds") > 0
        assert data.get("ttl_remaining_seconds") <= 250

    def test_status_includes_opened_at(self):
        """GET /vx11/window/status includes opened_at timestamp"""
        client.post(
            "/vx11/window/open",
            json={"target": "switch", "ttl_seconds": 300},
            headers={"X-VX11-Token": "test-token-valid"},
        )

        resp = client.get(
            "/vx11/window/status/switch",
            headers={"X-VX11-Token": "test-token-valid"},
        )
        data = resp.json()
        assert "opened_at" in data
        assert data.get("opened_at") is not None

    def test_status_includes_expires_at(self):
        """GET /vx11/window/status includes expires_at timestamp"""
        client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 100},
            headers={"X-VX11-Token": "test-token-valid"},
        )

        resp = client.get(
            "/vx11/window/status/spawner",
            headers={"X-VX11-Token": "test-token-valid"},
        )
        data = resp.json()
        assert "expires_at" in data
        assert data.get("expires_at") is not None

    def test_status_both_windows(self):
        """GET status for both windows"""
        client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 300},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        client.post(
            "/vx11/window/open",
            json={"target": "switch", "ttl_seconds": 200},
            headers={"X-VX11-Token": "test-token-valid"},
        )

        resp_spawner = client.get(
            "/vx11/window/status/spawner",
            headers={"X-VX11-Token": "test-token-valid"},
        )
        resp_switch = client.get(
            "/vx11/window/status/switch",
            headers={"X-VX11-Token": "test-token-valid"},
        )

        assert resp_spawner.json().get("is_open") is True
        assert resp_switch.json().get("is_open") is True


class TestWindowExpiration:
    """Test TTL expiration and cleanup"""

    def test_window_class_is_expired(self):
        """Window.is_expired() → true when TTL passed"""
        # Create window that expires immediately
        window = Window(
            target="spawner",
            ttl_seconds=0,  # Already expired
            reason="test",
        )
        # Manually set expired time
        window.expires_at = datetime.utcnow() - timedelta(seconds=1)

        assert window.is_expired() is True

    def test_window_class_ttl_remaining(self):
        """Window.ttl_remaining() → seconds until expiry"""
        window = Window(
            target="spawner",
            ttl_seconds=100,
            reason="test",
        )
        ttl = window.ttl_remaining()
        # Should be close to 100
        assert ttl > 0
        assert ttl <= 100

    def test_window_class_to_dict(self):
        """Window.to_dict() → valid dict representation"""
        window = Window(
            target="switch",
            ttl_seconds=200,
            reason="test",
        )
        data = window.to_dict()
        assert data.get("target") == "switch"
        assert data.get("is_open") is True
        assert "window_id" in data
        assert "ttl_remaining_seconds" in data

    def test_manager_cleanup_expired(self):
        """WindowManager.cleanup_expired_windows() removes expired"""
        wm = get_window_manager()

        # Open a window
        wm.open_window("spawner", 1, "test")

        # Wait for expiration
        time.sleep(1.5)

        # Cleanup should mark it as expired
        result = wm.cleanup_expired_windows()
        # result is Dict[str, bool]: {"switch": False, "spawner": True/False}
        assert result["spawner"] is True or not wm.is_window_open("spawner")
