"""
Shub-Niggurath Ultimate v3.0 — Núcleo Conversacional + Análisis Audio
Integración segura con VX11 v6.2 sin tocar nada fuera de /shub/
v3.1 — Soporte para REAPER real (no virtual)
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path

# ============================================================================
# ENUMS Y MODELOS BASE
# ============================================================================

class AssistantMode(str, Enum):
    """Modos de operación del asistente"""
    CONVERSATIONAL = "conversational"
    ANALYSIS = "analysis"
    MIXING = "mixing"
    MASTERING = "mastering"
    MONITORING = "monitoring"
    MAINTENANCE = "maintenance"


class AudioState(str, Enum):
    """Estados del proyecto de audio"""
    IDLE = "idle"
    RECORDING = "recording"
    ANALYZING = "analyzing"
    MIXING = "mixing"
    EXPORTING = "exporting"
    ERROR = "error"


class StudioContext:
    """Contexto global del estudio (análogo a Context7 en VX11)"""
    
    def __init__(self):
        self.mode: AssistantMode = AssistantMode.CONVERSATIONAL
        self.audio_state: AudioState = AudioState.IDLE
        self.timestamp: datetime = datetime.utcnow()
        self.conversation_history: List[Dict[str, str]] = []
        self.analysis_cache: Dict[str, Any] = {}
        self.active_tracks: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict:
        return {
            "mode": self.mode.value,
            "audio_state": self.audio_state.value,
            "timestamp": self.timestamp.isoformat(),
            "conversation_length": len(self.conversation_history),
            "active_tracks_count": len(self.active_tracks),
            "cache_entries": len(self.analysis_cache),
        }


class ShubMessage:
    """Estructura unificada de mensajes Shub"""
    
    def __init__(
        self,
        role: str,  # "user", "assistant", "system"
        content: str,
        context: Optional[StudioContext] = None,
        metadata: Optional[Dict] = None,
    ):
        self.role = role
        self.content = content
        self.context = context or StudioContext()
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "context": self.context.to_dict(),
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


# ============================================================================
# PIPELINE CORE (0→100)
# ============================================================================

class PipelineStage(Enum):
    """Etapas del pipeline de procesamiento"""
    INPUT = 0
    PARSE = 20
    ANALYZE = 40
    PROCESS = 60
    RENDER = 80
    OUTPUT = 100


class ShubPipeline:
    """Pipeline de procesamiento modular 0→100"""
    
    def __init__(self, name: str):
        self.name = name
        self.current_stage: PipelineStage = PipelineStage.INPUT
        self.progress: int = 0
        self.stages: Dict[PipelineStage, callable] = {}
        self.results: Dict[str, Any] = {}
        self.errors: List[str] = []
    
    def register_stage(self, stage: PipelineStage, handler: callable):
        """Registrar handler para etapa"""
        self.stages[stage] = handler
    
    async def execute(self, input_data: Any) -> Dict[str, Any]:
        """Ejecutar pipeline completo"""
        try:
            for stage in sorted(self.stages.keys(), key=lambda x: x.value):
                self.current_stage = stage
                self.progress = stage.value
                handler = self.stages[stage]
                self.results[stage.name] = await handler(input_data)
                input_data = self.results[stage.name]
            
            self.current_stage = PipelineStage.OUTPUT
            self.progress = 100
            return {
                "status": "success",
                "pipeline": self.name,
                "progress": self.progress,
                "results": self.results,
            }
        except Exception as e:
            self.errors.append(str(e))
            return {
                "status": "error",
                "pipeline": self.name,
                "error": str(e),
                "progress": self.progress,
            }


# ============================================================================
# ASISTENTE CORE
# ============================================================================

class ShubAssistant:
    """Asistente principal de Shub-Niggurath
    
    v3.1: Incluye soporte para REAPER real (ReaperBridge)
    """
    
    def __init__(self, name: str = "Shub-Niggurath", enable_reaper_bridge: bool = True):
        self.name = name
        self.context = StudioContext()
        self.conversation_history: List[ShubMessage] = []
        self.pipelines: Dict[str, ShubPipeline] = {}
        self.connected_vx11 = False
        self.last_action: Optional[str] = None
        self.analysis_engine = None  # Será inicializado en fase 2
        
        # v3.1: REAPER Bridge integration
        self.reaper_bridge = None
        self.reaper_enabled = enable_reaper_bridge
        if enable_reaper_bridge:
            try:
                from shubniggurath.shub_reaper_bridge import ReaperBridge, ShubReaperIntegration
                self.reaper_bridge = ReaperBridge()
                self.reaper_integration = ShubReaperIntegration(self.reaper_bridge)
            except Exception:
                self.reaper_enabled = False
        
        self.current_project = None  # Proyecto REAPER actual cargado
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Agregar mensaje al historial"""
        msg = ShubMessage(role, content, self.context.copy() if hasattr(self.context, 'copy') else self.context, metadata)
        self.conversation_history.append(msg)
        return msg
    
    async def process_command(self, command: str, args: Optional[Dict] = None) -> Dict:
        """Procesar comando del usuario"""
        self.context.mode = AssistantMode.CONVERSATIONAL
        
        response = {
            "status": "processing",
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
            "assistant": self.name,
        }
        
        try:
            # Enrutar comando
            if command == "analyze":
                response = await self._handle_analysis(args or {})
            elif command == "load_reaper":
                response = await self._handle_load_reaper(args or {})
            elif command == "reaper_analysis":
                response = await self._handle_reaper_analysis(args or {})
            elif command == "mix":
                response = await self._handle_mixing(args or {})
            elif command == "status":
                response = self._get_status()
            elif command == "help":
                response = self._get_help()
            else:
                response["status"] = "unknown_command"
                response["available"] = ["load_reaper", "reaper_analysis", "analyze", "mix", "status", "help"]
            
            self.last_action = command
        except Exception as e:
            response["status"] = "error"
            response["error"] = str(e)
        
        return response
    
    async def _handle_load_reaper(self, args: Dict) -> Dict:
        """Manejo de carga de proyecto REAPER"""
        if not self.reaper_enabled:
            return {"status": "error", "error": "REAPER bridge not available"}
        
        project_path = args.get("path")
        if not project_path:
            # Try to list projects
            projects = await self.reaper_bridge.get_projects_list()
            return {
                "status": "projects_available",
                "projects": projects[:10],  # Mostrar primeros 10
                "total": len(projects),
                "hint": "Provide 'path' parameter to load a specific project",
            }
        
        # Load specific project
        self.current_project = await self.reaper_bridge.parse_project_file(project_path)
        
        if not self.current_project:
            return {"status": "error", "error": f"Failed to load project: {project_path}"}
        
        self.context.metadata["current_project"] = self.current_project.name
        self.context.active_tracks = [t.name for t in self.current_project.tracks]
        
        return {
            "status": "project_loaded",
            "project_name": self.current_project.name,
            "bpm": self.current_project.bpm,
            "sample_rate": self.current_project.sample_rate,
            "track_count": len(self.current_project.tracks),
            "regions": len(self.current_project.regions),
        }
    
    async def _handle_reaper_analysis(self, args: Dict) -> Dict:
        """Análisis de proyecto REAPER"""
        if not self.current_project:
            return {"status": "error", "error": "No REAPER project loaded"}
        
        if not self.reaper_integration:
            return {"status": "error", "error": "REAPER integration not available"}
        
        analysis = await self.reaper_integration.analyze_project(self.current_project.path)
        
        self.context.analysis_cache["last_reaper_analysis"] = analysis
        self.context.audio_state = AudioState.ANALYZING
        
        return {
            "status": "reaper_analysis_complete",
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _handle_analysis(self, args: Dict) -> Dict:
        """Manejo de análisis de audio"""
        self.context.audio_state = AudioState.ANALYZING
        # Implementación en fase 3+
        return {
            "status": "analysis_queued",
            "analysis_type": args.get("type", "full"),
        }
    
    async def _handle_mixing(self, args: Dict) -> Dict:
        """Manejo de mezcla"""
        self.context.audio_state = AudioState.MIXING
        # Implementación en fase 3+
        return {
            "status": "mixing_queued",
            "num_tracks": len(self.context.active_tracks),
        }
    
    def _get_status(self) -> Dict:
        """Obtener estado actual"""
        return {
            "status": "ok",
            "assistant": self.name,
            "context": self.context.to_dict(),
            "conversation_length": len(self.conversation_history),
            "vx11_connected": self.connected_vx11,
            "last_action": self.last_action,
        }
    
    def _get_help(self) -> Dict:
        """Obtener ayuda"""
        return {
            "status": "help",
            "commands": {
                "load_reaper": "Cargar proyecto REAPER real (path: ruta al .rpp)",
                "reaper_analysis": "Analizar proyecto REAPER cargado",
                "analyze": "Analizar proyecto de audio",
                "mix": "Iniciar mezcla",
                "status": "Ver estado actual",
                "help": "Este mensaje",
            },
            "features": {
                "reaper_bridge_enabled": self.reaper_enabled,
                "reaper_projects_dir": str(self.reaper_bridge.projects_path) if self.reaper_bridge else "N/A",
                "current_project": self.current_project.name if self.current_project else None,
            },
        }


# ============================================================================
# EXPORTES
# ============================================================================

__all__ = [
    "AssistantMode",
    "AudioState",
    "StudioContext",
    "ShubMessage",
    "PipelineStage",
    "ShubPipeline",
    "ShubAssistant",
]
