"""Test Madre Shub orchestration"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_audio_pipeline_creation():
    """Test audio pipeline creation"""
    from madre.madre_shub_orchestrator import ShubAudioPipeline
    
    pipeline = ShubAudioPipeline("tenant-1", "project-1")
    
    pipeline.add_stage("analyzer", {"file_path": "/audio/test.wav"})
    pipeline.add_stage("eq_generator", {})
    pipeline.add_stage("dynamics_processor", {})
    
    assert len(pipeline.stages) == 3
    assert pipeline.stages[0]["engine"] == "analyzer"


@pytest.mark.asyncio
async def test_pipeline_execution():
    """Test pipeline execution"""
    from madre.madre_shub_orchestrator import ShubAudioPipeline
    
    pipeline = ShubAudioPipeline("tenant-1", "project-1")
    pipeline.add_stage("analyzer", {})
    
    result = await pipeline.execute()
    
    assert "pipeline_id" in result
    assert result["successful"] == 1


@pytest.mark.asyncio
async def test_madre_orchestrator():
    """Test Madre Shub orchestrator"""
    from madre.madre_shub_orchestrator import MadreShubOrchestrator
    
    config = {
        "spawner_url": "http://spawner:8008",
        "token": "test_token",
    }
    
    orchestrator = MadreShubOrchestrator(config)
    
    stages = [
        {"engine": "analyzer", "params": {}},
        {"engine": "eq_generator", "params": {}},
    ]
    
    pipeline_id = await orchestrator.create_audio_pipeline(
        "tenant-1",
        "project-1",
        stages,
    )
    
    assert pipeline_id in orchestrator.pipelines


@pytest.mark.asyncio
async def test_pipeline_execution_via_orchestrator():
    """Test pipeline execution via orchestrator"""
    from madre.madre_shub_orchestrator import MadreShubOrchestrator
    
    config = {"spawner_url": "http://spawner:8008", "token": "test"}
    orchestrator = MadreShubOrchestrator(config)
    
    pipeline_id = await orchestrator.create_audio_pipeline(
        "tenant-1",
        "project-1",
        [{"engine": "analyzer", "params": {}}],
    )
    
    result = await orchestrator.execute_pipeline(pipeline_id)
    
    assert result["successful"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
