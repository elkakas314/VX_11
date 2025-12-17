"""
Ingeniero Virtual: Agente IA que sugiere procesamiento basado en análisis
Usa Switch router para proporcionar recomendaciones inteligentes.
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import httpx

from shubniggurath.pro.dsp_engine import AudioAnalysisResult
from shubniggurath.pro.dsp_fx import EffectConfig, EffectType, PRESET_MASTERING, PRESET_CLEAN_VOICE, PRESET_BRIGHT
from config.settings import settings


class VirtualEngineer:
    """Ingeniero Virtual: IA que recomienda procesamiento"""
    
    def __init__(self):
        self.switch_url = f"http://127.0.0.1:{settings.switch_port}"
        self.preset_library = {
            "mastering": PRESET_MASTERING,
            "clean_voice": PRESET_CLEAN_VOICE,
            "bright": PRESET_BRIGHT,
        }
    
    async def analyze_and_recommend(
        self,
        analysis: AudioAnalysisResult,
        user_intent: Optional[str] = None,
        target_lufs: float = -14,
    ) -> Dict[str, Any]:
        """Analizar y recomendar procesamiento"""
        
        # Construir prompt para Switch
        issues_str = ", ".join(analysis.issues) if analysis.issues else "ninguno"
        analysis_summary = f"""
        Análisis de Audio:
        - Pico: {analysis.peak_db:.1f} dB
        - RMS: {analysis.rms_db:.1f} dB
        - LUFS: {analysis.lufs:.1f}
        - Rango dinámico: {analysis.dynamic_range_db:.1f} dB
        - Centroide espectral: {analysis.spectral_centroid_hz:.0f} Hz
        - Transitorios: {analysis.transient_count}
        - Issues detectados: {issues_str}
        
        Intención del usuario: {user_intent or "Masterización general"}
        Target LUFS: {target_lufs}
        
        Recomienda una cadena de FX (EQ, compresión, limitación) en JSON.
        Incluye parámetros específicos. Responde SOLO con JSON valido.
        """
        
        try:
            # Consultar Switch/IA
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.switch_url}/route",
                    json={
                        "prompt": analysis_summary,
                        "task_type": "audio_processing_recommendation",
                        "mode": "ECO",  # Rápido y eficiente
                    },
                    headers={"X-VX11-Token": settings.api_token},
                    timeout=15,
                )
                resp.raise_for_status()
                
                ai_response = resp.json()
                recommendation_text = ai_response.get("response", "")
        
        except Exception as e:
            # Fallback: usar recomendaciones basadas en reglas
            return self._rule_based_recommendation(analysis, user_intent, target_lufs, str(e))
        
        # Parsear respuesta IA
        try:
            # Buscar JSON en respuesta
            import re
            json_match = re.search(r'\{.*\}', recommendation_text, re.DOTALL)
            if json_match:
                fx_config = json.loads(json_match.group())
            else:
                raise ValueError("No JSON en respuesta IA")
        
        except Exception as e:
            # Fallback si parseo falla
            return self._rule_based_recommendation(analysis, user_intent, target_lufs, f"IA parse error: {e}")
        
        return {
            "success": True,
            "method": "ai",
            "fx_chain": fx_config,
            "reasoning": recommendation_text,
            "analysis": asdict(analysis),
            "target_lufs": target_lufs,
        }
    
    def _rule_based_recommendation(
        self,
        analysis: AudioAnalysisResult,
        user_intent: Optional[str],
        target_lufs: float,
        ai_error: str = "",
    ) -> Dict[str, Any]:
        """Recomendaciones basadas en reglas (fallback)"""
        
        fx_chain = []
        reasoning = []
        
        # 1. High-pass filter
        if analysis.spectral_centroid_hz and analysis.spectral_centroid_hz < 100:
            fx_chain.append({
                "type": "highpass",
                "enabled": True,
                "params": {"cutoff_hz": 20, "order": 2},
            })
            reasoning.append("High-pass filter para remover ruido de muy baja frecuencia")
        
        # 2. EQ basado en contenido
        eq_params = {"low_gain_db": 0, "mid_gain_db": 0, "high_gain_db": 0}
        
        if "clipping" in analysis.issues:
            eq_params["high_gain_db"] = -2
            reasoning.append("Reducir altas para suavizar clipping")
        
        if analysis.dynamic_range_db < 6:
            reasoning.append("Audio muy comprimido dinámicamente")
        elif analysis.dynamic_range_db > 20:
            eq_params["mid_gain_db"] = 1
            reasoning.append("Audio dinámico: añadir presencia en mids")
        
        if "dc_offset" in analysis.issues:
            eq_params["low_gain_db"] = -1
            reasoning.append("DC offset detectado: reducir bajos")
        
        fx_chain.append({
            "type": "eq",
            "enabled": True,
            "params": eq_params,
        })
        reasoning.append(f"EQ: low={eq_params['low_gain_db']}, mid={eq_params['mid_gain_db']}, high={eq_params['high_gain_db']}")
        
        # 3. Compresión según loudness
        if analysis.lufs < target_lufs - 3:
            # Muy suave: comprimir suave
            fx_chain.append({
                "type": "compressor",
                "enabled": True,
                "params": {
                    "threshold_db": -20,
                    "ratio": 2.0,
                    "attack_ms": 15,
                    "release_ms": 150,
                },
            })
            reasoning.append(f"Compresión suave (ratio 2:1) para llevar a {target_lufs} LUFS")
        
        elif analysis.lufs > target_lufs + 3:
            # Muy fuerte: comprimir agresivo
            fx_chain.append({
                "type": "compressor",
                "enabled": True,
                "params": {
                    "threshold_db": -15,
                    "ratio": 4.0,
                    "attack_ms": 5,
                    "release_ms": 100,
                },
            })
            reasoning.append(f"Compresión agresiva (ratio 4:1) para llevar a {target_lufs} LUFS")
        
        else:
            fx_chain.append({
                "type": "compressor",
                "enabled": True,
                "params": {
                    "threshold_db": -18,
                    "ratio": 3.0,
                    "attack_ms": 10,
                    "release_ms": 120,
                },
            })
            reasoning.append("Compresión balanceada (ratio 3:1)")
        
        # 4. Limiter de seguridad
        if analysis.peak_db > -3:
            fx_chain.append({
                "type": "limiter",
                "enabled": True,
                "params": {"threshold_db": -3},
            })
            reasoning.append("Limitador de seguridad a -3 dB")
        
        return {
            "success": True,
            "method": "rule_based",
            "fx_chain": fx_chain,
            "reasoning": "; ".join(reasoning),
            "analysis": asdict(analysis),
            "target_lufs": target_lufs,
            "ai_error": ai_error if ai_error else None,
        }
    
    async def get_preset_recommendation(
        self,
        preset_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Obtener preset predefinido"""
        return self.preset_library.get(preset_name)
    
    async def suggest_genre_preset(
        self,
        genre: str,
        analysis: AudioAnalysisResult,
    ) -> Dict[str, Any]:
        """Sugerir preset según género (expandible)"""
        
        genre_lower = genre.lower()
        
        if "voice" in genre_lower or "vocal" in genre_lower or "speech" in genre_lower:
            preset_name = "clean_voice"
        elif "master" in genre_lower or "master" in genre_lower:
            preset_name = "mastering"
        elif "bright" in genre_lower or "pop" in genre_lower or "electronic" in genre_lower:
            preset_name = "bright"
        else:
            preset_name = "mastering"
        
        preset = self.preset_library.get(preset_name)
        
        return {
            "genre": genre,
            "suggested_preset": preset_name,
            "fx_chain": preset.get("effects", []) if preset else [],
        }
    
    def get_available_presets(self) -> Dict[str, List[str]]:
        """Listar presets disponibles"""
        return {
            "presets": list(self.preset_library.keys()),
        }


# Singleton global
_engineer_instance = None


def get_virtual_engineer() -> VirtualEngineer:
    """Obtener ingeniero virtual global"""
    global _engineer_instance
    if _engineer_instance is None:
        _engineer_instance = VirtualEngineer()
    return _engineer_instance
