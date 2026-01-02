"""
P2.4 Testing: Local models and HuggingFace downloads
Tests:
- models_scanner module functions
- Window policy for downloads
- Database registration functions
"""

import pytest
import asyncio
from pathlib import Path

VALID_TOKEN = "vx11-test-token"


@pytest.mark.asyncio
async def test_models_pull_disabled_by_default():
    """Test that model download respects HERMES_ALLOW_DOWNLOAD flag"""
    import os
    from switch.hermes.models_scanner import download_hf_model
    
    # By default, HERMES_ALLOW_DOWNLOAD should not be set
    current_value = os.getenv("HERMES_ALLOW_DOWNLOAD")
    
    try:
        # Test with download disabled
        os.environ["HERMES_ALLOW_DOWNLOAD"] = "0"
        result = await download_hf_model("gpt2")
        assert result is None, "Should return None when download is disabled"
        print(f"✓ Download correctly disabled when HERMES_ALLOW_DOWNLOAD=0")
    finally:
        if current_value:
            os.environ["HERMES_ALLOW_DOWNLOAD"] = current_value
        elif "HERMES_ALLOW_DOWNLOAD" in os.environ:
            del os.environ["HERMES_ALLOW_DOWNLOAD"]


@pytest.mark.asyncio
async def test_models_scanner_module_syntax():
    """Test that models_scanner module imports correctly"""
    from switch.hermes.models_scanner import (
        scan_local_models,
        register_local_model,
        download_hf_model,
        MODEL_EXTENSIONS,
        MODEL_SEARCH_PATHS,
    )
    
    assert callable(scan_local_models)
    assert callable(register_local_model)
    assert callable(download_hf_model)
    assert isinstance(MODEL_EXTENSIONS, set)
    assert isinstance(MODEL_SEARCH_PATHS, list)
    print(f"✓ models_scanner module OK: {len(MODEL_EXTENSIONS)} extensions, {len(MODEL_SEARCH_PATHS)} paths")


@pytest.mark.asyncio
async def test_models_pull_request_schema():
    """Test ModelPullRequest schema"""
    from switch.hermes.main import ModelPullRequest
    
    # Valid request
    req = ModelPullRequest(model_id="gpt2")
    assert req.model_id == "gpt2"
    assert req.token is None
    assert req.cache_dir is None
    
    # With optional fields
    req2 = ModelPullRequest(
        model_id="meta-llama/Llama-2-7b",
        token="hf_xxx",
        cache_dir="/tmp/models"
    )
    assert req2.model_id == "meta-llama/Llama-2-7b"
    assert req2.token == "hf_xxx"
    assert req2.cache_dir == "/tmp/models"
    print(f"✓ ModelPullRequest schema OK")


@pytest.mark.asyncio
async def test_scan_local_models():
    """Test scan_local_models function"""
    from switch.hermes.models_scanner import scan_local_models
    
    # Scan default paths (should exist or be gracefully skipped)
    models = await scan_local_models()
    assert isinstance(models, list)
    print(f"✓ scan_local_models returned {len(models)} models")
    
    # Check structure if any models found
    if models:
        m = models[0]
        assert "name" in m
        assert "path" in m
        assert "size_bytes" in m
        assert "type" in m
        assert "discovered_at" in m
        print(f"  → Sample model: {m['name']} ({m['size_bytes']} bytes, type={m['type']})")


@pytest.mark.asyncio
async def test_register_local_model():
    """Test register_local_model function (DB registration)"""
    from switch.hermes.models_scanner import register_local_model
    
    # Register a test model
    model_id = await register_local_model(
        name="test_model_p24",
        path="/tmp/test_model.bin",
        size_bytes=1024 * 1024,  # 1 MB
        model_type="bin",
    )
    
    assert model_id is not None, "Model should be registered successfully"
    assert isinstance(model_id, int)
    print(f"✓ Model registered with ID: {model_id}")
    
    # Verify it's in the database
    from config.db_schema import LocalModelV2, get_session
    
    db = get_session("vx11")
    try:
        registered = db.query(LocalModelV2).filter_by(id=model_id).first()
        assert registered is not None, "Model should exist in database"
        assert registered.name == "test_model_p24"
        assert registered.engine == "gguf"
        assert registered.task_type == "chat"
        print(f"✓ Model verified in database: {registered.name} (engine={registered.engine}, task={registered.task_type})")
    finally:
        db.close()


@pytest.mark.asyncio
async def test_settings_hermes_allow_download():
    """Test that settings include hermes_allow_download flag"""
    from config.settings import settings
    
    assert hasattr(settings, "hermes_allow_download"), "settings should have hermes_allow_download"
    assert isinstance(settings.hermes_allow_download, bool)
    print(f"✓ settings.hermes_allow_download = {settings.hermes_allow_download}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

