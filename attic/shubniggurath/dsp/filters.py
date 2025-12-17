"""
Simple DSP filters utilities (placeholder math only).
"""

from __future__ import annotations

from typing import Dict, List


class FilterBank:
    """Very small set of helpers to avoid heavy DSP libs."""

    def normalize(self, samples: List[float], target_peak: float = 0.9) -> List[float]:
        if not samples:
            return samples
        current_peak = max(abs(s) for s in samples)
        if current_peak == 0:
            return samples
        gain = target_peak / current_peak
        return [max(min(s * gain, 1.0), -1.0) for s in samples]

    def highpass(self, samples: List[float], threshold: float = 0.01) -> List[float]:
        # Placeholder: zero-out very low-amplitude drift (dc-ish)
        return [s if abs(s) > threshold else 0.0 for s in samples]

    def estimate_balance(self, samples: List[float]) -> Dict[str, float]:
        # Coarse spectral split based on sample index bands (no FFT required)
        total = len(samples) or 1
        thirds = total // 3 or 1
        low = sum(abs(s) for s in samples[:thirds]) / thirds
        mid = sum(abs(s) for s in samples[thirds: 2 * thirds]) / thirds
        high = sum(abs(s) for s in samples[2 * thirds:]) / thirds
        total_energy = low + mid + high or 1.0
        return {
            "low": low / total_energy,
            "mid": mid / total_energy,
            "high": high / total_energy,
        }
