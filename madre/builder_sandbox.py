"""Builder sandbox runner for Madre (Docker isolated)."""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


def start_builder_job(
    input_payload: Dict[str, Any],
    ttl_seconds: int = 300,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    job_id = job_id or str(uuid.uuid4())
    job_root = Path("data/runtime/builder_jobs") / job_id
    output_dir = job_root / "output"
    job_root.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = job_root / "input.json"
    input_payload = dict(input_payload)
    input_payload.setdefault("job_id", job_id)
    input_path.write_text(json.dumps(input_payload, indent=2))

    env = os.environ.copy()
    env["JOB_ID"] = job_id
    cmd = [
        "docker",
        "compose",
        "-f",
        "docker-compose.builder.yml",
        "up",
        "--abort-on-container-exit",
        "--exit-code-from",
        "builder",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=ttl_seconds,
        env=env,
        check=False,
    )

    outputs: Dict[str, Any] = {}
    for name in [
        "intent.json",
        "module_canonical.json",
        "CANONICAL.json",
        "SPEC.json",
        "README.md",
    ]:
        path = output_dir / name
        if path.exists():
            outputs[name] = path.read_text()

    return {
        "job_id": job_id,
        "status": "ok" if result.returncode == 0 else "error",
        "returncode": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
        "outputs": outputs,
    }
