"""
tests/test_shub_core.py — Tests de Módulos Core Shub

Valida:
- REAPER RPC integration
- VX11 Bridge communication
- Batch Engine operations
- Virtual Engineer decision logic
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import json
from datetime import datetime

# Importar módulos Shub
from shubniggurath.integrations.reaper_rpc import REAPERController
from shubniggurath.integrations.vx11_bridge import VX11Bridge
from shubniggurath.core.audio_batch_engine import AudioBatchEngine, BatchJob
from shubniggurath.core.virtual_engineer import VirtualEngineer


class TestREAPERController:
    """Tests del controlador REAPER"""
    
    @pytest.fixture
    def reaper_controller(self):
        """Crear instancia de REAPERController"""
        return REAPERController(reaper_host="localhost", reaper_port=7899)
    
    @pytest.mark.asyncio
    async def test_reaper_controller_initialization(self, reaper_controller):
        """Test: Inicialización del controlador REAPER"""
        assert reaper_controller is not None
        assert reaper_controller.reaper_host == "localhost"
        assert reaper_controller.reaper_port == 7899
        assert reaper_controller.endpoint == "http://localhost:7899/api"
    
    @pytest.mark.asyncio
    async def test_reaper_12_methods_exist(self, reaper_controller):
        """Test: Verificar que existan los 12 métodos canónicos"""
        methods = [
            'list_projects',
            'load_project',
            'analyze_project',
            'list_tracks',
            'list_items',
            'list_fx',
            'apply_fx_chain',
            'render_master',
            'update_project_metadata',
            'send_shub_status_to_reaper',
            'auto_mix',
            'auto_master'
        ]
        
        for method_name in methods:
            assert hasattr(reaper_controller, method_name), f"Missing method: {method_name}"
    
    @pytest.mark.asyncio
    async def test_reaper_http_call_error_handling(self, reaper_controller):
        """Test: Error handling en llamadas HTTP"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Simulate health check failure
            health = await reaper_controller.health_check()
            assert health['status'] == 'disconnected'
    
    @pytest.mark.asyncio
    async def test_reaper_cleanup(self, reaper_controller):
        """Test: Cleanup de recursos"""
        await reaper_controller._ensure_client()
        await reaper_controller.cleanup()
        assert reaper_controller.http_client is None


class TestVX11Bridge:
    """Tests del puente VX11"""
    
    @pytest.fixture
    def vx11_bridge(self):
        """Crear instancia de VX11Bridge"""
        return VX11Bridge()
    
    @pytest.mark.asyncio
    async def test_vx11_bridge_initialization(self, vx11_bridge):
        """Test: Inicialización de VX11Bridge"""
        assert vx11_bridge is not None
        assert "madre" in vx11_bridge.madre_url or "http" in vx11_bridge.madre_url
        assert "switch" in vx11_bridge.switch_url or "http" in vx11_bridge.switch_url
        assert "hormiguero" in vx11_bridge.hormiguero_url or "http" in vx11_bridge.hormiguero_url
    
    @pytest.mark.asyncio
    async def test_vx11_bridge_9_methods_exist(self, vx11_bridge):
        """Test: Verificar que existan los 9 métodos canónicos"""
        methods = [
            'analyze',
            'mastering',
            'batch_submit',
            'batch_status',
            'report_issue_to_hormiguero',
            'notify_madre',
            'notify_switch',
            'notify_hijas',
            'health_cascade_check'
        ]
        
        for method_name in methods:
            assert hasattr(vx11_bridge, method_name), f"Missing method: {method_name}"
    
    @pytest.mark.asyncio
    async def test_http_client_initialization(self, vx11_bridge):
        """Test: Cliente HTTP se inicializa bajo demanda"""
        assert vx11_bridge.http_client is None
        await vx11_bridge._ensure_client()
        assert vx11_bridge.http_client is not None


