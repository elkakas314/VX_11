import os
import pytest
import httpx
import json

"""
Madre Contract Tests (P0)

Validates:
- /health endpoint responsive
- /operator/power/status returns JSON (200 or 403 by policy)
- /operator/power/policy/solo_madre/status returns JSON

All calls via VX11_ENTRYPOINT (single entrypoint principle).
No destructive actions (GET/info only).
"""

ENTRYPOINT = (
    os.getenv("VX11_ENTRYPOINT") or os.getenv("BASE_URL") or "http://localhost:8000"
)
VX11_TOKEN = os.getenv("VX11_TOKEN") or "vx11-test-token"


@pytest.mark.asyncio
async def test_madre_health():
    """Madre health endpoint must be responsive via entrypoint."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{ENTRYPOINT}/health")
        assert resp.status_code == 200, f"Health failed: {resp.status_code}"
        data = resp.json()
        assert "status" in data, "Health response missing 'status'"


@pytest.mark.asyncio
async def test_madre_power_status():
    """Madre power status endpoint must return JSON (200 or 403 by policy)."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{ENTRYPOINT}/operator/power/status",
            headers={"X-VX11-Token": VX11_TOKEN},
        )
        assert resp.status_code in [200, 403], f"Unexpected status: {resp.status_code}"
        # Should always be JSON
        try:
            data = resp.json()
            assert isinstance(data, dict), "Response is not JSON object"
        except json.JSONDecodeError:
            pytest.fail(f"Response is not valid JSON: {resp.text[:100]}")


@pytest.mark.asyncio
async def test_madre_solo_madre_policy_status():
    """Madre solo_madre policy status endpoint."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{ENTRYPOINT}/operator/power/policy/solo_madre/status",
            headers={"X-VX11-Token": VX11_TOKEN},
        )
        assert resp.status_code in [
            200,
            403,
            404,
        ], f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            try:
                data = resp.json()
                assert isinstance(data, dict), "Response is not JSON object"
            except json.JSONDecodeError:
                pytest.fail(f"Response not JSON: {resp.text[:100]}")
        elif resp.status_code == 404:
            pytest.skip("Endpoint not available in this deployment")
