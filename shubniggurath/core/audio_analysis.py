"""
AudioAnalysis: Dataclass y utilidades para análisis de audio real.
Extrae 40+ métricas usando librosa, scipy, numpy.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json


@dataclass
class IssueReport:
    """Reporte de un issue detectado en audio."""
    type: str  # clipping, dc_offset, high_noise_floor, phase_issues, sibilance, resonance
    severity: float  # 0.0-1.0
    description: str
    details: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Resonance:
    """Resonancia detectada en el espectro."""
    frequency: float  # Hz
    magnitude: float  # dB
    prominence: float  # dB


@dataclass
class AudioAnalysis:
    """
    Análisis completo de audio con 40+ métricas.
    Resultado de AnalyzerEngine.analyze_audio().
    """
    # Metadata
    duration: float  # segundos
    sample_rate: int  # Hz
    channels: int  # 1=mono, 2=stereo
    rms_dbfs: float  # RMS level en dBFS
    
    # ========== NIVEL ==========
    peak_dbfs: float  # Peak dBFS
    lufs_integrated: float  # LUFS integrado (loudness)
    lufs_range: float  # Loudness Range (LU)
    true_peak_dbfs: float  # True Peak (interpolado) dBFS
    
    # ========== ESPECTRAL ==========
    spectral_centroid: float  # Hz (promedio ponderado)
    spectral_rolloff: float  # Hz (85% energía)
    spectral_flux: float  # cambio espectral temporal
    zero_crossing_rate: float  # 0-1
    spectral_flatness: float  # 0-1 (noise-like vs tonal)
    
    # Descriptores
    mfcc: List[float]  # 13 coeficientes MFCC
    chroma: List[float]  # 12 notas (C-B)
    spectral_contrast: List[float]  # 7 bandas de contraste
    
    # ========== DINÁMICA ==========
    dynamic_range: float  # dB
    crest_factor: float  # dB (peak/rms)
    transients_count: int  # cantidad de transitorios detectados
    transients: List[float]  # tiempos (segundos) de transitorios
    
    # ========== ISSUES (PROBLEMAS) ==========
    clipping_samples: int
    dc_offset: float  # -1.0 a 1.0
    noise_floor_dbfs: float
    phase_correlation: float  # -1 a 1 (para stereo)
    sibilance_detected: bool
    sibilance_freq: float  # Hz del pico de sibilancia
    resonances: List[Resonance]  # resonancias detectadas
    issues: List[IssueReport]  # lista de problemas encontrados
    
    # ========== MUSICAL ==========
    bpm: Optional[float]  # BPM detectado
    key_detected: Optional[str]  # C, C#, D, etc
    key_confidence: Optional[float]  # 0-1
    harmonic_complexity: float  # 0-1 (ratio energía armónica)
    percussiveness: float  # 0-1 (ratio energía percusiva)
    
    # ========== CLASIFICACIÓN ==========
    instrument_prediction: Dict[str, float]  # {vocals: 0.3, guitar: 0.2, ...}
    genre_prediction: Dict[str, float]  # {rock: 0.3, pop: 0.25, ...}
    mood_prediction: Dict[str, float]  # {energetic: 0.3, calm: 0.2, ...}
    
    # ========== RECOMENDACIONES ==========
    recommendations: List[Dict[str, Any]]  # acciones sugeridas
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario (para JSON)."""
        data = asdict(self)
        # Convertir objetos complejos
        data['issues'] = [issue.to_dict() for issue in self.issues]
        data['resonances'] = [
            {
                'frequency': r.frequency,
                'magnitude': r.magnitude,
                'prominence': r.prominence
            }
            for r in self.resonances
        ]
        return data

    def to_json(self) -> str:
        """Convertir a JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AudioAnalysis':
        """Crear desde diccionario (JSON deserialized)."""
        # Convertir issues back to IssueReport
        issues_data = data.pop('issues', [])
        issues = [IssueReport(**issue) for issue in issues_data]
        
        # Convertir resonances back to Resonance
        resonances_data = data.pop('resonances', [])
        resonances = [Resonance(**r) for r in resonances_data]
        
        return AudioAnalysis(
            issues=issues,
            resonances=resonances,
            **data
        )