class TestAudioBatchEngine:
    """Tests del motor de procesamiento por lotes"""
    
    @pytest.fixture
    def batch_engine(self):
        """Crear instancia de AudioBatchEngine"""
        return AudioBatchEngine()
    
    @pytest.mark.asyncio
    async def test_batch_engine_initialization(self, batch_engine):
        """Test: Inicialización del batch engine"""
        assert batch_engine is not None
        assert hasattr(batch_engine, 'jobs')
        assert hasattr(batch_engine, 'queue')
    
    @pytest.mark.asyncio
    async def test_batch_job_dataclass_creation(self):
        """Test: Crear instancia de BatchJob"""
        job = BatchJob(
            job_id="test_job_001",
            audio_files=["file1.wav", "file2.wav"],
            job_name="Test Batch",
            analysis_type="quick",
            priority=5,
            status="queued",
            created_at=datetime.now(),
            progress=0
        )
        
        assert job.job_id == "test_job_001"
        assert len(job.audio_files) == 2
        assert job.priority == 5
    
    @pytest.mark.asyncio
    async def test_batch_engine_methods_exist(self, batch_engine):
        """Test: Verificar métodos del batch engine"""
        methods = [
            'enqueue_job',
            'get_status',
            'cancel_job',
            'process_queue'
        ]
        
        for method_name in methods:
            assert hasattr(batch_engine, method_name), f"Missing method: {method_name}"


class TestVirtualEngineer:
    """Tests del ingeniero virtual"""
    
    @pytest.fixture
    def virtual_engineer(self):
        """Crear instancia de VirtualEngineer"""
        return VirtualEngineer()
    
    @pytest.mark.asyncio
    async def test_virtual_engineer_initialization(self, virtual_engineer):
        """Test: Inicialización del virtual engineer"""
        assert virtual_engineer is not None
        assert hasattr(virtual_engineer, 'decide_pipeline')
        assert hasattr(virtual_engineer, 'decide_master_style')
    
    @pytest.mark.asyncio
    async def test_virtual_engineer_5_methods_exist(self, virtual_engineer):
        """Test: Verificar que existan los 5 métodos decisorios"""
        methods = [
            'decide_pipeline',
            'decide_master_style',
            'decide_priority',
            'decide_delegation',
            'generate_recommendations'
        ]
        
        for method_name in methods:
            assert hasattr(virtual_engineer, method_name), f"Missing method: {method_name}"
    
    @pytest.mark.asyncio
    async def test_complexity_score_calculation(self, virtual_engineer):
        """Test: Cálculo de complejidad"""
        # Mock AudioAnalysis
        mock_analysis = Mock()
        mock_analysis.issues = ["clipping", "dc_offset"]
        mock_analysis.spectral_flatness = 0.3
        mock_analysis.dynamic_range = 20.0
        
        score = virtual_engineer._calculate_complexity_score(mock_analysis)
        
        # Score debe estar entre 0 y 1
        assert 0.0 <= score <= 1.0


class TestIntegrationShubCanonical:
    """Tests de integración global del canon Shub"""
    
    @pytest.mark.asyncio
    async def test_all_modules_importable(self):
        """Test: Todos los módulos Shub son importables"""
        try:
            from shubniggurath.engines_paso8 import DSPEngine, FXEngine, AudioAnalysis
            from shubniggurath.integrations.reaper_rpc import REAPERController
            from shubniggurath.integrations.vx11_bridge import VX11Bridge
            from shubniggurath.core.dsp_pipeline_full import DSPPipelineFull
            from shubniggurath.core.audio_batch_engine import AudioBatchEngine
            from shubniggurath.core.virtual_engineer import VirtualEngineer
            
            assert True  # All imports successful
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_http_only_communication(self):
        """Test: Verificar que NO hay imports cruzados entre microservicios"""
        # Este test verifica que no hay referencias directas a módulos VX11
        
        # Las importaciones canónicas deben ser:
        # - config.settings
        # - config.tokens
        # - config.forensics
        # - httpx (para comunicación HTTP)
        # - numpy (para DSP)
        
        import ast
        import os
        
        shub_files = [
            "shubniggurath/integrations/reaper_rpc.py",
            "shubniggurath/integrations/vx11_bridge.py",
            "shubniggurath/core/dsp_pipeline_full.py",
            "shubniggurath/core/audio_batch_engine.py",
            "shubniggurath/core/virtual_engineer.py"
        ]
        
        forbidden_imports = [
            "madre", "switch", "hermes", "hormiguero",
            "manifestator", "tentaculo_link", "mcp", "spawner"
        ]
        
        for file_path in shub_files:
            if not os.path.exists(file_path):
                continue
            
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            for forbidden in forbidden_imports:
                for imp in imports:
                    assert forbidden not in imp, f"Found forbidden import in {file_path}: {imp}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
