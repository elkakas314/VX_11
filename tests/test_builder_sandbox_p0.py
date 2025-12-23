"""
P0 tests for builder sandbox compose + runner.
"""

import json
import sys
from pathlib import Path


def test_builder_compose_isolation():
    compose_path = Path("docker-compose.builder.yml")
    content = compose_path.read_text()

    assert "network_mode: \"none\"" in content
    assert "read_only: true" in content
    assert "cap_drop:" in content
    assert "- ALL" in content


def test_builder_runner_outputs(tmp_path):
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from builder.runner import run_builder_job

    input_payload = {
        "domain": "execution",
        "intent_type": "build",
        "summary": "test builder",
        "module": "vx11",
    }
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(input_payload))
    output_dir = tmp_path / "output"

    result = run_builder_job(input_path, output_dir)
    for name in result["outputs"]:
        assert (output_dir / name).exists()
