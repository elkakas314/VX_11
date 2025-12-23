import json
from pathlib import Path


def test_switch_hermes_canon_index_entry():
    index_path = Path("docs/canon/INDEX.json")
    assert index_path.is_file()
    data = json.loads(index_path.read_text(encoding="utf-8"))
    modules = data.get("modules", [])
    canon_path = "docs/canon/VX11_SWITCH_HERMES_CANONICAL_v1.0.0.json"
    ids = {m.get("id") for m in modules}
    assert "switch" in ids
    assert "hermes" in ids
    assert any(m.get("canonical") == canon_path for m in modules)
    assert Path(canon_path).is_file()
