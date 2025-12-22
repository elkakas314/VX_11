"""Valida el contrato del verificador canónico (hash + existencia de archivos)."""

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_master() -> dict:
    master_path = REPO_ROOT / "docs/CANONICAL_MASTER_VX11.json"
    with open(master_path, "r") as f:
        return json.load(f)


def main() -> int:
    master = load_master()
    canonical_files = master.get("canonical_files", {})
    sha_map = master.get("sha256", {})

    if not canonical_files:
        print("[FAIL] El MASTER no define archivos canónicos.")
        return 1

    canonical_paths = set(canonical_files.values())
    missing_hashes = [path for path in canonical_paths if path not in sha_map]
    extra_hashes = set(sha_map) - canonical_paths

    errors = []
    if missing_hashes:
        errors.append(f"Faltan hashes para {missing_hashes}")

    if extra_hashes:
        errors.append(f"Hashes extra no declarados: {sorted(extra_hashes)}")

    for relative in canonical_paths:
        absolute = REPO_ROOT / relative
        if not absolute.exists():
            errors.append(f"Archivo canónico faltante: {relative}")
            continue

        expected = sha_map.get(relative)
        if expected is None:
            errors.append(f"Archivo {relative} no tiene hash declarado.")
            continue

        actual = compute_sha256(absolute)
        if actual != expected:
            errors.append(
                f"Hash mismatch {relative}: esperado {expected}, actual {actual}"
            )

    if errors:
        print("VERIFIER CONTRACT VALIDATION ERRORS:")
        for item in errors:
            print(" -", item)
        return 1

    print("VERIFIER CONTRACT VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
