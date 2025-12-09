"""
Diagnostic helpers to keep the DSP pipeline actionable without heavy dependencies.
"""

from __future__ import annotations

from typing import Dict, List


class DiagnosticOps:
    def detect_issues(self, audio: List[float], rms: float, peak: float) -> List[Dict[str, str]]:
        issues = []
        if peak > 0.95:
            issues.append({"type": "clipping_risk", "severity": "high", "description": "Peak too close to full scale"})
        if rms < 0.05:
            issues.append({"type": "low_level", "severity": "medium", "description": "Signal is very quiet"})
        return issues

    def summarize(self, metadata: Dict[str, str], issues: List[Dict[str, str]]) -> str:
        tag = metadata.get("style") or metadata.get("genre") or "generic"
        if issues:
            return f"{tag}: {len(issues)} issues detected"
        return f"{tag}: clean"
