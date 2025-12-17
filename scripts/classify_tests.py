#!/usr/bin/env python3
"""Clasifica tests usando imports_ast_report.json.
Salida: docs/audit/cleanup_<TS>/tests_classification.tsv (TS se pasa como arg).
"""
import sys
import json
from pathlib import Path

if len(sys.argv) < 3:
    print("Usage: classify_tests.py <TS> <imports_ast_report.json>")
    sys.exit(2)

TS = sys.argv[1]
AST_JSON = Path(sys.argv[2])
OUT_DIR = Path("docs") / "audit" / f"cleanup_{TS}"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "tests_classification.tsv"

reqs = {
    "pytest",
    "fastapi",
    "httpx",
    "pydantic",
    "uvicorn",
    "requests",
    "sqlalchemy",
    "numpy",
    "pytest-asyncio",
    "pytest",
    "anyio",
}
canon_top = {"config", "switch", "tentaculo_link"}

report = json.loads(AST_JSON.read_text())
files = report.get("files", {})

with OUT.open("w", encoding="utf-8") as fh:
    fh.write("path\tstatus\timports_externos\n")
    for path, data in files.items():
        if not path.startswith("tests/"):
            continue
        imports = data.get("imports", [])
        top_imports = set(i.get("top") for i in imports if i.get("top"))
        externals = []
        legacy_flag = False
        for t in top_imports:
            if t in canon_top or t in (
                "os",
                "sys",
                "json",
                "re",
                "typing",
                "pathlib",
                "datetime",
            ):
                continue
            if t in reqs:
                externals.append(t)
                continue
            # if imports from known non-canonical modules -> legacy
            if t in (
                "madre",
                "hormiguero",
                "mcp",
                "spawner",
                "operator_backend",
                "manifestator",
                "shubniggurath",
                "operator",
            ):
                legacy_flag = True
                externals.append(t)
            else:
                # unknown -> mark external
                externals.append(t)
        status = (
            "legacy"
            if legacy_flag
            or any(
                e
                for e in externals
                if e not in reqs
                and e not in canon_top
                and e
                not in ("os", "sys", "json", "re", "typing", "pathlib", "datetime")
            )
            else "canonic"
        )
        fh.write(f"{path}\t{status}\t{','.join(sorted(set(externals)))}\n")

print("WROTE", OUT)
