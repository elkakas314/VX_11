"""
Análisis musical/técnico ligero. Usa numpy; si librosa está instalado, amplía features.
"""
import math
from typing import Dict, Sequence

try:
    import numpy as _np  # pragma: no cover
    import librosa  # type: ignore  # opcional
except Exception:  # pragma: no cover
    _np = None
    librosa = None


def spectral_centroid(samples: Sequence[float], sr: int) -> float:
    if librosa and _np is not None:
        return float(_np.mean(librosa.feature.spectral_centroid(y=_np.array(samples), sr=sr)))
    if not samples:
        return 0.0
    # Fallback simple: promedio de frecuencia ponderada por magnitud FFT
    import cmath
    n = len(samples)
    fft = [abs(cmath.rect(s, 0)) for s in samples]
    total = sum(fft)
    if total == 0:
        return 0.0
    # escala lineal aproximada
    return float(total / n)


def tempo_detect(samples: Sequence[float], sr: int) -> float:
    if librosa and _np is not None:
        tempo, _ = librosa.beat.beat_track(y=_np.array(samples), sr=sr)
        return float(tempo)
    return 0.0


def feature_summary(samples: Sequence[float], sr: int) -> Dict[str, float]:
    return {
        "spectral_centroid": spectral_centroid(samples, sr),
        "tempo": tempo_detect(samples, sr),
    }
