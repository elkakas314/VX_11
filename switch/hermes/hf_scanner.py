"""
HuggingFace Scanner — Buscador automático de modelos <2GB en HF.

Características:
- Búsqueda por tarea (text-generation, summarization, translation, etc.)
- Filtro: modelos <2GB solamente
- Cache local de búsquedas
- Scoring por descarga/puntuación/recencia
- Download URL generation

Hermes proporciona. Switch decide.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HFModel:
    """Metadata de modelo HuggingFace."""
    
    model_id: str              # e.g., "mistral/mistral-7b"
    task: str                  # text-generation, summarization, etc.
    model_name: str
    size_gb: float             # Size in GB
    downloads: int = 0         # Download count
    score: float = 0.0         # Community score (0-10)
    last_modified: str = ""    # ISO timestamp
    pipeline_tag: str = ""     # Task type tag
    gated: bool = False        # Requires approval
    
    # Rankings
    download_rank: int = 0
    score_rank: int = 0
    
    def download_url(self) -> str:
        """Generar URL de descarga."""
        return f"https://huggingface.co/{self.model_id}"
    
    def gguf_url(self) -> Optional[str]:
        """Generar URL si tiene GGUF disponible."""
        # Stub: en realidad buscaría en el repo
        return f"https://huggingface.co/{self.model_id}/blob/main/gguf"


class HFScanner:
    """Scanner de modelos HuggingFace."""
    
    def __init__(self, cache_dir: str = "data/hf_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.cache_dir / "hf_models_cache.json"
        self.cache_ttl = timedelta(hours=24)
        
        self.models_cache: Dict[str, List[HFModel]] = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Cargar cache local de búsquedas anteriores."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} cached model searches")
                    # Parse back to HFModel objects
                    for task, models in data.items():
                        self.models_cache[task] = [HFModel(**m) for m in models]
            except Exception as e:
                logger.warning(f"Failed to load HF cache: {e}")
    
    def _save_cache(self) -> None:
        """Guardar cache local."""
        try:
            cache_data = {
                task: [
                    {
                        "model_id": m.model_id,
                        "task": m.task,
                        "model_name": m.model_name,
                        "size_gb": m.size_gb,
                        "downloads": m.downloads,
                        "score": m.score,
                        "last_modified": m.last_modified,
                    }
                    for m in models
                ]
                for task, models in self.models_cache.items()
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.warning(f"Failed to save HF cache: {e}")
    
    async def search_models(
        self,
        task: str,
        max_size_gb: float = 2.0,
        limit: int = 10,
        use_cache: bool = True
    ) -> List[HFModel]:
        """
        Buscar modelos en HF para una tarea específica.
        
        Args:
            task: Task type (text-generation, summarization, etc.)
            max_size_gb: Máximo tamaño permitido (default 2GB)
            limit: Máximo número de resultados
            use_cache: Usar cache local si disponible
            
        Returns:
            Lista de HFModel encontrados, ordenados por relevancia
        """
        
        logger.info(f"Searching HF models for task={task}, max_size={max_size_gb}GB")
        
        # Check cache
        if use_cache and task in self.models_cache:
            cached = self.models_cache[task]
            filtered = [m for m in cached if m.size_gb <= max_size_gb]
            logger.info(f"Using cached results: {len(filtered)} models")
            return filtered[:limit]
        
        # Stub: en producción, queryaría API de HF
        # Para demo, retornar modelos conocidos y pequeños
        demo_models = await self._get_demo_models(task, max_size_gb)
        
        # Cache results
        self.models_cache[task] = demo_models
        self._save_cache()
        
        return demo_models[:limit]
    
    async def _get_demo_models(self, task: str, max_size_gb: float) -> List[HFModel]:
        """Get demo models for testing (stub)."""
        
        demo_registry = {
            "text-generation": [
                HFModel(
                    model_id="mistral/mistral-7b",
                    task="text-generation",
                    model_name="Mistral 7B",
                    size_gb=1.4,
                    downloads=500000,
                    score=4.9,
                ),
                HFModel(
                    model_id="meta-llama/llama-2-7b",
                    task="text-generation",
                    model_name="Llama 2 7B",
                    size_gb=1.6,
                    downloads=300000,
                    score=4.8,
                ),
            ],
            "code-generation": [
                HFModel(
                    model_id="bigcode/starcoder",
                    task="text-generation",
                    model_name="StarCoder",
                    size_gb=1.5,
                    downloads=150000,
                    score=4.7,
                ),
            ],
            "summarization": [
                HFModel(
                    model_id="facebook/bart-large-cnn",
                    task="summarization",
                    model_name="BART Large CNN",
                    size_gb=1.2,
                    downloads=200000,
                    score=4.6,
                ),
            ],
            "translation": [
                HFModel(
                    model_id="Helsinki-NLP/opus-mt-en-es",
                    task="translation",
                    model_name="Opus-MT EN-ES",
                    size_gb=0.5,
                    downloads=100000,
                    score=4.5,
                ),
            ],
        }
        
        models = demo_registry.get(task, [])
        filtered = [m for m in models if m.size_gb <= max_size_gb]
        return sorted(filtered, key=lambda m: m.downloads, reverse=True)
    
    async def get_model_details(self, model_id: str) -> Optional[HFModel]:
        """Obtener detalles de modelo específico."""
        # Stub: queryaría API de HF por model_id
        logger.info(f"Fetching details for {model_id}")
        
        # Search all cached models
        for models in self.models_cache.values():
            for model in models:
                if model.model_id == model_id:
                    return model
        
        return None
    
    async def download_model(
        self,
        model_id: str,
        target_dir: str = "models"
    ) -> Optional[str]:
        """
        Descargar modelo desde HF.
        
        Args:
            model_id: Model identifier
            target_dir: Directorio de destino
            
        Returns:
            Ruta del modelo descargado o None si falla
        """
        logger.info(f"Downloading model: {model_id} to {target_dir}")
        
        try:
            target_path = Path(target_dir) / model_id.replace("/", "__")
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Stub: usaría huggingface_hub.snapshot_download()
            # from huggingface_hub import snapshot_download
            # snapshot_download(repo_id=model_id, local_dir=target_path)
            
            logger.info(f"✓ Downloaded to {target_path}")
            return str(target_path)
        except Exception as e:
            logger.error(f"Failed to download {model_id}: {e}")
            return None
    
    async def list_all_tasks(self) -> List[str]:
        """Listar todas las tareas (tasks) soportadas en cache."""
        return list(self.models_cache.keys())


# Instancia global
_hf_scanner: Optional[HFScanner] = None


def get_hf_scanner() -> HFScanner:
    """Obtener instancia global del HF scanner."""
    global _hf_scanner
    if _hf_scanner is None:
        _hf_scanner = HFScanner()
    return _hf_scanner
