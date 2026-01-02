"""CLI Scanner for Hermes: detects local CLIs and registers them in BD."""

import subprocess
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from config.db_schema import get_session, CLIProvider, CLIRegistry

log = logging.getLogger("hermes.cli_scanner")

# List of CLIs to detect
COMMON_CLIS = [
    "gh",
    "copilot",
    "deepseek",
    "gemini",
    "ollama",
    "qwen",
    "which",
    "python3",
    "curl",
    "git",
]


async def scan_cli_binaries(cli_list: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Scan for local CLI binaries and extract version information.
    
    Args:
        cli_list: List of CLI names to scan. Defaults to COMMON_CLIS.
    
    Returns:
        List of {name, path, version, detected_at}
    """
    if cli_list is None:
        cli_list = COMMON_CLIS
    
    detected = []
    
    for cli_name in cli_list:
        try:
            # Try to find the CLI using 'which'
            result = subprocess.run(
                ["which", cli_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                cli_path = result.stdout.strip()
                version = "unknown"
                
                # Try to get version
                try:
                    version_result = subprocess.run(
                        [cli_name, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if version_result.returncode == 0:
                        version = version_result.stdout.strip().split('\n')[0][:100]
                except Exception as e:
                    log.debug(f"Failed to get version for {cli_name}: {e}")
                
                detected.append({
                    "name": cli_name,
                    "path": cli_path,
                    "version": version,
                    "detected_at": datetime.utcnow().isoformat(),
                })
                log.info(f"Detected CLI: {cli_name} at {cli_path} (version: {version[:50]})")
        
        except subprocess.TimeoutExpired:
            log.warning(f"CLI detection timeout for {cli_name}")
        except Exception as e:
            log.debug(f"CLI detection skipped for {cli_name}: {e}")
    
    return detected


async def register_cli_provider(
    name: str,
    path: str,
    version: str,
) -> Optional[int]:
    """Register a CLI provider in the database (cli_providers + cli_registry).
    
    Args:
        name: CLI name
        path: Full path to CLI binary
        version: Version string
    
    Returns:
        Provider ID if registered, None on failure
    """
    db = get_session("vx11")
    try:
        # Register in cli_providers (follows existing schema)
        existing_provider = db.query(CLIProvider).filter_by(name=name).first()
        if existing_provider:
            # Update existing entry
            existing_provider.api_key_env = "NONE"
            existing_provider.enabled = False
            existing_provider.updated_at = datetime.utcnow()
            db.commit()
            provider_id = existing_provider.id
            log.info(f"Updated CLI provider: {name} (id={provider_id})")
        else:
            # Create new entry
            provider = CLIProvider(
                name=name,
                api_key_env="NONE",
                enabled=False,
                task_types="cli",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(provider)
            db.commit()
            provider_id = provider.id
            log.info(f"Created CLI provider: {name} (id={provider_id})")
        
        # Register in cli_registry (follows existing schema)
        existing_registry = db.query(CLIRegistry).filter_by(name=name).first()
        if existing_registry:
            existing_registry.bin_path = path
            existing_registry.available = True
            existing_registry.last_checked = datetime.utcnow()
            existing_registry.updated_at = datetime.utcnow()
            db.commit()
            log.info(f"Updated CLI in registry: {name}")
        else:
            registry_entry = CLIRegistry(
                name=name,
                bin_path=path,
                available=True,
                cli_type="utility",
                last_checked=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(registry_entry)
            db.commit()
            log.info(f"Registered CLI in registry: {name}")
        
        return provider_id
    
    except Exception as e:
        log.error(f"register_cli_provider failed for {name}: {e}")
        db.rollback()
        return None
    finally:
        db.close()
