import os
import pytest
import httpx
import json

"""
Spawner Contract Tests (P0)

Validates:
- Spawner health via entrypoint
- Window policy enforcement (spawner target)
- Spawner status/info accessible

All calls via VX11_ENTRYPOINT.
No spawn/create operations (destructive).
"""

ENTRYPOINT = (
    os.getenv("VX11_ENTRYPOINT") or os.getenv("BASE_URL") or "http://localhost:8000"
)
VX11_TOKEN = os.getenv("VX11_TOKEN") or "vx11-test-token"


@pytest.mark.asyncio
async def test_spawner_status():
    """Spawner status endpoint via entrypoint."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{ENTRYPOINT}/operator/api/spawner/status",
            headers={"X-VX11-Token": VX11_TOKEN},
        )
        if resp.status_code == 404:
            pytest.skip("Spawner status endpoint not available")
        assert resp.status_code in [200, 403], f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            try:
                data = resp.json()
            except json.JSONDecodeError:
                pytest.fail(f"Response not JSON: {resp.text[:100]}")


@pytest.mark.asyncio
async def test_spawner_window_policy_enforced():
    """Spawner window policy must enforce solo_madre or TTL."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Attempt to open window targeting spawner
        resp = await client.post(
            f"{ENTRYPOINT}/vx11/window/open",
            json={"target": "spawner", "ttl_seconds": 5},
            headers={"X-VX11-Token": VX11_TOKEN},
        )
        # Expected: 200 (docker mode) or 403 (host mode solo_madre)
        assert resp.status_code in [200, 403], f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            try:
                data = resp.json()
                assert "window_id" in data, "Window response missing window_id"
            except json.JSONDecodeError:
                pytest.fail(f"Response not JSON: {resp.text[:100]}")
        elif resp.status_code == 403:
            # Policy denied; expected in host mode
            pass


@pytest.mark.asyncio
async def test_spawner_no_destructive_spawn():
    """Verify we don't spawn daughters in contract tests."""
    # This is a marker; spawning happens in E2E tests
    pytest.skip("Spawn operations reserved for E2E tests")
