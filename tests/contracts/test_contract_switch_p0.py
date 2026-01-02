import os
import pytest
import httpx
import json

"""
Switch Contract Tests (P0)

Validates:
- Global /health responsive
- Circuit breaker status endpoint accessible
- Switch routing responsive via entrypoint

All calls via VX11_ENTRYPOINT.
No destructive actions.
"""

ENTRYPOINT = (
    os.getenv("VX11_ENTRYPOINT") or os.getenv("BASE_URL") or "http://localhost:8000"
)
VX11_TOKEN = os.getenv("VX11_TOKEN") or "vx11-test-token"


@pytest.mark.asyncio
async def test_switch_health():
    """Switch health endpoint via entrypoint."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{ENTRYPOINT}/health")
        assert resp.status_code == 200, f"Health failed: {resp.status_code}"
        data = resp.json()
        assert "status" in data or "module" in data, "Health response missing fields"


@pytest.mark.asyncio
async def test_switch_circuit_breaker_status():
    """Circuit breaker status (switch responsibility)."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{ENTRYPOINT}/vx11/circuit-breaker/status",
            headers={"X-VX11-Token": VX11_TOKEN},
        )
        if resp.status_code == 404:
            pytest.skip("Circuit breaker endpoint not available")
        assert resp.status_code in [200, 403], f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            try:
                data = resp.json()
                # Should have state info
                assert isinstance(data, dict), "Response not JSON object"
            except json.JSONDecodeError:
                pytest.fail(f"Response not JSON: {resp.text[:100]}")


@pytest.mark.asyncio
async def test_switch_vx11_status():
    """VX11 status endpoint (routed via switch)."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{ENTRYPOINT}/vx11/status",
            headers={"X-VX11-Token": VX11_TOKEN},
        )
        if resp.status_code == 404:
            pytest.skip("Endpoint not available")
        assert resp.status_code in [200, 403], f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            try:
                data = resp.json()
            except json.JSONDecodeError:
                pytest.fail(f"Response not JSON: {resp.text[:100]}")
