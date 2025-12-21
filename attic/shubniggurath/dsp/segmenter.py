"""
Audio segmenter stub to split frames into coarse chunks.
"""

from __future__ import annotations

from typing import Dict, List


class AudioSegmenter:
    def split(self, samples: List[float], sample_rate: int, window_seconds: int = 5) -> List[Dict[str, float]]:
        if not samples or not sample_rate:
            return []

        window_size = max(1, sample_rate * window_seconds)
        segments = []
        for idx in range(0, len(samples), window_size):
            chunk = samples[idx: idx + window_size]
            peak = max(chunk) if chunk else 0.0
            rms = (sum(s * s for s in chunk) / len(chunk)) ** 0.5 if chunk else 0.0
            segments.append(
                {
                    "index": len(segments),
                    "start_sec": idx / sample_rate,
                    "end_sec": (idx + len(chunk)) / sample_rate,
                    "peak": peak,
                    "rms": rms,
                }
            )
        return segments
