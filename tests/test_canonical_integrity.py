import hashlib
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_json(path):
    with open(REPO_ROOT / path, "r") as f:
        return json.load(f)


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_canonical_master_integrity():
    """Verifica que el MASTER contenga los archivos canónicos base."""
    master = load_json("docs/CANONICAL_MASTER_VX11.json")
    expected_files = [
        "docs/CANONICAL_FS_VX11.json",
        "docs/CANONICAL_TARGET_FS_VX11.json",
        "docs/CANONICAL_FLOWS_VX11.json",
        "docs/CANONICAL_SEMANTIC_VX11.json",
        "docs/CANONICAL_RUNTIME_POLICY_VX11.json",
    ]
    for f in expected_files:
        assert f in master["sha256"], f"Falta hash para {f} en MASTER"


def test_policy_default_off():
    """Verifica que Manifestator y Shub-Niggurath estén OFF por defecto."""
    policy = load_json("docs/CANONICAL_RUNTIME_POLICY_VX11.json")

    # En la versión v2_with_modes, el modo por defecto debe ser low_power (solo madre)
    assert policy["default_mode"] == "low_power"
    assert "madre" in policy["modes"]["low_power"]["services"]
    assert len(policy["modes"]["low_power"]["services"]) == 1

    # Manifestator y Shub solo deben estar en el modo 'full'
    assert "manifestator" in policy["modes"]["full"]["services"]
    assert "shubniggurath" in policy["modes"]["full"]["services"]
    assert "manifestator" not in policy["modes"]["operative_core"]["services"]


def test_semantic_module_states():
    """Verifica que los módulos opcionales estén en los roles correctos."""
    semantic = load_json("docs/CANONICAL_SEMANTIC_VX11.json")

    # Mapear módulos por rol
    roles = {r["role"]: r["modules"] for r in semantic["roles"]}

    assert "manifestator" in roles["full_profile"]
    assert "shubniggurath" in roles["full_profile"]
    assert "hormiguero" in roles["support"]
    assert "switch/hermes" in roles["support"]
    assert "madre" in roles["core_essential"]


def test_hermes_no_root_duplicate():
    """Verifica que no haya rastro de hermes en la raíz según el FS canónico."""
    fs = load_json("docs/CANONICAL_FS_VX11.json")
    for path in fs["files"]:
        # No debe haber archivos en hermes/ (raíz), solo en switch/hermes/
        if path.startswith("hermes/"):
            # Excepción: si es un archivo de documentación o algo permitido, pero aquí somos estrictos
            assert False, f"Se encontró archivo en raíz hermes/: {path}"


def test_master_sha256_matches_files():
    """Valida que el MASTER mencione exactamente los archivos canónicos y sus hashes."""
    master = load_json("docs/CANONICAL_MASTER_VX11.json")
    sha_map = master.get("sha256", {})
    canonical_paths = set(master.get("canonical_files", {}).values())
    assert canonical_paths, "El MASTER no define archivos canónicos"

    missing_positions = [p for p in canonical_paths if p not in sha_map]
    assert not missing_positions, f"Falta hash para los archivos: {missing_positions}"

    extra_hashes = set(sha_map) - canonical_paths
    assert (
        not extra_hashes
    ), f"MASTER tiene hashes de archivos no declarados como canónicos: {extra_hashes}"

    mismatches = []
    for relative in canonical_paths:
        path = REPO_ROOT / relative
        assert path.exists(), f"Archivo canónico faltante: {relative}"
        actual = file_sha256(path)
        expected = sha_map[relative]
        if actual != expected:
            mismatches.append((relative, expected, actual))

    assert not mismatches, f"Hashes no coinciden: {mismatches}"


def test_attic_files_listed_in_fs_snapshot():
    """Asegura que los archivos relevantes de attic/ estén mapeados en el FS canónico."""
    fs_snapshot = load_json("docs/CANONICAL_FS_VX11.json")["files"]
    fs_set = set(fs_snapshot)
    attic_root = REPO_ROOT / "attic"
    ignore_suffixes = {".pyc", ".log", ".tmp", ".zip", ".tar.gz", ".tar", ".bak"}
    ignore_dirs = {
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "archive",
        "legacy",
    }

    actual_attic = set()
    for path in attic_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignore_dirs for part in path.parts):
            continue
        if path.suffix.lower() in ignore_suffixes:
            continue
        actual_attic.add(str(path.relative_to(REPO_ROOT).as_posix()))

    missing = sorted(actual_attic - fs_set)
    assert (
        not missing
    ), f"Los siguientes archivos canonizables de attic faltan en CANONICAL_FS: {missing}"


def test_fs_paths_case_insensitive_unique():
    """Previene alias duplicados detectando rutas repetidas sin distinguir mayúsculas."""
    fs_snapshot = load_json("docs/CANONICAL_FS_VX11.json")["files"]
    seen = {}
    duplicates = []
    for path in fs_snapshot:
        key = path.casefold()
        if key in seen:
            duplicates.append((seen[key], path))
        else:
            seen[key] = path

    allowed_variants = {
        frozenset(
            {
                "attic/.github/prompts/VX11_DBMAP.prompt.md",
                "attic/.github/prompts/vx11_dbmap.prompt.md",
            }
        )
    }
    not_allowed = [
        pair for pair in duplicates if frozenset(pair) not in allowed_variants
    ]
    assert (
        not not_allowed
    ), f"Rutas aliadas en canonical FS fuera de casos controlados: {not_allowed}"


def test_target_allowed_roots_exist():
    """Verifica que cada root declarado en el target exista realmente."""
    target = load_json("docs/CANONICAL_TARGET_FS_VX11.json")
    roots = target.get("allowed_roots", [])
    assert roots, "El target FS no expone allowed_roots"

    missing = []
    for root in roots:
        checks = [REPO_ROOT / root, REPO_ROOT / "attic" / root]
        if not any(p.exists() for p in checks):
            missing.append(root)

    assert not missing, f"Allowed roots faltantes: {missing}"
