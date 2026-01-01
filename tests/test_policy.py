"""
tests/test_policy.py - Policy enforcement tests (off_by_policy semantics)

Tests for:
- off_by_policy when switch window closed
- off_by_policy when spawner window closed
- Window-aware routing (if window open → allow)
- Error hints include window open instructions
"""

import pytest
from fastapi.testclient import TestClient
from tentaculo_link.main_v7 import app
from madre.window_manager import get_window_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_auth(monkeypatch):
    """Setup auth & reset windows"""
    monkeypatch.setenv("VX11_TENTACULO_LINK_TOKEN", "test-token-valid")
    wm = get_window_manager()
    # Close all windows
    wm.close_window("switch", "test setup")
    wm.close_window("spawner", "test setup")
    yield


class TestOffByPolicySwitch:
    """Test off_by_policy enforcement for switch service"""

    def test_intent_require_switch_window_closed(self):
        """POST /vx11/intent with require.switch=true & switch window closed → 403 off_by_policy"""
        resp = client.post(
            "/vx11/intent",
            json={
                "intent_type": "chat",
                "text": "switch command",
                "require": {"switch": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should be off_by_policy (403) since window is closed
        assert resp.status_code == 403
        data = resp.json()
        assert data.get("error") == "off_by_policy"

    def test_intent_require_switch_window_open(self):
        """POST /vx11/intent with require.switch=true & switch window open → 200 or routed"""
        wm = get_window_manager()
        # Open switch window
        wm.open_window("switch", 300, "test")

        resp = client.post(
            "/vx11/intent",
            json={
                "action": "switch_action",
                "params": {"require_switch": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Window is open, so should be allowed (200 or routed)
        assert resp.status_code in [
            200,
            202,
            400,
        ]  # 400 may come from switch service, but not 403
        data = resp.json()
        assert data.get("error") != "off_by_policy"

    def test_intent_no_require_switch(self):
        """POST /vx11/intent without require.switch → no off_by_policy"""
        resp = client.post(
            "/vx11/intent",
            json={
                "action": "generic_action",
                "params": {},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # No require.switch, so should not be off_by_policy
        assert resp.status_code != 403 or resp.json().get("error") != "off_by_policy"


class TestOffByPolicySpawner:
    """Test off_by_policy enforcement for spawner service"""

    def test_spawn_window_closed(self):
        """POST /vx11/spawn with spawner window closed → 403 off_by_policy"""
        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "print('test')",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data.get("error") == "off_by_policy"
        assert "spawner" in data.get("reason", "").lower()
        assert "window" in data.get("hint", "").lower()

    def test_spawn_window_open(self):
        """POST /vx11/spawn with spawner window open → 200 or 202 (not 403)"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "print('test')",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Window open → should attempt to route to spawner
        # May fail with 503 (spawner unavailable) but NOT 403 off_by_policy
        assert resp.status_code != 403 or resp.json().get("error") != "off_by_policy"

    def test_spawn_error_hint_correct_target(self):
        """off_by_policy error includes correct target in hint"""
        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "print('test')",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        data = resp.json()
        hint = data.get("hint", "")
        # Should include JSON with target="spawner"
        assert "spawner" in hint.lower()


class TestOffByPolicyIntent:
    """Test off_by_policy enforcement in /vx11/intent"""

    def test_intent_require_spawner_window_closed(self):
        """POST /vx11/intent with require.spawner=true & spawner window closed → 403 off_by_policy"""
        resp = client.post(
            "/vx11/intent",
            json={
                "action": "spawner_action",
                "params": {"require_spawner": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data.get("error") == "off_by_policy"
        assert "spawner" in data.get("reason", "").lower()

    def test_intent_require_spawner_window_open(self):
        """POST /vx11/intent with require.spawner=true & spawner window open → allowed"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/intent",
            json={
                "action": "spawner_action",
                "params": {"require_spawner": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Window open → should be allowed
        assert resp.status_code != 403 or resp.json().get("error") != "off_by_policy"

    def test_intent_require_both_switches(self):
        """POST /vx11/intent with require.switch=true & require.spawner=true, windows closed → 403"""
        resp = client.post(
            "/vx11/intent",
            json={
                "action": "combined_action",
                "params": {"require_switch": True, "require_spawner": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data.get("error") == "off_by_policy"

    def test_intent_require_both_switches_both_open(self):
        """POST /vx11/intent with require.switch=true & require.spawner=true, windows open → allowed"""
        wm = get_window_manager()
        wm.open_window("switch", 300, "test")
        wm.open_window("spawner", 300, "test")

        resp = client.post(
            "/vx11/intent",
            json={
                "action": "combined_action",
                "params": {"require_switch": True, "require_spawner": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Both windows open → should be allowed
        assert resp.status_code != 403 or resp.json().get("error") != "off_by_policy"

    def test_intent_require_switch_open_spawner_closed(self):
        """POST /vx11/intent require.switch=true (open) & require.spawner=true (closed) → 403"""
        wm = get_window_manager()
        wm.open_window("switch", 300, "test")
        wm.close_window("spawner", "test")

        resp = client.post(
            "/vx11/intent",
            json={
                "action": "action",
                "params": {"require_switch": True, "require_spawner": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # spawner required but closed → 403
        assert resp.status_code == 403
        data = resp.json()
        assert data.get("error") == "off_by_policy"
