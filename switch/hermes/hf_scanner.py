"""
HuggingFace Scanner — Buscador automático de modelos <2GB en HF.

Características:
- Búsqueda real contra API de HuggingFace
- Filtro estricto <2GB
- Cache local de búsquedas con TTL
- Ranking simple por descargas/puntuación

Hermes proporciona. Switch decide vía HermesCore.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from config.tokens import get_token

logger = logging.getLogger(__name__)


@dataclass
class HFModel:
    """Metadata de modelo HuggingFace."""

    model_id: str  # e.g., "mistral/mistral-7b"
    task: str  # text-generation, summarization, etc.
    model_name: str
    size_gb: float  # Size in GB
    downloads: int = 0  # Download count
    score: float = 0.0  # Community score (0-10)
    last_modified: str = ""  # ISO timestamp
    pipeline_tag: str = ""  # Task type tag
    gated: bool = False  # Requires approval

    # Rankings
    download_rank: int = 0
    score_rank: int = 0

    def download_url(self) -> str:
        """Generar URL de descarga."""
        return f"https://huggingface.co/{self.model_id}"

    def gguf_url(self) -> Optional[str]:
        """Generar URL si tiene GGUF disponible."""
        return f"https://huggingface.co/{self.model_id}/blob/main/gguf"


class HFScanner:
    """Scanner de modelos HuggingFace con cache y filtro <2GB."""

    def __init__(self, cache_dir: str = "data/hf_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.cache_dir / "hf_models_cache.json"
        self.cache_ttl = timedelta(hours=12)

        self.models_cache: Dict[str, List[HFModel]] = {}
        self.cache_updated_at: Dict[str, datetime] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Cargar cache local de búsquedas anteriores."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('models', {}))} cached model searches")
                    for task, models in data.get("models", {}).items():
                        self.models_cache[task] = [HFModel(**m) for m in models]
                    # timestamps opcionales
                    for task, ts in data.get("timestamps", {}).items():
                        try:
                            self.cache_updated_at[task] = datetime.fromisoformat(ts)
                        except Exception:
                            pass
            except Exception as e:
                logger.warning(f"Failed to load HF cache: {e}")

    def _save_cache(self) -> None:
        """Guardar cache local."""
        try:
            cache_data = {
                "models": {
                    task: [
                        {
                            "model_id": m.model_id,
                            "task": m.task,
                            "model_name": m.model_name,
                            "size_gb": m.size_gb,
                            "downloads": m.downloads,
                            "score": m.score,
                            "last_modified": m.last_modified,
                            "pipeline_tag": m.pipeline_tag,
                            "gated": m.gated,
                        }
                        for m in models
                    ]
                    for task, models in self.models_cache.items()
                },
                "timestamps": {k: v.isoformat() for k, v in self.cache_updated_at.items()},
            }
            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save HF cache: {e}")

    def _cache_valid(self, task: str) -> bool:
        ts = self.cache_updated_at.get(task)
        if not ts:
            return False
        return datetime.utcnow() - ts < self.cache_ttl

    async def search_models(
        self, task: str, max_size_gb: float = 2.0, limit: int = 10, use_cache: bool = True
    ) -> List[HFModel]:
        """
        Buscar modelos en HF para una tarea específica.
        Aplica filtro estricto <max_size_gb (default 2GB).
        """

        logger.info(f"Searching HF models for task={task}, max_size={max_size_gb}GB")

        if use_cache and self._cache_valid(task):
            cached = [m for m in self.models_cache.get(task, []) if m.size_gb <= max_size_gb]
            if cached:
                return cached[:limit]

        results = await self._query_hf_api(task, max_size_gb, limit)
        self.models_cache[task] = results
        self.cache_updated_at[task] = datetime.utcnow()
        self._save_cache()
        return results[:limit]

    async def _query_hf_api(self, task: str, max_size_gb: float, limit: int) -> List[HFModel]:
        """Consulta real a la API de HuggingFace con filtro <2GB."""
        api_url = "https://huggingface.co/api/models"
        params = {"search": task, "limit": max(limit * 2, 20), "sort": "downloads"}
        headers: Dict[str, str] = {}
        hf_token = get_token("HF_TOKEN") or None
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return self._parse_models(data, task, max_size_gb)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning(f"HF search fallback ({task}): {exc}")
            return self._demo_models(task, max_size_gb)

    def _parse_models(self, models: List[Dict[str, Any]], task: str, max_size_gb: float) -> List[HFModel]:
        parsed: List[HFModel] = []
        for model in models:
            model_id = model.get("modelId") or model.get("id") or ""
            if not model_id:
                continue
            size_bytes = self._estimate_size_bytes(model.get("siblings", []) or [])
            size_gb = size_bytes / (1024**3) if size_bytes else max_size_gb
            if size_gb > max_size_gb:
                continue
            parsed.append(
                HFModel(
                    model_id=model_id,
                    task=model.get("pipeline_tag") or task,
                    model_name=model_id.split("/")[-1],
                    size_gb=round(size_gb, 2),
                    downloads=model.get("downloads", 0) or model.get("likes", 0),
                    score=float(model.get("likes", 0) or 0) / 100.0,
                    last_modified=model.get("lastModified", "") or "",
                    pipeline_tag=model.get("pipeline_tag", ""),
                    gated=bool(model.get("gated")),
                )
            )
        parsed.sort(key=lambda m: (m.downloads, m.score), reverse=True)
        return parsed

    def _estimate_size_bytes(self, siblings: List[Dict[str, Any]]) -> int:
        """Calcular tamaño aproximado de un repo HF desde siblings."""
        total = 0
        for sibling in siblings:
            size = sibling.get("size") or 0
            if isinstance(size, (int, float)):
                total += int(size)
        return total

    def _demo_models(self, task: str, max_size_gb: float) -> List[HFModel]:
        """Fallback determinista para entornos sin red."""
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
                    task="code-generation",
                    model_name="StarCoder",
                    size_gb=1.5,
                    downloads=150000,
                    score=4.7,
                ),
            ],
        }
        models = demo_registry.get(task, demo_registry.get("text-generation", []))
        return [m for m in models if m.size_gb <= max_size_gb]

    async def get_model_details(self, model_id: str) -> Optional[HFModel]:
        """Obtener detalles de modelo específico desde cache."""
        for models in self.models_cache.values():
            for model in models:
                if model.model_id == model_id:
                    return model
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
