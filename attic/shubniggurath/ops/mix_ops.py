"""
Mix operations for combining stems.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


class MixOps:
    def mix_stems(self, stems: Dict[str, List[float]]) -> Tuple[List[float], Dict[str, float]]:
        """Average all stems sample-by-sample with basic gain staging."""
        if not stems:
            return [], {}

        max_length = max(len(data) for data in stems.values())
        if max_length == 0:
            return [], {}

        mixed = []
        for i in range(max_length):
            sample_sum = 0.0
            count = 0
            for data in stems.values():
                if i < len(data):
                    sample_sum += data[i]
                    count += 1
            mixed.append(sample_sum / max(count, 1))

        # Gain per stem to avoid clipping
        gains = {name: 0.9 for name in stems.keys()}
        return mixed, gains
