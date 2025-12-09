"""Router Dispatcher: Enrutamiento inteligente de tareas de audio."""

from typing import Dict, Any, Optional
from enum import Enum


class TaskType(Enum):
    """Tipos de tareas soportadas."""
    ANALYZE = "analyze"
    MIX = "mix"
    MASTER = "master"
    FX_GENERATE = "fx_generate"
    REPAIR = "repair"
    EXPORT = "export"


class Dispatcher:
    """Dispatcher centralizado de tareas de audio."""

    def __init__(self, engines: Dict[str, Any]):
        self.engines = engines
        self.task_queue = []

    async def dispatch(self, task_type: str, 
                      payload: Dict[str, Any]) -> Dict[str, Any]:
        """Despachar tarea al motor correcto."""
        
        if task_type == TaskType.ANALYZE.value:
            return await self._dispatch_analysis(payload)
        elif task_type == TaskType.MIX.value:
            return await self._dispatch_mixing(payload)
        elif task_type == TaskType.MASTER.value:
            return await self._dispatch_mastering(payload)
        elif task_type == TaskType.FX_GENERATE.value:
            return await self._dispatch_fx_generation(payload)
        elif task_type == TaskType.REPAIR.value:
            return await self._dispatch_repair(payload)
        elif task_type == TaskType.EXPORT.value:
            return await self._dispatch_export(payload)
        else:
            return {"error": f"Unknown task type: {task_type}"}

    async def _dispatch_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Despachar análisis."""
        analyzer = self.engines.get("analyzer")
        if not analyzer:
            return {"error": "Analyzer engine not available"}

        audio_file = payload.get("file")
        return await analyzer.analyze_audio(audio_file)

    async def _dispatch_mixing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Despachar mezcla."""
        mix_engine = self.engines.get("mix")
        if not mix_engine:
            return {"error": "Mix engine not available"}

        project = payload.get("project", {})
        analysis = await mix_engine.analyze_tracks(project.get("tracks", []))
        return {"status": "success", "analysis": analysis}

    async def _dispatch_mastering(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Despachar masterización."""
        master_engine = self.engines.get("master")
        if not master_engine:
            return {"error": "Master engine not available"}

        mix = payload.get("mix", {})
        platform = payload.get("platform", "streaming")
        analysis = await master_engine.analyze_for_mastering(mix)
        chain = await master_engine.generate_master_chain(mix, platform)
        
        return {"status": "success", "analysis": analysis, "chain": chain}

    async def _dispatch_fx_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Despachar generación de FX chain."""
        fx_engine = self.engines.get("fx")
        if not fx_engine:
            return {"error": "FX engine not available"}

        analysis = payload.get("analysis", {})
        style = payload.get("style")
        chain = fx_engine.generate_fx_chain(analysis, style)
        
        return {"status": "success", "chain": fx_engine.to_dict(chain)}

    async def _dispatch_repair(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Despachar reparación de audio."""
        # Placeholder para futuro
        return {"status": "success", "repairs": []}

    async def _dispatch_export(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Despachar exportación."""
        master_engine = self.engines.get("master")
        if not master_engine:
            return {"error": "Master engine not available"}

        master_config = payload.get("master_config", {})
        formats = payload.get("formats", ["wav"])
        
        return await master_engine.export_masters(master_config, formats)

    def register_engine(self, name: str, engine: Any):
        """Registrar un motor."""
        self.engines[name] = engine

    async def health_check(self) -> Dict[str, bool]:
        """Verificar disponibilidad de motores."""
        return {
            "analyzer": self.engines.get("analyzer") is not None,
            "mix": self.engines.get("mix") is not None,
            "master": self.engines.get("master") is not None,
            "fx": self.engines.get("fx") is not None,
            "spectral": self.engines.get("spectral") is not None,
            "assistant": self.engines.get("assistant") is not None
        }
