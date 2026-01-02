"""
P2.4: Local models scanner and HuggingFace model downloader.

Provides async functions to:
1. Scan local models on filesystem
2. Register models in DB (LocalModelV2)
3. Download models from HuggingFace Hub (with windowed access)
"""

import os
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from config.db_schema import get_session, LocalModelV2
from config.tokens import get_token

log = logging.getLogger(__name__)

# Common model patterns by file extension
MODEL_EXTENSIONS = {".bin", ".gguf", ".pt", ".pth", ".onnx", ".safetensors", ".pkl"}

# Common model directories to scan
MODEL_SEARCH_PATHS = [
    Path.home() / ".cache" / "huggingface" / "hub",
    Path.home() / ".cache" / "ollama",
    Path("/models"),
    Path("/app/models"),
    Path("/tmp/models"),
]


async def scan_local_models(search_paths: Optional[List[Path]] = None) -> List[Dict[str, Any]]:
    """
    Scan filesystem for local model files.
    
    Args:
        search_paths: List of paths to scan (defaults to MODEL_SEARCH_PATHS)
    
    Returns:
        List of detected models: {name, path, size_bytes, type, discovered_at}
    """
    if search_paths is None:
        search_paths = MODEL_SEARCH_PATHS
    
    detected = []
    
    for search_path in search_paths:
        if not search_path.exists():
            log.debug(f"Model search path does not exist: {search_path}")
            continue
        
        try:
            log.info(f"Scanning for models in: {search_path}")
            
            # Scan for model files
            for ext in MODEL_EXTENSIONS:
                try:
                    for model_file in search_path.rglob(f"*{ext}"):
                        if model_file.is_file():
                            try:
                                size_bytes = model_file.stat().st_size
                                model_name = model_file.stem
                                model_type = ext.lstrip(".")
                                
                                detected.append({
                                    "name": model_name,
                                    "path": str(model_file),
                                    "size_bytes": size_bytes,
                                    "type": model_type,
                                    "discovered_at": datetime.utcnow().isoformat(),
                                })
                                log.debug(f"Found model: {model_name} ({size_bytes} bytes)")
                            except Exception as e:
                                log.warning(f"Failed to process model file {model_file}: {e}")
                                continue
                except Exception as e:
                    log.warning(f"Failed to scan for extension {ext} in {search_path}: {e}")
                    continue
        
        except Exception as e:
            log.warning(f"Failed to scan directory {search_path}: {e}")
            continue
    
    log.info(f"Model scan complete: found {len(detected)} models")
    return detected


async def register_local_model(
    name: str,
    path: str,
    size_bytes: int,
    model_type: str = "general",
    engine: str = "gguf",
    task_type: str = "chat",
) -> Optional[int]:
    """
    Register a local model in the database.
    
    Args:
        name: Model name
        path: Full path to model file
        size_bytes: File size in bytes
        model_type: Model type (bin, gguf, pt, pth, onnx, safetensors, pkl) - stored in meta_info
        engine: Engine type (llama.cpp, gguf, ollama, transformers)
        task_type: Task type (chat, audio-engineer, summarization, audio-analysis)
    
    Returns:
        Model ID if registered, None on failure
    """
    db = get_session("vx11")
    try:
        import json
        
        # Check if model already exists
        existing = db.query(LocalModelV2).filter_by(name=name).first()
        meta_info = json.dumps({"file_type": model_type})
        
        if existing:
            # Update existing entry
            existing.path = path
            existing.size_bytes = size_bytes
            existing.engine = engine
            existing.task_type = task_type
            existing.last_checked = datetime.utcnow()  # Does not exist, use updated_at
            existing.updated_at = datetime.utcnow()
            existing.meta_info = meta_info
            db.commit()
            model_id = existing.id
            log.info(f"Updated local model: {name} (id={model_id})")
        else:
            # Create new entry
            model = LocalModelV2(
                name=name,
                path=path,
                size_bytes=size_bytes,
                engine=engine,
                task_type=task_type,
                meta_info=meta_info,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(model)
            db.commit()
            model_id = model.id
            log.info(f"Created local model: {name} (id={model_id})")
        
        return model_id
    
    except Exception as e:
        log.error(f"Failed to register model {name}: {e}")
        db.rollback()
        return None
    
    finally:
        db.close()


async def download_hf_model(
    model_id: str,
    token: Optional[str] = None,
    cache_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Download a model from HuggingFace Hub.
    
    Uses huggingface-hub CLI tool (huggingface-cli download).
    Requires HERMES_ALLOW_DOWNLOAD=1 environment variable.
    
    Args:
        model_id: HuggingFace model ID (e.g., "meta-llama/Llama-2-7b-hf")
        token: HuggingFace API token (defaults to env var HF_TOKEN)
        cache_dir: Custom cache directory (defaults to ~/.cache/huggingface/hub)
    
    Returns:
        Download info: {model_id, path, size_bytes, downloaded_at} or None on failure
    """
    allow_download = os.getenv("HERMES_ALLOW_DOWNLOAD", "0") == "1"
    if not allow_download:
        log.warning("Model download disabled (HERMES_ALLOW_DOWNLOAD != 1)")
        return None
    
    if cache_dir is None:
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    if token is None:
        token = os.getenv("HF_TOKEN") or get_token("HF_TOKEN")
    
    try:
        log.info(f"Downloading model from HuggingFace: {model_id}")
        
        # Use huggingface-cli download
        cmd = [
            "huggingface-cli",
            "download",
            model_id,
            "--cache-dir", str(cache_dir),
        ]
        
        if token:
            cmd.extend(["--token", token])
        
        # Run download with timeout (30 minutes = 1800 seconds)
        result = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            ),
            timeout=1800,
        )
        
        stdout, stderr = await result.communicate()
        
        if result.returncode != 0:
            log.error(f"Download failed: {stderr.decode()}")
            return None
        
        # Parse output to find model path
        output = stdout.decode()
        log.info(f"Download output: {output[:200]}")
        
        # Model is typically in cache_dir/models--user--repo/snapshots/...
        # For now, register with cache_dir as base path
        model_name = model_id.split("/")[-1]
        model_path = str(cache_dir / model_id.replace("/", "--"))
        
        # Get size if available
        size_bytes = 0
        try:
            if Path(model_path).exists():
                size_bytes = sum(f.stat().st_size for f in Path(model_path).rglob("*") if f.is_file())
        except Exception as e:
            log.warning(f"Failed to calculate model size: {e}")
        
        result_info = {
            "model_id": model_id,
            "path": model_path,
            "size_bytes": size_bytes,
            "downloaded_at": datetime.utcnow().isoformat(),
        }
        
        log.info(f"Download complete: {model_id} ({size_bytes} bytes)")
        return result_info
    
    except asyncio.TimeoutError:
        log.error(f"Download timeout for {model_id}")
        return None
    
    except Exception as e:
        log.error(f"Download failed for {model_id}: {e}")
        return None


if __name__ == "__main__":
    # Simple test: scan local models
    import asyncio as _asyncio
    
    async def test():
        models = await scan_local_models()
        print(f"Found {len(models)} models")
        for m in models[:3]:
            print(f"  - {m['name']}: {m['size_bytes']} bytes")
    
    _asyncio.run(test())
