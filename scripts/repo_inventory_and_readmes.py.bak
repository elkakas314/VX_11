#!/usr/bin/env python3
"""
Recorre el repo y clasifica archivos en ACTIVE / CANONICAL_ARCHIVE / POTENTIAL_ARCHIVE / TRASH_CANDIDATE.
Genera CSV en `docs/archive/repo_inventory.csv` y crea READMEs en `docs/archive/*` y `archive/*`.
También genera `docs/archive/REPO_CLEANUP_SUMMARY.md`.
No borra ni mueve nada.
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py

import os
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "archive"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUT_DIR / "repo_inventory.csv"
SUMMARY_PATH = OUT_DIR / "REPO_CLEANUP_SUMMARY.md"

# Folders to mark as canonical archive
CANONICAL_ARCH_PREFIXES = [
    os.path.join("docs", "audit"),
    os.path.join("docs", "archive"),
    os.path.join("archive"),
]

# Conservative active prefixes (do not move)
ACTIVE_PREFIXES = [
    "config",
    "tentaculo_link",
    "madre",
    "switch",
    "hermes",
    "hormiguero",
    "shubniggurath",
    "spawner",
    "mcp",
    "operator_backend",
    "operador_ui",
    "scripts",
    "tests",
    "models",
    "data",
    "prompts",
]

# Potential archive/trash prefixes
POTENTIAL_ARCHIVE_PREFIXES = [
    "build",
    "build/artifacts",
    "backups",
    "gateway.deprecated",
    "forensic",
    "logs",
]

TRASH_CANDIDATE_EXT = [".tmp", ".bak", ".old", ".swp"]

rows = []
counts = {
    "ACTIVE": 0,
    "CANONICAL_ARCHIVE": 0,
    "POTENTIAL_ARCHIVE": 0,
    "TRASH_CANDIDATE": 0,
}

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip .git directory
    if ".git" in dirpath.split(os.sep):
        continue
    for fn in filenames:
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT)
        # skip the generated CSV/summary to avoid self-inclusion
        if rel.startswith("docs/archive/") and (
            rel.endswith("repo_inventory.csv")
            or rel.endswith("REPO_CLEANUP_SUMMARY.md")
        ):
            continue
        # classification
        classification = "ACTIVE"
        reason = "Default: in known active area or unclear"
        # canonical archive
        if any(rel.startswith(p) for p in CANONICAL_ARCH_PREFIXES):
            classification = "CANONICAL_ARCHIVE"
            reason = "Located under docs/audit or existing archive folders"
        elif any(rel.startswith(p + os.sep) or rel == p for p in ACTIVE_PREFIXES):
            classification = "ACTIVE"
            reason = "Source code or runtime/configuration directory"
        elif any(
            rel.startswith(p + os.sep) or rel == p for p in POTENTIAL_ARCHIVE_PREFIXES
        ):
            classification = "POTENTIAL_ARCHIVE"
            reason = "Build/artifacts/backups/logs; likely archival candidate"
        elif os.path.splitext(fn)[1].lower() in TRASH_CANDIDATE_EXT:
            classification = "TRASH_CANDIDATE"
            reason = "Temporary or backup file extension"
        else:
            # small heuristics
            if rel.startswith("docs/"):
                # non-audit docs: keep active docs
                classification = "ACTIVE"
                reason = "Documentation (non-audit)"
            else:
                classification = "ACTIVE"
                reason = "Conservative default: keep active"
        size = None
        try:
            size = os.path.getsize(full)
        except Exception:
            size = 0
        rows.append((rel, classification, reason, str(size)))
        counts[classification] = counts.get(classification, 0) + 1

# write CSV
with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["path", "classification", "reason", "size_bytes"])
    for r in sorted(rows):
        writer.writerow(r)

# Ensure README files exist in archive dirs
archive_dirs = [ROOT / "docs" / "archive", ROOT / "archive"]
for d in archive_dirs:
    d.mkdir(parents=True, exist_ok=True)
    readme = d / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Archive folder\n\nThis folder contains archived files produced by the canonical repo cleanup process.\n\n- Why: archived canonical artifacts (audit, reports) retained for history and traceability.\n- Reversibility: no originals are deleted; all archives are copies.\n- No deletions: this process does not remove or move ACTIVE files.\n",
            encoding="utf-8",
        )

# ensure docs/archive/audits README
audits_dir = ROOT / "docs" / "archive" / "audits"
audits_dir.mkdir(parents=True, exist_ok=True)
audits_readme = audits_dir / "README.md"
if not audits_readme.exists():
    audits_readme.write_text(
        "# Archived Audits\n\nThis folder stores archived audit artifacts from `docs/audit`. Originals remain in `docs/audit`.\n\nDo not delete originals. These are lightweight copies for quick access.\n",
        encoding="utf-8",
    )

# write summary
with SUMMARY_PATH.open("w", encoding="utf-8") as f:
    f.write("# Repo Cleanup Summary\n\n")
    f.write(
        "This summary was generated by `scripts/repo_inventory_and_readmes.py`.\n\n"
    )
    f.write("## Counts\n\n")
    for k, v in counts.items():
        f.write(f"- {k}: {v}\n")
    f.write("\n## Output files\n\n")
    f.write(f"- Inventory CSV: {CSV_PATH.relative_to(ROOT)}\n")
    f.write(f"- Summary: {SUMMARY_PATH.relative_to(ROOT)}\n")
    f.write("\n## Notes\n\n")
    f.write("- No files were deleted or moved.\n")
    f.write("- Classification is conservative: if unsure, files are marked ACTIVE.\n")
    f.write("- Review `docs/archive/repo_inventory.csv` before making any changes.\n")

print(f"Inventory written to {CSV_PATH}")
print(f"Summary written to {SUMMARY_PATH}")