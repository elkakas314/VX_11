"""
REAPER pipeline stub to generate simple session metadata.
"""

from __future__ import annotations

from typing import Any, Dict


class ReaperPipeline:
    name = "reaper_pipeline_v1"

    async def build_session(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Return a minimal REAPER-friendly descriptor without touching disk."""
        return {
            "project": "shub_session",
            "tracks": [
                {
                    "name": "Master",
                    "notes": analysis.get("headline", "shub session"),
                    "fx_chain": ["shub_cleanup", "shub_comp"],
                }
            ],
            "metadata": {"duration": analysis.get("duration_seconds", 0.0)},
        }
