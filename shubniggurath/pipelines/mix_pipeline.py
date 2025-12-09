"""
Mix pipeline wiring stem processing + compression suggestions.
"""

from __future__ import annotations

from typing import Any, Dict, List

from shubniggurath.ops.comp_ops import CompressionOps
from shubniggurath.ops.mix_ops import MixOps
from shubniggurath.ops.stem_ops import StemOps


class MixPipeline:
    name = "mix_pipeline_v1"

    def __init__(self, mix_ops: MixOps, comp_ops: CompressionOps, stem_ops: StemOps):
        self.mix_ops = mix_ops
        self.comp_ops = comp_ops
        self.stem_ops = stem_ops

    async def run(self, stems: Dict[str, List[float]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        validation = self.stem_ops.validate(stems)
        roles = self.stem_ops.detect_roles(stems)
        mixed, gains = self.mix_ops.mix_stems(stems)
        makeup = self.comp_ops.suggest_gain(mixed)

        return {
            "mixed": mixed,
            "roles": roles,
            "validation": validation,
            "gains": gains,
            "makeup_gain_db": makeup,
            "metadata": metadata,
        }
