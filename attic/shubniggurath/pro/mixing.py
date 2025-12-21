"""
Funciones de mezcla automatizada básica.
"""
import math
from typing import Dict, List, Sequence, Tuple


def gain_stage(samples: Sequence[float], target_lufs: float = -16.0) -> List[float]:
    if not samples:
        return list(samples)
    current = 20 * math.log10(math.sqrt(sum(s * s for s in samples) / len(samples)) + 1e-9)
    gain_db = target_lufs - current
    factor = 10 ** (gain_db / 20)
    return [max(-1.0, min(1.0, s * factor)) for s in samples]


def pan(samples: Sequence[float], pan_value: float = 0.0) -> Tuple[List[float], List[float]]:
    """
    pan_value -1.0 (L) to 1.0 (R); return stereo lists (L, R)
    """
    left = [s * (1 - max(0, pan_value)) for s in samples]
    right = [s * (1 + min(0, pan_value)) for s in samples]
    return left, right


def auto_mix(samples: Sequence[float], target_lufs: float = -16.0, pan_value: float = 0.0) -> Dict[str, Sequence[float]]:
    staged = gain_stage(samples, target_lufs=target_lufs)
    stereo = pan(staged, pan_value=pan_value)
    return {"mono": staged, "stereo": stereo}
