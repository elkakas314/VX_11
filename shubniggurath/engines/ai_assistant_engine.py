"""AI Assistant Engine: Asistente inteligente para ingeniero de sonido."""

from typing import Dict, List, Any
from enum import Enum


class ExpertiseLevel(Enum):
    """Niveles de experiencia del ingeniero."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    PROFESSIONAL = "professional"


class AIAssistantEngine:
    """Motor de asistencia IA para ingenieros de sonido."""

    def __init__(self, expertise: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE):
        self.expertise = expertise
        self.conversation_history: List[Dict[str, str]] = []
        self.project_context: Dict[str, Any] = {}

    async def process_intent(self, user_message: str, 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar intención del ingeniero de sonido."""
        self.project_context = context

        # Detectar tipo de tarea
        task_type = self._detect_task_type(user_message)
        
        # Generar respuesta contextual
        response = await self._generate_response(task_type, user_message)

        # Guardar en historial
        self.conversation_history.append({
            "user": user_message,
            "assistant": response["message"],
            "task_type": task_type
        })

        return response

    def _detect_task_type(self, message: str) -> str:
        """Detectar tipo de tarea del mensaje."""
        keywords = {
            "analyze": ["analizar", "analyze", "ver", "check", "scan"],
            "mix": ["mezclar", "mix", "balance", "levels"],
            "master": ["masterizar", "master", "loudness", "lufs"],
            "fx": ["efectos", "fx", "plugin", "reverb", "delay", "eq"],
            "generate": ["generar", "generate", "create", "suggest", "recomendar"],
            "repair": ["reparar", "repair", "fix", "clipping", "noise"],
            "export": ["exportar", "export", "render", "save"]
        }

        message_lower = message.lower()
        for task, keywords_list in keywords.items():
            if any(kw in message_lower for kw in keywords_list):
                return task

        return "general"

    async def _generate_response(self, task_type: str,
                                message: str) -> Dict[str, Any]:
        """Generar respuesta contextual."""
        
        if task_type == "analyze":
            return {
                "message": "Analizando audio... Escaneando niveles, espectro y dinámicas.",
                "action": "run_analysis",
                "parameters": {}
            }
        elif task_type == "mix":
            return {
                "message": "Iniciando mezcla automática. Balanceando niveles y panning.",
                "action": "run_mixing",
                "parameters": {"tracks": self.project_context.get("tracks", [])}
            }
        elif task_type == "master":
            return {
                "message": "Preparando masterización. Ajustando loudness según plataforma de destino.",
                "action": "run_mastering",
                "parameters": {"platform": "streaming"}
            }
        elif task_type == "fx":
            return {
                "message": "Generando cadena de efectos inteligente basada en análisis.",
                "action": "generate_fx_chain",
                "parameters": {"style": "auto"}
            }
        elif task_type == "repair":
            return {
                "message": "Detectando y reparando problemas de audio (clipping, ruido, etc).",
                "action": "run_repair",
                "parameters": {}
            }
        elif task_type == "export":
            return {
                "message": "Preparando exportación en múltiples formatos.",
                "action": "export_masters",
                "parameters": {"formats": ["wav", "mp3", "flac"]}
            }
        else:
            return {
                "message": "¿Cómo puedo ayudarte con tu producción de audio?",
                "action": None,
                "parameters": {}
            }

    async def suggest_improvements(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sugerir mejoras basadas en análisis."""
        suggestions = []

        # Sugerencias basadas en niveles
        lufs = analysis.get("lufs_integrated", -14.0)
        if lufs > -12.0:
            suggestions.append({
                "category": "loudness",
                "severity": "high",
                "suggestion": f"LUFS muy alto ({lufs:.1f}). Reducir ganancia.",
                "action": "apply_gain_reduction",
                "amount": -((lufs + 14.0) / 2)
            })

        # Sugerencias basadas en dinámicas
        dr = analysis.get("dynamic_range", 10.0)
        if dr < 6.0:
            suggestions.append({
                "category": "dynamics",
                "severity": "medium",
                "suggestion": f"Rango dinámico bajo ({dr:.1f} dB). Considerar expansor.",
                "action": "add_expander"
            })

        # Sugerencias basadas en espectro
        centroid = analysis.get("spectral_centroid", 1000.0)
        if centroid < 800:
            suggestions.append({
                "category": "tone",
                "severity": "low",
                "suggestion": "Audio muy oscuro. Considerar brillo (high shelf EQ).",
                "action": "brighten"
            })

        return suggestions

    def get_expertise_level(self) -> str:
        """Obtener nivel de experiencia actual."""
        return self.expertise.value

    async def adapt_to_expertise(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Adaptar respuesta al nivel de experiencia."""
        if self.expertise == ExpertiseLevel.BEGINNER:
            # Explicaciones más detalladas
            response["explanation"] = "Esto significa que el audio necesita ajustes."
            response["hint"] = "Haz clic para ver detalles"
        elif self.expertise == ExpertiseLevel.PROFESSIONAL:
            # Respuestas técnicas directas
            response["simplified"] = False

        return response
