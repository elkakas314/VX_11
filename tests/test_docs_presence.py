from pathlib import Path

import pytest


@pytest.mark.unit
def test_module_readme_exists():
    """Each module root must have a README.md (or doc entrypoint)."""
    repo_root = Path(__file__).resolve().parent.parent
    modules = [
        "madre",
        "tentaculo_link",
        "switch",
        "spawner",
        "operator",
        "manifestator",
        "hormiguero",
        "mcp",
        "shubniggurath",
    ]
    missing = [m for m in modules if not (repo_root / m / "README.md").exists()]
    assert not missing, f"Missing README.md in module roots: {missing}"
