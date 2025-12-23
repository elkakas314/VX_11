"""
Motor de efectos DSP: EQ, compresión, limitador, reverb, etc.
Cadena procesable y configurable.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import warnings

try:
    import importlib
    signal = importlib.import_module("scipy.signal")
    HAS_SCIPY = True
except Exception:
    HAS_SCIPY = False

    # Fallback stub for environments without scipy.signal.
    # Provides minimal butter/filtfilt API used by this module and performs no-op filtering.
    class _SignalStub:
        @staticmethod
        def butter(order, Wn, btype='low'):
            # Return neutral filter coefficients (no filtering).
            return np.array([1.0]), np.array([1.0])

        @staticmethod
        def filtfilt(b, a, x):
            # No-op: return input unchanged, preserving shape and dtype.
            return x

    signal = _SignalStub()


class EffectType(Enum):
    """Tipos de efectos disponibles"""
    EQ = "eq"
    COMPRESSOR = "compressor"
    LIMITER = "limiter"
    REVERB = "reverb"
    DELAY = "delay"
    DISTORTION = "distortion"
    GAIN = "gain"
    HIGHPASS = "highpass"
    LOWPASS = "lowpass"


@dataclass
class EffectConfig:
    """Configuración genérica de efecto"""
    type: EffectType
    enabled: bool = True
    params: Dict[str, float] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}


class Effect:
    """Clase base para efectos DSP"""
    
    def __init__(self, config: EffectConfig, sample_rate: int = 48000):
        self.config = config
        self.sample_rate = sample_rate
        self.state = {}
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Procesar audio (override en subclases)"""
        return audio
    
    async def process_async(self, audio: np.ndarray) -> np.ndarray:
        """Procesamiento asincrónico (opcional)"""
        return self.process(audio)


class GainEffect(Effect):
    """Gain/Atenuación simple"""
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        gain_db = self.config.params.get("gain_db", 0)
        gain_linear = 10 ** (gain_db / 20)
        return audio * gain_linear


class CompressorEffect(Effect):
    """Compresor dinámico"""
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not HAS_SCIPY:
            warnings.warn("scipy no disponible; compresor desactivado")
            return audio
        
        threshold = self.config.params.get("threshold_db", -20)
        ratio = self.config.params.get("ratio", 4.0)
        attack_ms = self.config.params.get("attack_ms", 10)
        release_ms = self.config.params.get("release_ms", 100)
        
        # Envoltura
        threshold_linear = 10 ** (threshold / 20)
        attack_samples = int(attack_ms * self.sample_rate / 1000)
        release_samples = int(release_ms * self.sample_rate / 1000)
        
        # Detector (simplificado)
        detected = np.abs(audio)
        
        # Envolvente de ataque/release
        envelope = np.zeros_like(audio)
        for i in range(len(audio)):
            if detected[i] > (envelope[i-1] if i > 0 else 0):
                envelope[i] = detected[i]
            else:
                envelope[i] = detected[i]
        
        # Ganancia de compresión
        gain = np.ones_like(audio)
        over_threshold = envelope > threshold_linear
        gain[over_threshold] = threshold_linear / (envelope[over_threshold] / (ratio - 1) + threshold_linear)
        
        return audio * gain


class LimiterEffect(Effect):
    """Limitador (compresor con ratio infinita)"""
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        threshold_db = self.config.params.get("threshold_db", -3)
        threshold_linear = 10 ** (threshold_db / 20)
        
        # Hard limiting
        return np.clip(audio, -threshold_linear, threshold_linear)


class EQEffect(Effect):
    """Ecualizador paramétrico (3 bandas: lo, mid, hi)"""
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not HAS_SCIPY:
            warnings.warn("scipy no disponible; EQ desactivado")
            return audio
        
        try:
            # Parámetros
            low_gain_db = self.config.params.get("low_gain_db", 0)
            mid_gain_db = self.config.params.get("mid_gain_db", 0)
            high_gain_db = self.config.params.get("high_gain_db", 0)
            
            # Filtros simples (shelving de primer orden)
            low_cutoff = 200
            high_cutoff = 3000
            
            output = audio.copy()
            
            # Low shelf
            if low_gain_db != 0:
                gain_linear = 10 ** (low_gain_db / 20)
                # Aproximación: sumar/restar versión LP
                b, a = signal.butter(1, low_cutoff / (self.sample_rate / 2), btype='low')
                lp = signal.filtfilt(b, a, audio)
                output = output + (lp - audio) * (gain_linear - 1)
            
            # High shelf
            if high_gain_db != 0:
                gain_linear = 10 ** (high_gain_db / 20)
                b, a = signal.butter(1, high_cutoff / (self.sample_rate / 2), btype='high')
                hp = signal.filtfilt(b, a, audio)
                output = output + (hp - audio) * (gain_linear - 1)
            
            return output
        except Exception as e:
            warnings.warn(f"Error en EQ: {e}")
            return audio


