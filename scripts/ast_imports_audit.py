#!/usr/bin/env python3
"""AST imports auditor
Genera docs/audit/imports_ast_report.json con clasificación básica de imports.
Clasificación heurística: relative/import-from-level >0 -> internal; top-level name in repo dirs -> internal; top-level name in requirements.txt -> third-party; in stdlib -> stdlib; else unknown.
"""
import ast
import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs" / "audit" / "imports_ast_report.json"
REQUIREMENTS = ROOT / "requirements.txt"
EXCLUDE_DIRS = {".venv", "build", "dist", "__pycache__", ".git", "data", "archive"}


def load_requirements(req_path):
    names = set()
    if not req_path.exists():
        return names
    for line in req_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # extract package name before extras or version spec
        for sep in ("[", "==", ">=", "<=", "~=", "!=", ">", "<", " ", ";"):
            if sep in line:
                line = line.split(sep, 1)[0]
                break
        names.add(line.lower())
    return names


def discover_local_packages(root):
    pkgs = set()
    for p in root.iterdir():
        if p.name in EXCLUDE_DIRS or p.name.startswith("."):
            continue
        if p.is_dir():
            # treat as package if contains python files or __init__.py
            if any(p.glob("*.py")) or (p / "__init__.py").exists():
                pkgs.add(p.name)
    return pkgs


def top_name(modname):
    if not modname:
        return None
    return modname.split(".")[0]


def classify_name(name, reqs, local_pkgs, stdlib_names):
    if not name:
        return "unknown"
    n = name.lower()
    if n in local_pkgs:
        return "internal"
    if n in reqs:
        return "third-party"
    if n in stdlib_names:
        return "stdlib"
    return "unknown"


def gather_imports(pyfile, reqs, local_pkgs, stdlib_names):
    text = pyfile.read_text(errors="ignore")
    try:
        tree = ast.parse(text)
    except Exception as e:
        return {"error": str(e)}
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = top_name(alias.name)
                imports.append(
                    {
                        "type": "import",
                        "full": alias.name,
                        "top": top,
                        "lineno": node.lineno,
                        "class": classify_name(top, reqs, local_pkgs, stdlib_names),
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                # relative import like from . import x
                mod = None
            else:
                mod = node.module
            top = top_name(mod) if mod else None
            cls = (
                "internal"
                if (node.level and node.level > 0)
                else classify_name(top, reqs, local_pkgs, stdlib_names)
            )
            imports.append(
                {
                    "type": "from",
                    "module": mod,
                    "top": top,
                    "level": node.level,
                    "lineno": node.lineno,
                    "class": cls,
                }
            )
    return imports


def main():
    reqs = load_requirements(REQUIREMENTS)
    local_pkgs = discover_local_packages(ROOT)
    # stdlib names
    stdlib = set()
    if hasattr(sys, "stdlib_module_names"):
        stdlib = set(map(str.lower, sys.stdlib_module_names))
    else:
        stdlib = set(map(str.lower, sys.builtin_module_names))

    report = {
        "meta": {
            "root": str(ROOT),
            "local_packages": sorted(list(local_pkgs)),
            "requirements_count": len(reqs),
        },
        "files": {},
    }

    for dirpath, dirnames, filenames in os.walk(ROOT):
        parts = Path(dirpath).parts
        if any(p in EXCLUDE_DIRS for p in parts):
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            fpath = Path(dirpath) / fn
            rel = fpath.relative_to(ROOT).as_posix()
            imports = gather_imports(fpath, reqs, local_pkgs, stdlib)
            report["files"][rel] = {"imports": imports}

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print("Wrote", OUT_JSON)


if __name__ == "__main__":
    main()
