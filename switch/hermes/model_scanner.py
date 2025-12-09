"""
Hermes Model Scanner v2:
- Escanea carpetas locales para modelos (HF, GGUF, ONNX, etc)
- Registra en BD (ModelRegistry)
- Enforza límites (max modelos, max GB)
- Integración con DeepSeek R1 para sugerencias
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio

from config.settings import settings
from config import deepseek
from config.forensics import write_log

logger = logging.getLogger("switch.hermes.model_scanner")


class ModelScanner:
    """Scanner centralizado de modelos locales."""
    
    # Extensiones conocidas
    MODEL_EXTENSIONS = {
        ".gguf": "gguf",
        ".bin": "pytorch",
        ".safetensors": "safetensors",
        ".pt": "pytorch",
        ".pth": "pytorch",
        ".onnx": "onnx",
        ".pb": "tensorflow",
        ".h5": "tensorflow",
    }
    
    # Carpetas a escanear
    DEFAULT_SCAN_PATHS = [
        "./models",
        "./checkpoints",
        "~/.cache/huggingface/hub",
        "/mnt/models",
        "/models",
    ]
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.scan_paths = self._resolve_paths()
    
    def _resolve_paths(self) -> List[Path]:
        """Resolver rutas (expandir ~, crear si no existen)."""
        paths = []
        scan_dirs = [
            getattr(settings, "local_models_path", "./models"),
            getattr(settings, "huggingface_cache_path", "~/.cache/huggingface"),
        ]
        scan_dirs.extend(self.DEFAULT_SCAN_PATHS)
        
        for p in scan_dirs:
            try:
                resolved = Path(p).expanduser().resolve()
                if resolved.exists():
                    paths.append(resolved)
            except Exception as e:
                logger.warning(f"Could not resolve path {p}: {e}")
        
        return list(set(paths))  # Deduplicar
    
    async def scan_local_models(self) -> List[Dict]:
        """Escanear carpetas y retornar modelos encontrados."""
        models = []
        
        for scan_path in self.scan_paths:
            try:
                for root, dirs, files in os.walk(scan_path):
                    # Limitar profundidad
                    if root.count(os.sep) - scan_path.count(os.sep) > 3:
                        dirs.clear()
                        continue
                    
                    for file in files:
                        ext = Path(file).suffix.lower()
                        if ext in self.MODEL_EXTENSIONS:
                            model_path = Path(root) / file
                            model_info = await self._extract_model_info(model_path)
                            if model_info:
                                models.append(model_info)
            except Exception as e:
                logger.error(f"Error scanning {scan_path}: {e}")
                write_log("hermes", f"scan_error:{scan_path}:{e}", level="WARN")
        
        write_log("hermes", f"scan_complete:found={len(models)}")
        return models
    
    async def _extract_model_info(self, model_path: Path) -> Optional[Dict]:
        """Extraer info del modelo (nombre, tamaño, tipo)."""
        try:
            size_bytes = model_path.stat().st_size
            
            # Heurística simple para tipo (mejorar después)
            model_type = "chat"  # default
            if "code" in model_path.name.lower():
                model_type = "code"
            elif "embed" in model_path.name.lower():
                model_type = "embedding"
            
            # Provider heurístico
            provider = "local"
            if ".gguf" in model_path.suffix.lower():
                provider = "gguf"
            elif ".onnx" in model_path.suffix.lower():
                provider = "onnx"
            
            return {
                "name": model_path.stem,
                "path": str(model_path),
                "provider": provider,
                "type": model_type,
                "size_bytes": size_bytes,
                "tags": ["local"],
                "last_used": datetime.utcnow().isoformat(),
                "score": 0.5,
                "available": True,
                "metadata": {
                    "file_extension": model_path.suffix,
                    "discovered_at": datetime.utcnow().isoformat(),
                },
            }
        except Exception as e:
            logger.error(f"Could not extract info from {model_path}: {e}")
            return None
    
    async def register_models_in_db(self, models: List[Dict]) -> Dict:
        """Registrar/actualizar modelos en BD."""
        if not self.db_session:
            logger.warning("No DB session, skipping registration")
            return {"registered": 0, "updated": 0, "skipped": 0}
        
        from config.db_schema import ModelRegistry
        
        registered = 0
        updated = 0
        
        for model_info in models:
            try:
                # Buscar si ya existe
                existing = self.db_session.query(ModelRegistry).filter_by(
                    name=model_info["name"],
                    path=model_info["path"]
                ).first()
                
                if existing:
                    existing.last_used = datetime.utcnow()
                    existing.available = True
                    updated += 1
                else:
                    new_model = ModelRegistry(**model_info)
                    self.db_session.add(new_model)
                    registered += 1
            except Exception as e:
                logger.error(f"Error registering model {model_info['name']}: {e}")
        
        try:
            self.db_session.commit()
        except Exception as e:
            logger.error(f"DB commit error: {e}")
            self.db_session.rollback()
        
        result = {"registered": registered, "updated": updated, "skipped": len(models) - registered - updated}
        write_log("hermes", f"register_models:{result}")
        return result
    
    async def enforce_limits(self) -> Dict:
        """Enforcar límites de modelo (max count, max GB)."""
        if not self.db_session:
            return {"cleaned": 0}
        
        from config.db_schema import ModelRegistry
        
        max_models = getattr(settings, "max_local_models", 20)
        max_gb = getattr(settings, "max_local_models_gb", 4.0)
        max_bytes = max_gb * (1024 ** 3)
        
        # Obtener todos los modelos ordenados por score (peor primero)
        models = self.db_session.query(ModelRegistry).order_by(
            ModelRegistry.score,
            ModelRegistry.last_used
        ).all()
        
        total_size = sum(m.size_bytes for m in models)
        cleaned = 0
        
        # Eliminar modelos menos usados si se exceden límites
        for model in models:
            if len(models) <= max_models and total_size <= max_bytes:
                break
            
            try:
                if model.path and Path(model.path).exists():
                    Path(model.path).unlink()
                
                self.db_session.delete(model)
                total_size -= model.size_bytes
                cleaned += 1
                write_log("hermes", f"enforce_limits:deleted:{model.name}")
            except Exception as e:
                logger.error(f"Error deleting model {model.name}: {e}")
        
        try:
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
        
        return {"cleaned": cleaned}
    
    async def suggest_models_for(
        self,
        task_type: str,
        constraints: Dict
    ) -> List[str]:
        """
        Usar DeepSeek R1 para sugerir modelos HF a descargar.
        Si no hay API key, usar heurísticas locales.
        """
        max_size_gb = constraints.get("max_size_gb", 2.0)
        context_length = constraints.get("context_length", 4096)
        
        # Prompt para DeepSeek R1
        prompt = f"""
        Necesito modelos HuggingFace para: {task_type}
        
        Restricciones:
        - Tamaño máximo: {max_size_gb} GB
        - Context length: {context_length} tokens
        
        Sugiere 5 modelos específicos (nombre exacto de HF repo).
        Retorna JSON: [
            {{"repo": "org/model-name", "size_gb": 2.5, "reason": "...", "context": 4096}},
            ...
        ]
        """
        
        # Intentar DeepSeek R1
        try:
            resp = await deepseek.call_deepseek_reasoner(prompt, timeout=30.0)
            if resp.get("ok"):
                # Parsear JSON de la respuesta
                # TODO: Implementar parsing robusto
                return resp.get("result", [])
        except Exception as e:
            logger.warning(f"DeepSeek suggestion failed: {e}")
        
        # Fallback heurístico local
        fallback_suggestions = {
            "chat": [
                "mistralai/Mistral-7B-Instruct-v0.2",
                "meta-llama/Llama-2-7b-chat",
                "NousResearch/Nous-Hermes-2-7b",
            ],
            "code": [
                "mistralai/Mistral-7B",
                "bigcode/starcoder",
                "Qwen/Qwen1.5-7B",
            ],
            "embedding": [
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2",
            ],
        }
        
        return fallback_suggestions.get(task_type, fallback_suggestions["chat"])


class CLIRegistry:
    """Gestor centralizado de CLIs."""
    
    KNOWN_CLIS = {
        # DevOps
        "docker": {"type": "devops", "rate_limit": None},
        "kubectl": {"type": "devops", "rate_limit": None},
        "terraform": {"type": "devops", "rate_limit": None},
        "ansible": {"type": "devops", "rate_limit": None},
        
        # VCS
        "git": {"type": "vcs", "rate_limit": None},
        "gh": {"type": "vcs", "token_key": "GH_TOKEN", "rate_limit": 5000},
        "gitlab": {"type": "vcs", "token_key": "GITLAB_TOKEN", "rate_limit": 600},
        
        # Búsqueda / Info
        "curl": {"type": "http", "rate_limit": None},
        "wget": {"type": "http", "rate_limit": None},
        
        # Dev
        "npm": {"type": "package_mgr", "rate_limit": None},
        "pip": {"type": "package_mgr", "rate_limit": None},
        "cargo": {"type": "package_mgr", "rate_limit": None},
        
        # Utils
        "python": {"type": "interpreter", "rate_limit": None},
        "node": {"type": "interpreter", "rate_limit": None},
        "ruby": {"type": "interpreter", "rate_limit": None},
    }
    
    def __init__(self, db_session=None):
        self.db_session = db_session
    
    async def check_available_clis(self) -> Dict:
        """Detectar qué CLIs están disponibles."""
        import shutil
        
        available = {}
        for cli_name, cli_info in self.KNOWN_CLIS.items():
            bin_path = shutil.which(cli_name)
            available[cli_name] = {
                "available": bool(bin_path),
                "bin_path": bin_path,
                **cli_info,
            }
        
        return available
    
    async def register_clis_in_db(self, clis_status: Dict) -> Dict:
        """Registrar CLIs en BD."""
        if not self.db_session:
            return {"registered": 0}
        
        from config.db_schema import CLIRegistry
        
        registered = 0
        
        for cli_name, cli_info in clis_status.items():
            try:
                existing = self.db_session.query(CLIRegistry).filter_by(
                    name=cli_name
                ).first()
                
                if existing:
                    existing.available = cli_info["available"]
                    existing.bin_path = cli_info.get("bin_path")
                    existing.last_checked = datetime.utcnow()
                else:
                    new_cli = CLIRegistry(
                        name=cli_name,
                        bin_path=cli_info.get("bin_path"),
                        available=cli_info["available"],
                        cli_type=cli_info.get("type", "unknown"),
                        token_config_key=cli_info.get("token_key"),
                        rate_limit_daily=cli_info.get("rate_limit"),
                    )
                    self.db_session.add(new_cli)
                    registered += 1
            except Exception as e:
                logger.error(f"Error registering CLI {cli_name}: {e}")
        
        try:
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
        
        return {"registered": registered}


# Instancias globales
_scanner = None
_cli_registry = None


async def get_scanner(db_session=None):
    """Get o crear instancia scanner."""
    global _scanner
    if not _scanner:
        _scanner = ModelScanner(db_session)
    return _scanner


async def get_cli_registry(db_session=None):
    """Get o crear instancia CLI registry."""
    global _cli_registry
    if not _cli_registry:
        _cli_registry = CLIRegistry(db_session)
    return _cli_registry
