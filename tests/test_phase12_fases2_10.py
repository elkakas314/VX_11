"""
FASE 12: Automated Test Suite v6.2
Tests de integración para todas las FASEs implementadas
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("VX11_RUN_INTEGRATION"),
    reason="integration tests require running services"
)
import asyncio
import json
from typing import Dict, Any
import httpx

# Endpoints base
TENTACULO = "http://127.0.0.1:8000"
MADRE = "http://127.0.0.1:52112"
SWITCH = "http://127.0.0.1:52113"
HERMES = "http://127.0.0.1:52114"
HORMIGUERO = "http://127.0.0.1:52115"
MCP = "http://127.0.0.1:52116"
SHUB = "http://127.0.0.1:52117"


class TestContext7Implementation:
    """Tests para Context-7 (FASE 2)"""
    
    @pytest.mark.asyncio
    async def test_context7_in_madre_chat(self):
        """Valida que madre/chat acepte y valide context-7"""
        async with httpx.AsyncClient() as client:
            payload = {
                "messages": [{"role": "user", "content": "Test"}],
                "context7": {
                    "layer1_user": {"user_id": "test"},
                    "layer2_session": {"session_id": "test-session"},
                    "layer3_task": {"task_id": "test-task", "task_type": "test"},
                    "layer4_environment": {"os": "linux", "vx_version": "6.2"},
                    "layer5_security": {"auth_level": "user"},
                    "layer6_history": {"recent_commands": []},
                    "layer7_meta": {"mode": "balanced"},
                }
            }
            
            resp = await client.post(f"{MADRE}/chat", json=payload, timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") in ["ok", "error"]


class TestScoringEngine:
    """Tests para Scoring (FASE 3)"""
    
    @pytest.mark.asyncio
    async def test_switch_scoring_query(self):
        """Valida endpoint /switch/query con scoring"""
        async with httpx.AsyncClient() as client:
            payload = {
                "query": "Test query",
                "context7": {
                    "layer7_meta": {"mode": "balanced"}
                }
            }
            
            resp = await client.post(f"{SWITCH}/switch/query", json=payload, timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"
            assert "engine_selected" in data
            assert "score" in data


class TestPheromoneEngine:
    """Tests para Pheromone Engine (FASE 4)"""
    
    @pytest.mark.asyncio
    async def test_pheromone_update(self):
        """Valida actualización de feromonas"""
        async with httpx.AsyncClient() as client:
            payload = {
                "engine_id": "local_gguf_small",
                "outcome": "success"
            }
            
            resp = await client.post(f"{SWITCH}/switch/pheromone/update", json=payload, timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"
            assert "new_value" in data
    
    @pytest.mark.asyncio
    async def test_pheromone_summary(self):
        """Valida resumen de feromonas"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{SWITCH}/switch/pheromone/summary", timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"
            assert "data" in data


class TestGeneticAlgorithm:
    """Tests para Genetic Algorithm (FASE 5)"""
    
    @pytest.mark.asyncio
    async def test_ga_optimize(self):
        """Valida optimización GA en hormiguero"""
        async with httpx.AsyncClient() as client:
            payload = {
                "engine_id": "local_gguf_small",
                "steps": 1
            }
            
            resp = await client.post(f"{HORMIGUERO}/hormiguero/ga/optimize", json=payload, timeout=15)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"
            assert "generations" in data
    
    @pytest.mark.asyncio
    async def test_ga_summary(self):
        """Valida resumen GA"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{HORMIGUERO}/hormiguero/ga/summary", timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"


class TestPlaywright:
    """Tests para Playwright (FASE 6)"""
    
    @pytest.mark.asyncio
    async def test_playwright_navigate(self):
        """Valida endpoint Playwright"""
        async with httpx.AsyncClient() as client:
            payload = {
                "url": "https://example.com",
                "action": "navigate",
                "context7": {
                    "layer5_security": {"auth_level": "admin"}
                }
            }
            
            resp = await client.post(f"{HERMES}/hermes/playwright", json=payload, timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"


class TestOrchestration:
    """Tests para Orquestación (FASE 7)"""
    
    @pytest.mark.asyncio
    async def test_orchestration_quick(self):
        """Valida pipeline rápido de orquestación"""
        async with httpx.AsyncClient() as client:
            payload = {
                "query": "Test query",
                "pipeline_type": "quick"
            }
            
            resp = await client.post(f"{TENTACULO}/vx11/orchestrate", json=payload, timeout=20)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"


class TestMCPBridge:
    """Tests para MCP Bridge (FASE 8)"""
    
    @pytest.mark.asyncio
    async def test_mcp_list_tools(self):
        """Valida LIST_TOOLS en MCP"""
        async with httpx.AsyncClient() as client:
            payload = {
                "method": "LIST_TOOLS",
                "resource": "/mcp/tools"
            }
            
            resp = await client.post(f"{MCP}/mcp/copilot-bridge", json=payload, timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"
            assert "tools" in data
    
    @pytest.mark.asyncio
    async def test_mcp_post_chat(self):
        """Valida POST /chat en MCP"""
        async with httpx.AsyncClient() as client:
            payload = {
                "method": "POST",
                "resource": "/mcp/chat",
                "params": {
                    "message": "Test",
                    "session_id": "test-session"
                }
            }
            
            resp = await client.post(f"{MCP}/mcp/copilot-bridge", json=payload, timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"


class TestCopilotValidation:
    """Tests para Copilot Validation (FASE 9)"""
    
    @pytest.mark.asyncio
    async def test_copilot_bridge_validation(self):
        """Valida suite de validación Copilot"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{TENTACULO}/vx11/validate/copilot-bridge", timeout=30)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"
            assert "validation_results" in data


class TestShubniggurath:
    """Tests para Shubniggurath (FASE 10)"""
    
    @pytest.mark.asyncio
    async def test_shub_copilot_status(self):
        """Valida estado Copilot-Shubniggurath"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{SHUB}/shub/copilot-status", timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"
            assert "shub_status" in data
    
    @pytest.mark.asyncio
    async def test_shub_copilot_prepare_activate(self):
        """Valida activación a STANDBY"""
        async with httpx.AsyncClient() as client:
            payload = {
                "action": "activate"
            }
            
            resp = await client.post(f"{SHUB}/shub/copilot-prepare", json=payload, timeout=10)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "ok"


class TestHealthAndControl:
    """Tests para endpoints obligatorios"""
    
    @pytest.mark.asyncio
    async def test_all_modules_health(self):
        """Valida /health en todos los módulos"""
        modules = {
            "tentaculo_link": TENTACULO,
            "madre": MADRE,
            "switch": SWITCH,
            "hermes": HERMES,
            "hormiguero": HORMIGUERO,
            "mcp": MCP,
            "shub": SHUB,
        }
        
        async with httpx.AsyncClient() as client:
            for name, endpoint in modules.items():
                resp = await client.get(f"{endpoint}/health", timeout=5)
                assert resp.status_code == 200, f"{name} /health failed"


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "-s"])
