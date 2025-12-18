#!/usr/bin/env python3
"""
Hermes Download + Register Test Models
Downloads 2 GGUF models (<2GB each) and registers them in vx11.db

Models:
1. Mistral 7B Instruct (2.2GB GGUF Q4_K_M)
2. Neural Chat 7B (2.0GB GGUF Q4_M)
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py


import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import os
import urllib.request
import urllib.error

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.db_schema import get_session, LocalModelV2
from config.settings import settings
from config.forensics import write_log


MODELS_PATH = Path(os.getenv("VX11_MODELS_PATH", "data/models"))
MODELS_PATH.mkdir(parents=True, exist_ok=True)

# Model registry with HuggingFace URLs (using stable fast-download models for testing)
MODELS = [
    {
        "name": "tinyllama-1b-q4",
        "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_0.gguf",
        "size_mb": 656,
        "task_type": "chat",
        "tags": ["tinyllama", "1b", "lightweight", "fast"],
        "description": "TinyLlama 1.1B Chat, quantized Q4_0",
    },
    {
        "name": "llama2-7b-q4",
        "url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_0.gguf",
        "size_mb": 3826,
        "task_type": "chat",
        "tags": ["llama2", "7b", "instruct", "general"],
        "description": "Llama 2 7B Chat, quantized Q4_0",
    },
]


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_model(
    name: str, url: str, expected_size_mb: int, force: bool = False
) -> Optional[Path]:
    """
    Download GGUF model from HuggingFace.

    Args:
        name: Model name
        url: HuggingFace download URL
        expected_size_mb: Expected file size (for validation)
        force: Re-download even if exists

    Returns:
        Path to downloaded model, or None if failed
    """
    model_path = MODELS_PATH / f"{name}.gguf"

    # Check if already exists
    if model_path.exists() and not force:
        actual_size_mb = model_path.stat().st_size / (1024 * 1024)
        write_log("hermes", f"model_download:exists:{name}:{actual_size_mb:.1f}MB")
        print(f"✓ {name} already exists ({actual_size_mb:.1f}MB)")
        return model_path

    print(f"⏳ Downloading {name} ({expected_size_mb}MB)...")
    write_log("hermes", f"model_download:start:{name}:{url}")

    try:
        # Simple download with progress
        def download_progress(block_num, block_size, total_size):
            downloaded = (block_num * block_size) / (1024 * 1024)
            percent = min(100, (downloaded / (total_size / (1024 * 1024))) * 100)
            sys.stdout.write(
                f"\r  Progress: {percent:.1f}% ({downloaded:.1f}MB / {total_size / (1024 * 1024):.1f}MB)"
            )
            sys.stdout.flush()

        # Download
        urllib.request.urlretrieve(url, model_path, reporthook=download_progress)
        print()  # Newline after progress

        # Verify size
        actual_size_mb = model_path.stat().st_size / (1024 * 1024)
        if actual_size_mb < (expected_size_mb * 0.9):  # Allow 10% variance
            write_log(
                "hermes",
                f"model_download:size_mismatch:{name}:{actual_size_mb}MB vs {expected_size_mb}MB",
                level="WARNING",
            )
            print(
                f"⚠️  {name} size mismatch: {actual_size_mb:.1f}MB vs {expected_size_mb}MB expected"
            )

        # Compute hash
        hash_val = compute_file_hash(model_path)
        write_log(
            "hermes",
            f"model_download:ok:{name}:{actual_size_mb:.1f}MB:hash={hash_val[:16]}...",
        )
        print(f"✓ Downloaded {name} ({actual_size_mb:.1f}MB)")
        print(f"  Hash: {hash_val}")

        return model_path

    except urllib.error.HTTPError as e:
        write_log("hermes", f"model_download:http_error:{name}:{e.code}", level="ERROR")
        print(f"❌ HTTP error {e.code} downloading {name}")
        return None
    except urllib.error.URLError as e:
        write_log(
            "hermes", f"model_download:url_error:{name}:{e.reason}", level="ERROR"
        )
        print(f"❌ URL error downloading {name}: {e.reason}")
        return None
    except Exception as e:
        write_log("hermes", f"model_download:error:{name}:{e}", level="ERROR")
        print(f"❌ Error downloading {name}: {e}")
        return None


def register_model_in_db(
    name: str, path: Path, task_type: str, tags: list, description: str = ""
) -> bool:
    """
    Register model in model_registry (local_models_v2 table).

    Args:
        name: Model name
        path: Path to model file
        task_type: Task type (e.g., "chat")
        tags: List of tags
        description: Model description

    Returns:
        True if successful, False otherwise
    """
    db = None
    try:
        db = get_session("vx11")

        # Check if already registered
        existing = db.query(LocalModelV2).filter_by(name=name).first()
        if existing:
            write_log("hermes", f"model_register:already_exists:{name}")
            print(f"ℹ️  {name} already registered in DB")
            return True

        # Create new model entry
        model = LocalModelV2(
            name=name,
            engine="llama.cpp",  # Standard engine for GGUF
            path=str(path),
            size_bytes=int(path.stat().st_size),
            task_type=task_type,
            max_context=4096,
            enabled=True,
            compatibility="cpu",  # CPU-only for now
            meta_info=json.dumps(
                {
                    "tags": tags,
                    "description": description,
                    "quantization": "Q4",  # GGUF quantization level
                    "downloaded_at": datetime.utcnow().isoformat(),
                }
            ),
        )
        db.add(model)
        db.commit()

        write_log(
            "hermes",
            f"model_register:ok:{name}:{path.stat().st_size / (1024**2):.1f}MB",
        )
        print(f"✓ Registered {name} in DB")
        return True

    except Exception as e:
        write_log("hermes", f"model_register:error:{name}:{e}", level="ERROR")
        print(f"❌ Error registering {name}: {e}")
        if db:
            db.rollback()
        return False

    finally:
        if db:
            db.close()


def list_registered_models() -> int:
    """List all registered models in DB."""
    db = None
    try:
        db = get_session("vx11")
        models = db.query(LocalModelV2).filter_by(enabled=True).all()

        if not models:
            print("\nℹ️  No models registered")
            return 0

        print("\n📦 Registered Models:")
        print("-" * 70)
        for model in models:
            size_mb = model.size_bytes / (1024**2)
            print(
                f"  {model.name:30} | {size_mb:6.1f}MB | {model.task_type:10} | {model.engine}"
            )
        print(f"\nTotal: {len(models)} model(s)")
        return len(models)

    finally:
        if db:
            db.close()


def main():
    """Main entry point."""
    print("=" * 70)
    print("VX11 Hermes — Download & Register Test Models")
    print("=" * 70)
    print()

    # Download models
    downloaded = []
    for model_spec in MODELS:
        model_path = download_model(
            name=model_spec["name"],
            url=model_spec["url"],
            expected_size_mb=model_spec["size_mb"],
        )
        if model_path:
            downloaded.append((model_spec, model_path))
        print()

    if not downloaded:
        print("❌ No models downloaded successfully")
        return False

    print(f"✓ Downloaded {len(downloaded)}/{len(MODELS)} models")
    print()

    # Register in DB
    print("Registering models in database...")
    registered = 0
    for model_spec, model_path in downloaded:
        if register_model_in_db(
            name=model_spec["name"],
            path=model_path,
            task_type=model_spec["task_type"],
            tags=model_spec["tags"],
            description=model_spec["description"],
        ):
            registered += 1
        print()

    if registered == 0:
        print("❌ Failed to register models")
        return False

    print(f"✓ Registered {registered}/{len(downloaded)} models")
    print()

    # List all registered models
    list_registered_models()

    print()
    print("=" * 70)
    print("✅ Models download and registration complete")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)