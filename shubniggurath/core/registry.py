"""
Factory helpers for Shub-Niggurath components.
"""

from __future__ import annotations

from functools import lru_cache

from shubniggurath.core.engine import ShubEngine
from shubniggurath.dsp.analyzers import AudioAnalyzer
from shubniggurath.dsp.filters import FilterBank
from shubniggurath.dsp.segmenter import AudioSegmenter
from shubniggurath.ops.comp_ops import CompressionOps
from shubniggurath.ops.diagnostic_ops import DiagnosticOps
from shubniggurath.ops.mix_ops import MixOps
from shubniggurath.ops.stem_ops import StemOps
from shubniggurath.pipelines.audio_analyzer import AudioAnalyzerPipeline
from shubniggurath.pipelines.mix_pipeline import MixPipeline
from shubniggurath.pipelines.reaper_pipeline import ReaperPipeline


@lru_cache(maxsize=1)
def get_engine() -> ShubEngine:
    """Singleton ShubEngine instance."""
    analyzer = AudioAnalyzer(FilterBank(), AudioSegmenter())
    diagnostics = DiagnosticOps()
    mix_ops = MixOps()
    comp_ops = CompressionOps()
    stems = StemOps()

    analyzer_pipeline = AudioAnalyzerPipeline(analyzer, diagnostics)
    mix_pipeline = MixPipeline(mix_ops, comp_ops, stems)
    reaper_pipeline = ReaperPipeline()

    return ShubEngine(analyzer_pipeline, mix_pipeline, reaper_pipeline)
