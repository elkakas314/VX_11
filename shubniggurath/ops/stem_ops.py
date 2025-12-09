"""
Stem utilities for Shub-Niggurath.
"""

from __future__ import annotations

from typing import Dict, List


class StemOps:
    def validate(self, stems: Dict[str, List[float]]) -> Dict[str, int]:
        return {name: len(data) for name, data in stems.items()}

    def detect_roles(self, stems: Dict[str, List[float]]) -> Dict[str, str]:
        roles = {}
        for name in stems.keys():
            lower = name.lower()
            if "vox" in lower or "voc" in lower:
                roles[name] = "vocals"
            elif "kick" in lower or "drum" in lower:
                roles[name] = "drums"
            elif "bass" in lower:
                roles[name] = "bass"
            else:
                roles[name] = "instrument"
        return roles
