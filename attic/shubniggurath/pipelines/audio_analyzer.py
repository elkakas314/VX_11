"""
Audio analyzer pipeline combining DSP features and diagnostics.
"""

from __future__ import annotations

from typing import Any, Dict, List

from shubniggurath.dsp.analyzers import AudioAnalyzer
from shubniggurath.ops.diagnostic_ops import DiagnosticOps


class AudioAnalyzerPipeline:
    name = "audio_analyzer_v1"

    def __init__(self, analyzer: AudioAnalyzer, diagnostics: DiagnosticOps):
        self.analyzer = analyzer
        self.diagnostics = diagnostics

    async def run(self, audio: List[float], sample_rate: int, metadata: Dict[str, Any]) -> Dict[str, Any]:
        base = await self.analyzer.analyze(audio, sample_rate, metadata)
        issues = self.diagnostics.detect_issues(audio, base.get("rms", 0.0), base.get("peak", 0.0))
        summary = self.diagnostics.summarize(metadata, issues)
        return {
            "summary": {"headline": summary, "duration": base.get("duration_seconds", 0.0)},
            "analysis": base,
            "issues": issues,
        }
