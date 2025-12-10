"""
Shub Router para Switch

Detecta tareas de audio/DSP y enruta hacia Shubniggurath.
Define interfaces para audio processing, restoration, arrangement.
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
import re

log = logging.getLogger("vx11.switch.shub_router")


class AudioDomain(Enum):
    """Dominios de procesamiento de audio en Shub"""
    
    RESTORATION = "restoration"  # Denoise, declip, etc
    ARRANGEMENT = "arrangement"  # Arreglos, recombinación
    ANALYSIS = "analysis"  # Análisis espectral, armónico
    MIXING = "mixing"  # Mezcla, balanceo
    MASTERING = "mastering"  # Mastering final
    EFFECTS = "effects"  # Efectos y procesamiento
    SYNTHESIS = "synthesis"  # Síntesis de audio
    REAPER_CONTROL = "reaper_control"  # Control de REAPER


class ShubRouter:
    """
    Router que detecta tareas de audio y las enruta hacia Shub.
    
    Identifica keywords/patrones que indican procesamiento de audio,
    selecciona el engine correcto de Shub, y prepara payload.
    """
    
    # Patrones para detección de audio
    AUDIO_KEYWORDS = {
        AudioDomain.RESTORATION: [
            r"(denoise|noise reduction|clean|restore|remove noise)",
            r"(declip|remove clipping|fix clipping)",
            r"(restore|repair audio|fix|recover)",
            r"(restoration|audio restoration|audio repair)",
        ],
        AudioDomain.ARRANGEMENT: [
            r"(arrange|arreglo|arrangement|rearrange|recombine)",
            r"(mix|mezcla|orchestrate|orchestration)",
            r"(combine tracks|merge|fusion)",
        ],
        AudioDomain.ANALYSIS: [
            r"(analyze|analysis|spectral|harmonic|frequency)",
            r"(detect|identify|recognize).*(instrument|vocal|sound)",
            r"(spectrum|spectrogram|FFT)",
        ],
        AudioDomain.MIXING: [
            r"(mix|mezcla|balance|EQ|equalize|compress)",
            r"(level|volume|pan|panning)",
            r"(EQ|equalization|equalizer)",
        ],
        AudioDomain.MASTERING: [
            r"(master|mastering|master audio|loudness)",
            r"(loudness normalization|LUFS|prepare for release)",
            r"(broadcast|streaming quality|commercial)",
        ],
        AudioDomain.EFFECTS: [
            r"(effect|reverb|delay|distortion|overdrive)",
            r"(chorus|flanger|phaser|compression)",
            r"(add effect|apply filter|process)",
        ],
        AudioDomain.SYNTHESIS: [
            r"(synthesize|synthesis|generate|create audio)",
            r"(synth|pad|lead|bass generation)",
        ],
        AudioDomain.REAPER_CONTROL: [
            r"(reaper|DAW|digital audio workstation)",
            r"(reaper control|reaper automation|reaper script)",
            r"(open reaper|launch reaper|reaper project)",
        ],
    }
    
    # Patrones que indican tarea de audio
    AUDIO_TRIGGERS = [
        r"(audio|sound|música|music|daw|reaper)",
        r"(shub|shubniggurath|restore|mix|master)",
        r"(track|vocal|instrument|drums|beat)",
        r"(WAV|MP3|FLAC|OGG|audio file)",
    ]
    
    def __init__(self, shub_endpoint: str = "http://switch:8007"):
        self.shub_endpoint = shub_endpoint
        self.enabled = True
    
    def should_route_to_shub(self, query: str, context: Dict[str, Any] = None) -> bool:
        """
        Determina si una tarea debe routed hacia Shub.
        
        Args:
            query: Texto de la consulta
            context: Contexto adicional (opcional)
        
        Returns:
            True si la tarea debe ir a Shub
        """
        query_lower = query.lower()
        
        # Revisar triggers de audio
        for trigger in self.AUDIO_TRIGGERS:
            if re.search(trigger, query_lower):
                log.debug(f"Audio trigger detectado: {trigger}")
                return True
        
        # Revisar contexto
        if context:
            if context.get("audio_file"):
                return True
            if context.get("is_audio_task"):
                return True
            if context.get("format") in ["wav", "mp3", "flac", "ogg", "aiff"]:
                return True
        
        return False
    
    def detect_audio_domain(self, query: str, context: Dict[str, Any] = None) -> Optional[AudioDomain]:
        """
        Detecta el dominio de audio específico de la tarea.
        
        Args:
            query: Texto de la consulta
            context: Contexto adicional
        
        Returns:
            AudioDomain detectado o None
        """
        query_lower = query.lower()
        scores: Dict[AudioDomain, int] = {}
        
        # Revisar cada dominio
        for domain, patterns in self.AUDIO_KEYWORDS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    scores[domain] = scores.get(domain, 0) + 1
        
        # Retornar dominio con mayor score
        if scores:
            best_domain = max(scores, key=scores.get)
            log.debug(f"Audio domain detectado: {best_domain.value} (score: {scores[best_domain]})")
            return best_domain
        
        # Default: analysis
        return AudioDomain.ANALYSIS
    
    def build_shub_payload(self, 
                          query: str, 
                          domain: AudioDomain,
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Construye payload para enviar a Shub.
        
        Args:
            query: Texto original de consulta
            domain: Dominio de audio detectado
            context: Contexto adicional
        
        Returns:
            Payload estructurado para Shub
        """
        payload = {
            "query": query,
            "domain": domain.value,
            "context": context or {},
            "parameters": self._extract_parameters(query, domain),
        }
        
        return payload
    
    def _extract_parameters(self, query: str, domain: AudioDomain) -> Dict[str, Any]:
        """Extrae parámetros específicos según dominio"""
        params = {}
        query_lower = query.lower()
        
        # Parámetros comunes
        if "high quality" in query_lower or "professional" in query_lower:
            params["quality"] = "professional"
        elif "draft" in query_lower or "preview" in query_lower:
            params["quality"] = "draft"
        else:
            params["quality"] = "standard"
        
        # Parámetros por dominio
        if domain == AudioDomain.RESTORATION:
            if "denoise" in query_lower or "noise" in query_lower:
                params["operation"] = "denoise"
            elif "declip" in query_lower or "clipping" in query_lower:
                params["operation"] = "declip"
            else:
                params["operation"] = "restore"
            
            # Intensidad
            if "aggressive" in query_lower or "heavy" in query_lower:
                params["intensity"] = "heavy"
            elif "light" in query_lower or "gentle" in query_lower:
                params["intensity"] = "light"
            else:
                params["intensity"] = "medium"
        
        elif domain == AudioDomain.MASTERING:
            # Target loudness
            if "LUFS" in query:
                import re as regex
                match = regex.search(r'(-\d+\.?\d*)\s*LUFS', query)
                if match:
                    params["target_loudness"] = float(match.group(1))
                else:
                    params["target_loudness"] = -14.0
            else:
                params["target_loudness"] = -14.0
            
            # Género
            if "classical" in query_lower:
                params["genre"] = "classical"
            elif "rock" in query_lower:
                params["genre"] = "rock"
            elif "pop" in query_lower:
                params["genre"] = "pop"
            elif "electronic" in query_lower or "edm" in query_lower:
                params["genre"] = "electronic"
            else:
                params["genre"] = "general"
        
        elif domain == AudioDomain.MIXING:
            if "EQ" in query or "equalize" in query_lower:
                params["operation"] = "eq"
            elif "compress" in query_lower or "compression" in query_lower:
                params["operation"] = "compress"
            elif "reverb" in query_lower:
                params["operation"] = "reverb"
            else:
                params["operation"] = "balance"
        
        elif domain == AudioDomain.ARRANGEMENT:
            if "orchestrate" in query_lower:
                params["style"] = "orchestral"
            elif "minimal" in query_lower:
                params["style"] = "minimal"
            else:
                params["style"] = "hybrid"
        
        return params
    
    def get_shub_endpoint(self, domain: AudioDomain) -> str:
        """Retorna endpoint específico de Shub según dominio"""
        endpoint_map = {
            AudioDomain.RESTORATION: f"{self.shub_endpoint}/shub/restore",
            AudioDomain.ARRANGEMENT: f"{self.shub_endpoint}/shub/arrange",
            AudioDomain.ANALYSIS: f"{self.shub_endpoint}/shub/analyze",
            AudioDomain.MIXING: f"{self.shub_endpoint}/shub/mix",
            AudioDomain.MASTERING: f"{self.shub_endpoint}/shub/master",
            AudioDomain.EFFECTS: f"{self.shub_endpoint}/shub/effects",
            AudioDomain.SYNTHESIS: f"{self.shub_endpoint}/shub/synthesize",
            AudioDomain.REAPER_CONTROL: f"{self.shub_endpoint}/shub/reaper",
        }
        return endpoint_map.get(domain, f"{self.shub_endpoint}/shub/process")
    
    def can_handle_locally(self, domain: AudioDomain) -> bool:
        """Indica si Switch puede manejar esta tarea localmente"""
        # Audio processing requiere Shub, nunca local
        return False
