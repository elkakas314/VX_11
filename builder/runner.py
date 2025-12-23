"""Builder sandbox runner: transforms input.json into canonical outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def run_builder_job(input_path: Path, output_dir: Path) -> Dict[str, Any]:
    input_data = json.loads(input_path.read_text())
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.utcnow().isoformat() + "Z"
    intent = {
        "domain": input_data.get("domain", "unknown"),
        "intent_type": input_data.get("intent_type", "unknown"),
        "summary": input_data.get("summary", "builder_job"),
        "generated_at": now,
    }
    module_canonical = {
        "module": input_data.get("module", "unknown"),
        "source_job": input_data.get("job_id"),
        "generated_at": now,
    }
    external_canon = {
        "schema": "external_v1",
        "generated_at": now,
        "input": input_data,
    }
    external_spec = {
        "spec_version": "v1",
        "generated_at": now,
        "notes": "builder sandbox output",
    }

    _write_json(output_dir / "intent.json", intent)
    _write_json(output_dir / "module_canonical.json", module_canonical)
    _write_json(output_dir / "CANONICAL.json", external_canon)
    _write_json(output_dir / "SPEC.json", external_spec)
    (output_dir / "README.md").write_text(
        "Builder sandbox output (planning-only).",
    )

    return {
        "outputs": [
            "intent.json",
            "module_canonical.json",
            "CANONICAL.json",
            "SPEC.json",
            "README.md",
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="VX11 builder sandbox runner")
    parser.add_argument("input_path", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    run_builder_job(args.input_path, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
