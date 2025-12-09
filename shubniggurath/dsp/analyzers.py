"""
Lightweight audio analyzer that avoids heavy DSP dependencies.
The input is expected to be a list of floats (normalized samples).
"""

from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List, Tuple

from shubniggurath.dsp.filters import FilterBank
from shubniggurath.dsp.segmenter import AudioSegmenter


class AudioAnalyzer:
    def __init__(self, filters: FilterBank, segmenter: AudioSegmenter):
        self.filters = filters
        self.segmenter = segmenter

    async def analyze(self, audio: List[float], sample_rate: int = 48000, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        duration = len(audio) / float(sample_rate) if sample_rate else 0.0
        peak = max(audio) if audio else 0.0
        rms = self._rms(audio)
        segments = self.segmenter.split(audio, sample_rate)

        spectral_hint = self.filters.estimate_balance(audio)
        mood = self._estimate_mood(rms, spectral_hint)

        return {
            "duration_seconds": duration,
            "sample_rate": sample_rate,
            "peak": peak,
            "rms": rms,
            "segments": segments,
            "spectral_balance": spectral_hint,
            "mood": mood,
            "metadata": metadata or {},
            "headline": f"{mood} tone | peak {peak:.3f} | rms {rms:.3f}",
        }

    def _rms(self, audio: List[float]) -> float:
        if not audio:
            return 0.0
        return (sum(sample * sample for sample in audio) / len(audio)) ** 0.5

    def _estimate_mood(self, rms: float, spectral: Dict[str, float]) -> str:
        highs = spectral.get("high", 0.0)
        lows = spectral.get("low", 0.0)
        if highs > lows and rms > 0.3:
            return "bright"
        if lows > highs and rms < 0.2:
            return "dark"
        return "balanced"
