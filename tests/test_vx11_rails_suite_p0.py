"""
P0 suite aggregator for VX11 rails/reina/builder flow.
"""

from pathlib import Path


def test_p0_suite_manifest():
    required = [
        "tests/test_manifestator_rails_p0.py",
        "tests/test_madre_lane_routing_p0.py",
        "tests/test_hormiguero_reina_intents_p0.py",
        "tests/test_builder_sandbox_p0.py",
    ]
    for path in required:
        assert Path(path).exists()
