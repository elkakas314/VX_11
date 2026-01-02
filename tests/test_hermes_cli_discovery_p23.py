"""
P2.3 Testing: CLI discovery and catalog endpoints
Tests:
- POST /vx11/hermes/discover (CLI scanning + registration)
- GET /vx11/hermes/catalog (unified models + providers)
"""

import pytest
import httpx
import asyncio
from datetime import datetime
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
DISCOVER_ENDPOINT = f"{BASE_URL}/vx11/hermes/discover"
CATALOG_ENDPOINT = f"{BASE_URL}/vx11/hermes/catalog"

VALID_TOKEN = "vx11-test-token"
HEADERS = {"X-VX11-Token": VALID_TOKEN}


@pytest.mark.asyncio
async def test_hermes_discover_endpoint():
    """Test POST /vx11/hermes/discover endpoint"""
    async with httpx.AsyncClient(timeout=30) as client:
        # First, call discover with plan=False (dry run)
        response = await client.post(
            DISCOVER_ENDPOINT,
            json={"apply": False, "allow_web": False},
            headers=HEADERS,
        )
        assert response.status_code == 200, f"Discover plan failed: {response.text}"
        data = response.json()
        assert data["status"] == "plan"
        assert "plan" in data
        assert "cli" in data["plan"]["tiers"]
        print(f"✓ Discover plan OK: tiers={data['plan']['tiers']}")

        # Now, call discover with apply=True (actual scanning + registration)
        response = await client.post(
            DISCOVER_ENDPOINT, json={"apply": True, "allow_web": False}, headers=HEADERS
        )
        assert response.status_code == 200, f"Discover apply failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        assert data["apply"] == True
        assert "tier4_cli" in data["results"]
        cli_binaries = data["results"]["tier4_cli"]
        print(f"✓ Discover apply OK: {len(cli_binaries)} CLIs discovered")

        # Verify at least some CLIs were discovered
        if cli_binaries:
            assert "name" in cli_binaries[0]
            assert "path" in cli_binaries[0]
            print(f"  → Sample CLIs: {[c['name'] for c in cli_binaries[:3]]}")


@pytest.mark.asyncio
async def test_hermes_catalog_endpoint():
    """Test GET /vx11/hermes/catalog endpoint"""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(CATALOG_ENDPOINT, headers=HEADERS)
        assert response.status_code == 200, f"Catalog failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok"
        assert "models" in data
        assert "providers" in data
        print(
            f"✓ Catalog OK: {data['total_models']} models, {data['total_providers']} providers"
        )

        # Verify structure
        if data["providers"]:
            provider = data["providers"][0]
            assert "type" in provider
            assert provider["type"] == "provider"
            print(f"  → Sample providers: {[p['name'] for p in data['providers'][:3]]}")


@pytest.mark.asyncio
async def test_cli_registration_in_db():
    """Test that CLIs are actually registered in DB"""
    from config.db_schema import CLIProvider, get_session

    async with httpx.AsyncClient(timeout=30) as client:
        # Call discover to populate DB
        response = await client.post(
            DISCOVER_ENDPOINT, json={"apply": True, "allow_web": False}, headers=HEADERS
        )
        assert response.status_code == 200

        # Query DB to verify registration
        db = get_session("vx11")
        try:
            providers = db.query(CLIProvider).all()
            print(f"✓ CLI providers in DB: {len(providers)} registered")

            if providers:
                for p in providers[:3]:
                    print(f"  → {p.name}: enabled={p.enabled}, tasks={p.task_types}")
        finally:
            db.close()


@pytest.mark.asyncio
async def test_discover_plan_vs_apply():
    """Test discover endpoint with plan vs apply"""
    async with httpx.AsyncClient(timeout=30) as client:
        # Plan (dry run)
        response_plan = await client.post(
            DISCOVER_ENDPOINT,
            json={"apply": False, "allow_web": False},
            headers=HEADERS,
        )
        assert response_plan.status_code == 200
        data_plan = response_plan.json()
        assert data_plan["status"] == "plan"
        assert data_plan["db_write"] == "skipped"
        print(f"✓ Plan: db_write=skipped")

        # Apply (actual changes)
        response_apply = await client.post(
            DISCOVER_ENDPOINT, json={"apply": True, "allow_web": False}, headers=HEADERS
        )
        assert response_apply.status_code == 200
        data_apply = response_apply.json()
        assert data_apply["status"] == "ok"
        assert data_apply["db_write"] == "ok"
        print(f"✓ Apply: db_write=ok")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
