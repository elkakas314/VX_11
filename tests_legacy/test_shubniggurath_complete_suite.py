"""Comprehensive Shub test suite - All phases validation"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch


# ============== CORE PHASE TESTS ==============

class TestShubCoreInitialization:
    """Test Shub core initialization"""
    
    @pytest.mark.asyncio
    async def test_initializer_creates_components(self):
        from shubniggurath.core import ShubCoreInitializer
        
        config = {
            "reaper": {"host": "localhost", "port": 7899},
            "vx11": {"url": "http://switch:8002", "token": "test"},
        }
        
        initializer = ShubCoreInitializer(config)
        status = await initializer.initialize()
        
        assert status["status"] == "initialized"
        assert "components" in status


class TestDSPEngine:
    """Test DSP engine"""
    
    @pytest.mark.asyncio
    async def test_audio_analysis(self):
        import numpy as np
        from shubniggurath.core import DSPEngine
        
        engine = DSPEngine(sample_rate=48000)
        audio = np.random.randn(48000) * 0.1
        
        result = await engine.analyze_audio(audio)
        
        assert result.loudness_lufs < 0
        assert -50 < result.true_peak_dbfs < 0
        assert 0 < result.bpm < 300
        assert result.key in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


class TestEngineRegistry:
    """Test engine registry"""
    
    @pytest.mark.asyncio
    async def test_all_10_engines_registered(self):
        from shubniggurath.engines import EngineRegistry
        
        registry = EngineRegistry()
        engines = registry.list_engines()
        
        assert len(engines) == 10
        required = [
            "analyzer",
            "transient_detector",
            "eq_generator",
            "dynamics_processor",
            "stereo_processor",
            "fx_engine",
            "ai_recommender",
            "ai_mastering",
            "preset_generator",
            "batch_processor",
        ]
        for req in required:
            assert req in engines
    
    @pytest.mark.asyncio
    async def test_engine_processing(self):
        from shubniggurath.engines import EngineRegistry
        
        registry = EngineRegistry()
        result = await registry.process("analyzer", {"file_path": "/test.wav"})
        
        assert result.success
        assert result.engine_name == "analyzer"


# ============== VX11 INTEGRATION TESTS ==============

class TestVX11Integration:
    """Test VX11 module integrations"""
    
    @pytest.mark.asyncio
    async def test_switch_audio_router(self):
        from switch.switch_audio_router import ShubAudioRouter
        
        router = ShubAudioRouter({"token": "test", "shub_url": "http://localhost:8007"})
        
        characteristics = {"percussiveness": 0.8, "loudness": -20, "bpm": 150}
        engine = await router.select_best_engine(characteristics)
        
        assert engine == "transient_detector"
    
    @pytest.mark.asyncio
    async def test_hermes_shub_provider(self):
        from shubniggurath.integrations.hermes_shub_provider import ShubAudioProvider
        
        provider = ShubAudioProvider({})
        assert await provider.is_available()
        
        result = await provider.execute_operation("analyze", {})
        assert result["success"]
    
    @pytest.mark.asyncio
    async def test_madre_orchestration(self):
        from madre.madre_shub_orchestrator import MadreShubOrchestrator
        
        config = {"spawner_url": "http://spawner:8008", "token": "test"}
        orchestrator = MadreShubOrchestrator(config)
        
        stages = [{"engine": "analyzer", "params": {}}]
        pipeline_id = await orchestrator.create_audio_pipeline("t1", "p1", stages)
        
        assert pipeline_id is not None


class TestMCPIntegration:
    """Test MCP audio commands"""
    
    @pytest.mark.asyncio
    async def test_mcp_audio_command(self):
        from mcp.mcp_shub_bridge import MCPShubBridge
        
        bridge = MCPShubBridge({"shub_url": "http://localhost:8007", "token": "test"})
        
        result = await bridge.handle_audio_command("analyze my audio", {})
        assert "response" in result


# ============== DATABASE TESTS ==============

class TestDatabaseModels:
    """Test database models"""
    
    def test_tenant_model(self):
        from shubniggurath.database.models import Tenant
        
        tenant = Tenant(
            name="test_studio",
            studio_name="Test Studio",
            tier="pro",
            storage_quota_gb=500,
        )
        
        assert tenant.name == "test_studio"
        assert tenant.tier == "pro"


# ============== OPERATOR TESTS ==============

class TestOperatorShubDashboard:
    """Test Operator + Shub dashboard"""
    
    @pytest.mark.asyncio
    async def test_dashboard_endpoint(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from operator_backend.backend.shub_api import shub_router
        
        app = FastAPI()
        app.include_router(shub_router)
        client = TestClient(app)
        
        response = client.get("/operator/shub/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "engines" in data
    
    @pytest.mark.asyncio
    async def test_engines_health_endpoint(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from operator_backend.backend.shub_api import shub_router
        
        app = FastAPI()
        app.include_router(shub_router)
        client = TestClient(app)
        
        response = client.get("/operator/shub/engines/health")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10


# ============== DRIFT DETECTION TESTS ==============

class TestManifestatorDrift:
    """Test Manifestator drift detection"""
    
    @pytest.mark.asyncio
    async def test_drift_detector(self):
        from manifestator.manifestator_shub_bridge import ShubDriftDetector
        
        detector = ShubDriftDetector()
        report = detector.get_drift_report()
        
        assert "report_timestamp" in report
        assert "total_modules" in report


# ============== SYNC TESTS ==============

class TestBidirectionalSync:
    """Test VX11 ↔ Shub sync"""
    
    @pytest.mark.asyncio
    async def test_asset_sync(self):
        from shubniggurath.integrations.db_sync import BidirectionalSync
        
        sync = BidirectionalSync(None, None)
        
        result = await sync.sync_asset_to_shub("task-1", {
            "tenant_id": "t1",
            "file_path": "/test",
        })
        
        assert result is True


# ============== INTEGRATION TESTS ==============

class TestEndToEnd:
    """End-to-end workflow tests"""
    
    @pytest.mark.asyncio
    async def test_full_audio_pipeline(self):
        from madre.madre_shub_orchestrator import ShubAudioPipeline
        
        pipeline = ShubAudioPipeline("t1", "p1")
        pipeline.add_stage("analyzer", {})
        pipeline.add_stage("eq_generator", {})
        
        result = await pipeline.execute()
        
        assert result["successful"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
