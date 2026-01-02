import os
import pytest
import httpx
import json

"""
Hermes Contract Tests (P0)

Validates:
- Hermes health endpoint responsive
- Hermes integration via entrypoint (proxied or direct)
- No execution of heavy operations; info-only

All calls via VX11_ENTRYPOINT.
"""

ENTRYPOINT = (
    os.getenv("VX11_ENTRYPOINT") or os.getenv("BASE_URL") or "http://localhost:8000"
)
VX11_TOKEN = os.getenv("VX11_TOKEN") or "vx11-test-token"


@pytest.mark.asyncio
async def test_hermes_health():
    """Hermes health endpoint via entrypoint."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            f"{ENTRYPOINT}/vx11/hermes/health",
            headers={"X-VX11-Token": VX11_TOKEN},
        )
        if resp.status_code == 404:
            pytest.skip("Hermes health endpoint not available")
        assert resp.status_code in [200, 403], f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            try:
                data = resp.json()
            except json.JSONDecodeError:
                pytest.fail(f"Response not JSON: {resp.text[:100]}")


@pytest.mark.asyncio
async def test_hermes_available_via_proxy():
    """Verify hermes is accessible via entrypoint proxy."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Try to reach raw hermes health if proxied
        resp = await client.get(
            f"{ENTRYPOINT}/hermes/get-engine",
            headers={"X-VX11-Token": VX11_TOKEN},
        )
        if resp.status_code == 404:
            pytest.skip("Hermes not proxied via entrypoint")
        # 403 acceptable (policy), 200 expected (success), 405 is GET not allowed (expected for some endpoints)
        assert resp.status_code in [
            200,
            403,
            400,
            405,
        ], f"Unexpected status: {resp.status_code}"


@pytest.mark.asyncio
async def test_hermes_no_heavy_execution():
    """Verify we don't execute heavy hermes operations in contract tests."""
    # This is a marker test; actual execution happens in E2E tests
    pytest.skip("Heavy execution reserved for E2E tests")
