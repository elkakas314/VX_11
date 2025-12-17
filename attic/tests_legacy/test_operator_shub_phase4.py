"""Test Operator + Shub integration"""

import pytest


@pytest.mark.asyncio
async def test_shub_dashboard():
    """Test dashboard endpoint"""
    from fastapi.testclient import TestClient
    from operator_backend.backend.shub_api import shub_router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(shub_router)
    
    client = TestClient(app)
    response = client.get("/operator/shub/dashboard")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "engines" in data


@pytest.mark.asyncio
async def test_engines_health():
    """Test engines health endpoint"""
    from fastapi.testclient import TestClient
    from operator_backend.backend.shub_api import shub_router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(shub_router)
    
    client = TestClient(app)
    response = client.get("/operator/shub/engines/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "analyzer" in data
    assert len(data) == 10  # 10 engines


@pytest.mark.asyncio
async def test_platform_stats():
    """Test platform stats endpoint"""
    from fastapi.testclient import TestClient
    from operator_backend.backend.shub_api import shub_router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(shub_router)
    
    client = TestClient(app)
    response = client.get("/operator/shub/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_assets" in data
    assert "total_projects" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
