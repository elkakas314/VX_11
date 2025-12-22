"""
Virtual Engineer — Motor de Decisión Automática Inteligente
===========================================================

Sistema experto determinístico que decide automáticamente:
- Pipeline de procesamiento (mode_c, quick, deep)
- Estilo de masterización (streaming, vinyl, cd, loudness_war, dynamic)
- Prioridad de procesamiento (1-10)
- Delegación a módulos (Switch, Hermes, Hormiguero)
- Recomendaciones para Madre/Operador

Usa análisis de AudioAnalysis para inferir decisiones óptimas.
Integración bidireccional con Switch para IA de routing.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.forensics import write_log, record_crash
from shubniggurath.engines_paso8 import AudioAnalysis
from shubniggurath.integrations.vx11_bridge import VX11Bridge

# =============================================================================
# LOGGING & CONSTANTS
# =============================================================================

logger = logging.getLogger(__name__)

# Definición de estilos de masterización
MASTER_STYLES = {
    "streaming": {
        "target_lufs": -14.0,
        "description": "Loudness estándar para Spotify/Apple Music",
        "plugins": ["compressor", "eq", "limiter"],
    },
    "vinyl": {
        "target_lufs": -16.0,
        "description": "Optimizado para vinilo (más dinámica)",
        "plugins": ["highpass", "compressor", "eq", "limiter"],
    },
    "cd": {
        "target_lufs": -9.0,
        "description": "CD clásico (loudness war)",
        "plugins": ["multiband_comp", "eq", "limiter"],
    },
    "loudness_war": {
        "target_lufs": -4.0,
        "description": "Máxima loudness (riesgo de clipping)",
        "plugins": ["aggressive_comp", "limiter"],
    },
    "dynamic": {
        "target_lufs": -18.0,
        "description": "Conservar dinámica natural",
        "plugins": ["gentle_comp", "eq"],
    },
}

# Definición de pipelines
PIPELINE_MODES = {
    "quick": {
        "duration_seconds": 5,
        "phases": [1, 2, 4],
        "description": "Análisis rápido (raw, norm, clasificación)",
    },
    "mode_c": {
        "duration_seconds": 30,
        "phases": [1, 2, 3, 4, 5, 6, 7, 8],
        "description": "Pipeline completo (8 fases)",
    },
    "deep": {
        "duration_seconds": 120,
        "phases": [1, 2, 3, 4, 5, 6, 7, 8],
        "description": "Análisis profundo con iteraciones",
    },
}

# =============================================================================
# VIRTUAL ENGINEER
# =============================================================================


class VirtualEngineer:
    """
    Ingeniero Virtual: motor de decisión automática basado en análisis.
    
    Métodos principales:
    - decide_pipeline()     — Elegir pipeline óptimo
    - decide_master_style() — Elegir estilo de masterización
    - decide_priority()     — Calcular prioridad
    - decide_delegation()   — Decidir a qué módulo delegar
    - generate_recommendations() — Generar recomendaciones
    """

    def __init__(self):
        self.vx11_bridge = VX11Bridge()
        self.decision_history: Dict[str, Any] = {}

    # =========================================================================
    # MÉTODO 1: decide_pipeline
    # =========================================================================

    async def decide_pipeline(
        self,
        audio_analysis: AudioAnalysis,
        user_preference: str = None,
    ) -> Dict[str, Any]:
        """
        Decidir pipeline óptimo basado en análisis.
        
        Args:
            audio_analysis: Análisis completo del audio
            user_preference: Preferencia del usuario (quick, mode_c, deep)
            
        Retorna:
        {
            "status": "success",
            "pipeline_mode": "mode_c",
            "rationale": "Full analysis recommended for complex audio",
            "estimated_time_seconds": 30,
            "phases": [1, 2, 3, 4, 5, 6, 7, 8],
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("virtual_engineer", "DECIDE_PIPELINE: iniciando", level="INFO")
            
            # Si hay preferencia del usuario, respetarla
            if user_preference and user_preference in PIPELINE_MODES:
                write_log("virtual_engineer", f"DECIDE_PIPELINE: usando preferencia {user_preference}", level="INFO")
                mode = user_preference
                rationale = f"User preference: {user_preference}"
            else:
                # Lógica heurística basada en análisis
                complexity_score = self._calculate_complexity_score(audio_analysis)
                
                if complexity_score > 0.7:
                    mode = "deep"
                    rationale = "High complexity detected (multiple issues, unusual spectral characteristics)"
                elif complexity_score > 0.4:
                    mode = "mode_c"
                    rationale = "Moderate complexity (standard analysis recommended)"
                else:
                    mode = "quick"
                    rationale = "Low complexity (quick analysis sufficient)"
            
            pipeline_config = PIPELINE_MODES[mode]
            
            write_log("virtual_engineer", f"DECIDE_PIPELINE: mode={mode}, complexity={self._calculate_complexity_score(audio_analysis):.2f}", level="INFO")
            
            return {
                "status": "success",
                "pipeline_mode": mode,
                "rationale": rationale,
                "estimated_time_seconds": pipeline_config["duration_seconds"],
                "phases": pipeline_config["phases"],
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("virtual_engineer", e)
            write_log("virtual_engineer", f"DECIDE_PIPELINE_ERROR: {str(e)}", level="ERROR")
            # Fallback a mode_c (safest)
            return {
                "status": "error",
                "pipeline_mode": "mode_c",
                "message": str(e),
            }

    # =========================================================================
    # MÉTODO 2: decide_master_style
    # =========================================================================

    async def decide_master_style(
        self,
        audio_analysis: AudioAnalysis,
        genre: str = None,
        user_preference: str = None,
    ) -> Dict[str, Any]:
        """
        Decidir estilo de masterización óptimo.
        
        Args:
            audio_analysis: Análisis completo
            genre: Género de música (pop, rock, jazz, classical, electronic, etc.)
            user_preference: Preferencia del usuario (streaming, vinyl, cd, etc.)
            
        Retorna:
        {
            "status": "success",
            "master_style": "streaming",
            "target_lufs": -14.0,
            "rationale": "Streaming platform standard...",
            "plugins": ["compressor", "eq", "limiter"],
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("virtual_engineer", f"DECIDE_MASTER_STYLE: genre={genre}, preference={user_preference}", level="INFO")
            
            # Si hay preferencia del usuario, respetarla
            if user_preference and user_preference in MASTER_STYLES:
                style = user_preference
                rationale = f"User preference: {user_preference}"
            else:
                # Lógica heurística basada en género y análisis
                style = self._choose_master_style_heuristic(audio_analysis, genre)
                rationale = f"Auto-selected based on genre='{genre}' and analysis"
            
            style_config = MASTER_STYLES[style]
            
            # Calcular parámetros específicos basados en análisis
            lufs_target = style_config["target_lufs"]
            current_lufs = audio_analysis.lufs_integrated
            
            if current_lufs is not None:
                gain_adjustment = lufs_target - current_lufs
            else:
                gain_adjustment = 0.0
            
            write_log("virtual_engineer", f"DECIDE_MASTER_STYLE: style={style}, lufs_adjustment={gain_adjustment:.1f}dB", level="INFO")
            
            return {
                "status": "success",
                "master_style": style,
                "target_lufs": lufs_target,
                "current_lufs": current_lufs,
                "gain_adjustment_db": gain_adjustment,
                "rationale": rationale,
                "plugins": style_config["plugins"],
                "description": style_config["description"],
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("virtual_engineer", e)
            write_log("virtual_engineer", f"DECIDE_MASTER_STYLE_ERROR: {str(e)}", level="ERROR")
            # Fallback a streaming (safest)
            return {
                "status": "error",
                "master_style": "streaming",
                "message": str(e),
            }

    # =========================================================================
    # MÉTODO 3: decide_priority
    # =========================================================================

    async def decide_priority(
        self,
        audio_analysis: AudioAnalysis,
        user_priority: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Decidir prioridad de procesamiento (1-10).
        
        Args:
            audio_analysis: Análisis completo
            user_priority: Prioridad sugerida por usuario (1-10)
            
        Retorna:
        {
            "status": "success",
            "priority": 7,
            "rationale": "High complexity + high issue count",
            "issues_severity": "high",
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            if user_priority is not None and 1 <= user_priority <= 10:
                priority = user_priority
                rationale = f"User specified: {user_priority}"
            else:
                # Heurística: basada en issues y complejidad
                issue_count = len(audio_analysis.issues or [])
                complexity = self._calculate_complexity_score(audio_analysis)
                
                # Escala 1-10
                priority = min(10, max(1, int(2 + issue_count * 1.5 + complexity * 5)))
                
                if issue_count > 3:
                    severity = "critical"
                elif issue_count > 1:
                    severity = "high"
                elif complexity > 0.5:
                    severity = "medium"
                else:
                    severity = "low"
                
                rationale = f"{severity} severity ({issue_count} issues, complexity={complexity:.2f})"
            
            write_log("virtual_engineer", f"DECIDE_PRIORITY: priority={priority}, issues={len(audio_analysis.issues or [])}", level="INFO")
            
            return {
                "status": "success",
                "priority": priority,
                "rationale": rationale,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("virtual_engineer", e)
            return {
                "status": "error",
                "priority": 5,  # Fallback neutro
                "message": str(e),
            }

    # =========================================================================
    # MÉTODO 4: decide_delegation
    # =========================================================================

    async def decide_delegation(
        self,
        audio_analysis: AudioAnalysis,
        pipeline_mode: str = "mode_c",
    ) -> Dict[str, Any]:
        """
        Decidir delegación: ¿a qué módulos enviar?
        
        Args:
            audio_analysis: Análisis completo
            pipeline_mode: Pipeline seleccionado
            
        Retorna:
        {
            "status": "success",
            "delegations": {
                "madre": {
                    "action": "create_child_hija",
                    "rationale": "Complex task requires Madre orchestration"
                },
                "switch": {
                    "action": "route_to_hermes",
                    "rationale": "Request DSP resources"
                },
                "hormiguero": {
                    "action": "queue_batch",
                    "rationale": "Multiple files detected"
                }
            },
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("virtual_engineer", "DECIDE_DELEGATION: iniciando", level="INFO")
            
            delegations = {}
            
            # Siempre notificar a Madre (orquestador)
            delegations["madre"] = {
                "action": "notify_event",
                "event": "audio_analysis_available",
                "rationale": "Madre coordinates all VX11 activities",
            }
            
            # Delegación a Switch si hay complejidad
            if len(audio_analysis.issues or []) > 2 or self._calculate_complexity_score(audio_analysis) > 0.5:
                delegations["switch"] = {
                    "action": "request_routing",
                    "rationale": "Complex issues require Switch routing intelligence",
                }
            
            # Delegación a Hormiguero si hay batch jobs
            if pipeline_mode == "deep":
                delegations["hormiguero"] = {
                    "action": "queue_iterative_analysis",
                    "rationale": "Deep mode requires iterative processing via Hormiguero",
                }
            
            write_log("virtual_engineer", f"DECIDE_DELEGATION: {len(delegations)} delegaciones decididas", level="INFO")
            
            return {
                "status": "success",
                "delegations": delegations,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("virtual_engineer", e)
            write_log("virtual_engineer", f"DECIDE_DELEGATION_ERROR: {str(e)}", level="ERROR")
            return {
                "status": "error",
                "message": str(e),
            }

    # =========================================================================
    # MÉTODO 5: generate_recommendations
    # =========================================================================

    async def generate_recommendations(
        self,
        audio_analysis: AudioAnalysis,
    ) -> Dict[str, Any]:
        """
        Generar recomendaciones de acción para Madre/Operador.
        
        Retorna:
        {
            "status": "success",
            "recommendations": [
                {
                    "action": "apply_compressor",
                    "reason": "High dynamic range detected",
                    "priority": "high",
                    "estimated_improvement": "8 dB reduction"
                },
                ...
            ],
            "next_steps": [
                "Review FX chain recommendations",
                "Approve master style selection",
                "Generate REAPER preset"
            ],
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("virtual_engineer", "GENERATE_RECOMMENDATIONS: iniciando", level="INFO")
            
            recommendations = []
            
            # Recomendaciones basadas en issues detectados
            for issue in audio_analysis.issues or []:
                if issue == "clipping_detected":
                    recommendations.append({
                        "action": "reduce_gain",
                        "reason": "Digital clipping detected",
                        "priority": "critical",
                        "estimated_improvement": "Eliminate clipping",
                    })
                
                elif issue == "excessive_bass":
                    recommendations.append({
                        "action": "apply_highpass_filter",
                        "reason": "Excessive bass frequencies detected",
                        "priority": "high",
                        "estimated_improvement": "Balance spectral content",
                    })
                
                elif issue == "lacking_highs":
                    recommendations.append({
                        "action": "apply_eq_high_shelf",
                        "reason": "Insufficient high frequencies",
                        "priority": "medium",
                        "estimated_improvement": "Add presence and clarity",
                    })
                
                elif issue == "high_dynamic_range":
                    recommendations.append({
                        "action": "apply_compressor",
                        "reason": "High dynamic range detected",
                        "priority": "medium",
                        "estimated_improvement": "Tame peaks, lift floor",
                    })
                
                elif issue == "over_compressed":
                    recommendations.append({
                        "action": "reduce_compression",
                        "reason": "Audio already heavily compressed",
                        "priority": "high",
                        "estimated_improvement": "Restore natural dynamics",
                    })
            
            # Recomendaciones basadas en clasificación
            if audio_analysis.genre == "quiet":
                recommendations.append({
                    "action": "apply_gentle_compression",
                    "reason": "Quiet material benefits from gentle compression",
                    "priority": "low",
                    "estimated_improvement": "Improve consistency",
                })
            
            # Pasos siguientes
            next_steps = [
                "Review FX chain recommendations above",
                "Approve master style selection",
                "Generate REAPER preset from analysis",
                "Preview master before rendering",
            ]
            
            write_log("virtual_engineer", f"GENERATE_RECOMMENDATIONS: {len(recommendations)} recomendaciones", level="INFO")
            
            return {
                "status": "success",
                "recommendations": recommendations,
                "next_steps": next_steps,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("virtual_engineer", e)
            return {
                "status": "error",
                "message": str(e),
            }

    # =========================================================================
    # HELPERS: Heuristics
    # =========================================================================

    def _calculate_complexity_score(self, audio_analysis: AudioAnalysis) -> float:
        """
        Calcular puntuación de complejidad (0-1) basada en análisis.
        """
        score = 0.0
        
        # Factor: cantidad de issues
        issue_count = len(audio_analysis.issues or [])
        score += min(0.3, issue_count * 0.1)
        
        # Factor: spectral imbalance
        if hasattr(audio_analysis, 'bass_power') and hasattr(audio_analysis, 'treble_power'):
            imbalance = abs(audio_analysis.bass_power - audio_analysis.treble_power)
            score += min(0.2, imbalance / 50)
        
        # Factor: dynamic range
        if hasattr(audio_analysis, 'dynamic_range'):
            if audio_analysis.dynamic_range > 15:
                score += 0.3
            elif audio_analysis.dynamic_range > 10:
                score += 0.15
        
        # Factor: spectral characteristics
        if hasattr(audio_analysis, 'spectral_flatness'):
            if audio_analysis.spectral_flatness < 0.5:  # Picos pronunciados
                score += 0.2
        
        return min(1.0, score)

    def _choose_master_style_heuristic(
        self,
        audio_analysis: AudioAnalysis,
        genre: Optional[str],
    ) -> str:
        """
        Elegir estilo de masterización basado en heurísticas.
        """
        # Lógica género -> estilo
        if genre:
            if "classical" in genre.lower() or "acoustic" in genre.lower():
                return "dynamic"
            elif "vinyl" in genre.lower() or "jazz" in genre.lower():
                return "vinyl"
            elif "electronic" in genre.lower() or "pop" in genre.lower():
                return "streaming"
        
        # Lógica basada en análisis si no hay género
        if hasattr(audio_analysis, 'dynamic_range') and audio_analysis.dynamic_range > 15:
            return "dynamic"  # Conservar dinámica
        
        # Default a streaming (más común)
        return "streaming"


# Instancia global
virtual_engineer = VirtualEngineer()
