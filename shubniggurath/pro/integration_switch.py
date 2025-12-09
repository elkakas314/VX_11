"""
Adaptador mínimo para integrar Shub Pro con Switch/Madre/Operator.
"""
from typing import Dict, Any
from .pipeline import run_pipeline, ingest_track


class ShubProJobAdapter:
    def __init__(self):
        pass

    def handle_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        job: {"project": str, "track": str, "path": str, "action": "pipeline|ingest"}
        """
        action = job.get("action", "pipeline")
        if action == "ingest":
            return ingest_track(job.get("project", "demo"), job.get("track", "track"), job["path"])
        return run_pipeline(job.get("project", "demo"), job.get("track", "track"), job["path"], output_dir=job.get("output_dir"))
