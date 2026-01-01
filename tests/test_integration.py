"""
tests/test_integration.py - End-to-end integration tests

Tests for:
- Full flow: intent → window → spawn → result polling
- Policy enforcement across modules
- Window state consistency
- Correlation ID tracking through flow
- Error propagation and recovery
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
    wm.close_window("switch", "test setup")
    wm.close_window("spawner", "test setup")
    yield


class TestE2EIntentFlow:
    """End-to-end intent submission flow"""

    def test_e2e_intent_no_window_requirement(self):
        """Intent without window requirement works with SOLO_MADRE"""
        resp = client.post(
            "/vx11/intent",
            json={
                "action": "status_check",
                "params": {"check_type": "health"},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should succeed or have defined error (not 403 off_by_policy)
        assert resp.status_code in [200, 202, 400, 404]
        assert resp.json().get("error") != "off_by_policy"

    def test_e2e_intent_requires_window(self):
        """Intent requiring window: closed → 403, open → allowed"""
        # Test 1: window closed → off_by_policy
        resp_closed = client.post(
            "/vx11/intent",
            json={
                "action": "spawner_task",
                "params": {"require_spawner": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_closed.status_code == 403
        assert resp_closed.json().get("error") == "off_by_policy"

        # Test 2: open window → allowed
        wm = get_window_manager()
        wm.open_window("spawner", 300, "e2e test")

        resp_open = client.post(
            "/vx11/intent",
            json={
                "action": "spawner_task",
                "params": {"require_spawner": True},
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should not be off_by_policy
        assert resp_open.json().get("error") != "off_by_policy"


class TestE2ESpawnFlow:
    """End-to-end spawn submission flow"""

    def test_e2e_spawn_complete_flow(self):
        """Complete spawn flow: open window → submit → get response"""
        wm = get_window_manager()

        # Step 1: Open window
        resp_open = client.post(
            "/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 300},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_open.status_code == 200
        window_state = resp_open.json()
        assert window_state.get("is_open") is True

        # Step 2: Query window status
        resp_status = client.get(
            "/vx11/window/status/spawner",
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_status.status_code == 200
        assert resp_status.json().get("is_open") is True

        # Step 3: Submit spawn task
        resp_spawn = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "print('e2e test')",
                "ttl_seconds": 60,
                "correlation_id": "e2e-spawn-001",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should not be 403 (error may come from spawner service, but not auth/policy)
        assert resp_spawn.status_code != 403
        if resp_spawn.status_code in [200, 202]:
            spawn_data = resp_spawn.json()
            assert "spawn_id" in spawn_data
            assert spawn_data.get("correlation_id") == "e2e-spawn-001"

        # Step 4: Close window
        resp_close = client.post(
            "/vx11/window/close",
            json={"target": "spawner", "reason": "flow complete"},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_close.status_code == 200
        assert resp_close.json().get("closed") is True

        # Step 5: Verify window closed
        resp_verify = client.get(
            "/vx11/window/status/spawner",
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_verify.json().get("is_open") is False

    def test_e2e_spawn_blocked_then_allowed(self):
        """Spawn: blocked (no window) → open window → allowed"""
        # Step 1: Try spawn with window closed
        resp_blocked = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_blocked.status_code == 403

        # Step 2: Open window
        wm = get_window_manager()
        wm.open_window("spawner", 300, "e2e test")

        # Step 3: Retry spawn
        resp_allowed = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "x=1",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should not be 403
        assert resp_allowed.status_code != 403


class TestE2EDualWindowFlow:
    """End-to-end flow with both windows"""

    def test_e2e_both_windows_required(self):
        """Intent requiring both switch + spawner windows"""
        # Step 1: Both closed → 403
        resp_both_closed = client.post(
            "/vx11/intent",
            json={
                "action": "combined_task",
                "params": {
                    "require_switch": True,
                    "require_spawner": True,
                },
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_both_closed.status_code == 403

        # Step 2: Open only spawner
        wm = get_window_manager()
        wm.open_window("spawner", 300, "e2e test")

        resp_one_open = client.post(
            "/vx11/intent",
            json={
                "action": "combined_task",
                "params": {
                    "require_switch": True,
                    "require_spawner": True,
                },
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Still 403 because switch is required but closed
        assert resp_one_open.status_code == 403

        # Step 3: Open both windows
        wm.open_window("switch", 300, "e2e test")

        resp_both_open = client.post(
            "/vx11/intent",
            json={
                "action": "combined_task",
                "params": {
                    "require_switch": True,
                    "require_spawner": True,
                },
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should be allowed (200 or routed to services)
        assert resp_both_open.json().get("error") != "off_by_policy"

    def test_e2e_window_status_consistency(self):
        """Window status queries remain consistent throughout flow"""
        wm = get_window_manager()

        # Open both windows
        wm.open_window("switch", 200, "consistency test")
        wm.open_window("spawner", 300, "consistency test")

        # Get status multiple times
        for _ in range(3):
            resp = client.get(
                "/vx11/window/status/switch",
                headers={"X-VX11-Token": "test-token-valid"},
            )
            assert resp.json().get("is_open") is True

            resp = client.get(
                "/vx11/window/status/spawner",
                headers={"X-VX11-Token": "test-token-valid"},
            )
            assert resp.json().get("is_open") is True


class TestE2ECorrelationTracking:
    """Correlation ID tracking across flow"""

    def test_e2e_correlation_preserved_through_spawn(self):
        """Correlation ID preserved from submission through response"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "e2e test")

        correlation_id = "e2e-corr-track-001"

        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "test()",
                "correlation_id": correlation_id,
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )

        if resp.status_code in [200, 202]:
            data = resp.json()
            # Correlation ID should be preserved in response
            assert data.get("correlation_id") == correlation_id

    def test_e2e_correlation_auto_generated(self):
        """Correlation ID auto-generated if not provided"""
        wm = get_window_manager()
        wm.open_window("spawner", 300, "e2e test")

        resp = client.post(
            "/vx11/spawn",
            json={
                "task_type": "python",
                "code": "test()",
            },
            headers={"X-VX11-Token": "test-token-valid"},
        )

        if resp.status_code in [200, 202]:
            data = resp.json()
            # Should have auto-generated correlation_id
            assert "correlation_id" in data
            assert len(data.get("correlation_id", "")) > 0


class TestE2EErrorRecovery:
    """Error handling and recovery in flows"""

    def test_e2e_recover_from_auth_error(self):
        """Auth error followed by correct auth"""
        # Step 1: Wrong token
        resp_wrong = client.post(
            "/vx11/spawn",
            json={"task_type": "python", "code": "x=1"},
            headers={"X-VX11-Token": "wrong-token"},
        )
        assert resp_wrong.status_code == 403

        # Step 2: Correct token
        wm = get_window_manager()
        wm.open_window("spawner", 300, "e2e recovery")

        resp_correct = client.post(
            "/vx11/spawn",
            json={"task_type": "python", "code": "x=1"},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should not be auth error
        assert resp_correct.status_code != 403

    def test_e2e_recover_from_policy_error(self):
        """Policy error followed by policy fix"""
        # Step 1: Window closed → off_by_policy
        resp_blocked = client.post(
            "/vx11/spawn",
            json={"task_type": "python", "code": "x=1"},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        assert resp_blocked.status_code == 403

        # Step 2: Open window and retry
        wm = get_window_manager()
        wm.open_window("spawner", 300, "e2e recovery")

        resp_allowed = client.post(
            "/vx11/spawn",
            json={"task_type": "python", "code": "x=1"},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should not be blocked by policy
        assert resp_allowed.status_code != 403