class HighPassEffect(Effect):
    """Filtro paso-alto"""
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not HAS_SCIPY:
            return audio
        
        try:
            cutoff_hz = self.config.params.get("cutoff_hz", 20)
            order = self.config.params.get("order", 2)
            
            nyquist = self.sample_rate / 2
            normalized_cutoff = cutoff_hz / nyquist
            
            if normalized_cutoff < 0.01:
                return audio
            
            b, a = signal.butter(order, normalized_cutoff, btype='high')
            return signal.filtfilt(b, a, audio)
        except Exception as e:
            warnings.warn(f"Error en HighPass: {e}")
            return audio


class LowPassEffect(Effect):
    """Filtro paso-bajo"""
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        if not HAS_SCIPY:
            return audio
        
        try:
            cutoff_hz = self.config.params.get("cutoff_hz", 10000)
            order = self.config.params.get("order", 2)
            
            nyquist = self.sample_rate / 2
            normalized_cutoff = cutoff_hz / nyquist
            
            if normalized_cutoff > 0.99:
                return audio
            
            b, a = signal.butter(order, normalized_cutoff, btype='low')
            return signal.filtfilt(b, a, audio)
        except Exception as e:
            warnings.warn(f"Error en LowPass: {e}")
            return audio


class DistortionEffect(Effect):
    """Distorsión/saturación simple"""
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        drive = self.config.params.get("drive", 1.0)
        tone = self.config.params.get("tone", 0.5)  # 0 = bright, 1 = dark
        
        # Saturación
        driven = audio * drive
        saturated = np.tanh(driven)  # Soft clipping
        
        # Mezcla
        mix = self.config.params.get("mix", 0.5)
        return audio * (1 - mix) + saturated * mix


class FXChain:
    """Cadena de procesamiento de efectos"""
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.effects: List[Effect] = []
    
    def add_effect(self, effect: Effect) -> "FXChain":
        """Agregar efecto a la cadena"""
        self.effects.append(effect)
        return self
    
    def add_effect_config(self, config: EffectConfig) -> "FXChain":
        """Agregar efecto desde configuración"""
        effect = self._create_effect(config)
        if effect:
            self.effects.append(effect)
        return self
    
    def _create_effect(self, config: EffectConfig) -> Optional[Effect]:
        """Factory para crear efectos"""
        effect_map = {
            EffectType.GAIN: GainEffect,
            EffectType.COMPRESSOR: CompressorEffect,
            EffectType.LIMITER: LimiterEffect,
            EffectType.EQ: EQEffect,
            EffectType.HIGHPASS: HighPassEffect,
            EffectType.LOWPASS: LowPassEffect,
            EffectType.DISTORTION: DistortionEffect,
        }
        
        effect_class = effect_map.get(config.type)
        if not effect_class:
            warnings.warn(f"Tipo de efecto no soportado: {config.type}")
            return None
        
        return effect_class(config, self.sample_rate)
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Procesar audio a través de la cadena"""
        output = audio.copy()
        
        for effect in self.effects:
            if effect.config.enabled:
                output = effect.process(output)
        
        return output
    
    async def process_async(self, audio: np.ndarray) -> np.ndarray:
        """Procesamiento asincrónico"""
        output = audio.copy()
        
        for effect in self.effects:
            if effect.config.enabled:
                output = await effect.process_async(output)
        
        return output
    
    def save_preset(self) -> Dict[str, Any]:
        """Guardar preset de cadena"""
        return {
            "sample_rate": self.sample_rate,
            "effects": [
                {
                    "type": e.config.type.value,
                    "enabled": e.config.enabled,
                    "params": e.config.params,
                }
                for e in self.effects
            ],
        }
    
    def load_preset(self, preset: Dict[str, Any]) -> None:
        """Cargar preset"""
        self.effects = []
        for effect_data in preset.get("effects", []):
            config = EffectConfig(
                type=EffectType(effect_data["type"]),
                enabled=effect_data.get("enabled", True),
                params=effect_data.get("params", {}),
            )
            self.add_effect_config(config)


# Presets predefinidos
PRESET_MASTERING = {
    "effects": [
        {"type": "highpass", "enabled": True, "params": {"cutoff_hz": 20}},
        {"type": "eq", "enabled": True, "params": {"low_gain_db": 2, "mid_gain_db": 0, "high_gain_db": 1}},
        {"type": "compressor", "enabled": True, "params": {"threshold_db": -20, "ratio": 2.0}},
        {"type": "limiter", "enabled": True, "params": {"threshold_db": -3}},
    ]
}

PRESET_CLEAN_VOICE = {
    "effects": [
        {"type": "highpass", "enabled": True, "params": {"cutoff_hz": 80}},
        {"type": "eq", "enabled": True, "params": {"low_gain_db": -2, "mid_gain_db": 3, "high_gain_db": 2}},
        {"type": "compressor", "enabled": True, "params": {"threshold_db": -15, "ratio": 3.0}},
    ]
}

PRESET_BRIGHT = {
    "effects": [
        {"type": "eq", "enabled": True, "params": {"low_gain_db": 1, "mid_gain_db": 0, "high_gain_db": 4}},
        {"type": "distortion", "enabled": True, "params": {"drive": 1.2, "mix": 0.1}},
    ]
}
