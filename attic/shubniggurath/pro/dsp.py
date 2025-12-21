"""
Funciones DSP básicas para Shub Pro.
Se basan en numpy; sin dependencias pesadas en tiempo de prueba.
"""
import math
from typing import Dict, Sequence


def rms(samples: Sequence[float]) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def peak(samples: Sequence[float]) -> float:
    return max((abs(s) for s in samples), default=0.0)


def lufs_approx(samples: Sequence[float]) -> float:
    val = rms(samples)
    if val <= 0:
        return -999.0
    return 20 * math.log10(val + 1e-9)


def dynamic_range(samples: Sequence[float]) -> float:
    p = peak(samples)
    r = rms(samples)
    if r <= 0:
        return 0.0
    return 20 * math.log10((p + 1e-9) / (r + 1e-9))


def detect_clipping(samples: Sequence[float], threshold: float = 0.99) -> int:
    return sum(1 for s in samples if abs(s) >= threshold)


def noise_floor(samples: Sequence[float]) -> float:
    if not samples:
        return -120.0
    sorted_abs = sorted(abs(s) for s in samples)
    idx = max(0, int(len(sorted_abs) * 0.1) - 1)
    silent = sorted_abs[idx]
    return 20 * math.log10(silent + 1e-9)


def analyze_basic(samples: Sequence[float]) -> Dict[str, float]:
    return {
        "rms": rms(samples),
        "peak": peak(samples),
        "lufs": lufs_approx(samples),
        "dynamic_range": dynamic_range(samples),
        "clipping_events": detect_clipping(samples),
        "noise_floor": noise_floor(samples),
    }
