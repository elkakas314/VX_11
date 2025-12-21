#!/usr/bin/env python3
"""Generate SCORECARD.json and FINAL_REPORT.md from the latest docs/audit/<TS> run."""
import json
import os
import sys
from datetime import datetime


def latest_audit_dir(base="docs/audit"):
    entries = []
    try:
        for name in os.listdir(base):
            path = os.path.join(base, name)
            if os.path.isdir(path) and name.isdigit():
                entries.append((name, path))
            elif os.path.isdir(path) and name.startswith("202"):
                entries.append((name, path))
    except FileNotFoundError:
        return None
    if not entries:
        return None
    entries.sort()
    return entries[-1][1]


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def build_scorecard(folder):
    score = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "evidence_folder": folder,
        "services_checked": 0,
        "services_up": [],
        "services_down_or_unreachable": [],
        "sqlite": {},
        "db_map_generated": False,
        "backup_present": False,
        "git_head": None,
        "recommended_actions": [],
    }

    # health files
    health_files = [f for f in os.listdir(folder) if f.startswith("health_")]
    score["services_checked"] = len(health_files)
    for hf in health_files:
        data = read_file(os.path.join(folder, hf))
        if not data or data.startswith("ERR"):
            score["services_down_or_unreachable"].append(
                hf.replace("health_", "").replace(".txt", "")
            )
        else:
            score["services_up"].append(hf.replace("health_", "").replace(".txt", ""))

    # sqlite checks
    score["sqlite"]["quick_check"] = (
        read_file(os.path.join(folder, "sqlite_quick_check.txt")) or "missing"
    )
    score["sqlite"]["integrity_check"] = (
        read_file(os.path.join(folder, "sqlite_integrity_check.txt")) or "missing"
    )
    fk = read_file(os.path.join(folder, "sqlite_foreign_key_check.txt"))
    score["sqlite"]["foreign_key_check"] = fk if fk is not None else "missing"

    # DB map
    score["db_map_generated"] = os.path.exists(
        "docs/audit/DB_SCHEMA_v7_FINAL.json"
    ) and os.path.exists("docs/audit/DB_MAP_v7_FINAL.md")

    # backup
    score["backup_present"] = os.path.exists(os.path.join(folder, "vx11.db.backup"))

    # git head
    gh = read_file(os.path.join(folder, "git_head.txt"))
    if gh:
        score["git_head"] = gh.strip()

    # recommended actions
    if score["services_down_or_unreachable"]:
        score["recommended_actions"].append("start_missing_services_via_docker_compose")
    if (
        score["sqlite"].get("quick_check") != "ok"
        or score["sqlite"].get("integrity_check") != "ok"
    ):
        score["recommended_actions"].append("investigate_sqlite_integrity")
    score["recommended_actions"].append(
        "do_not_run_db_retention_without_backup_and_triple_lock"
    )

    return score


def write_scorecard(folder, score):
    path_json = os.path.join(folder, "SCORECARD.json")
    path_md = os.path.join(folder, "SCORECARD.md")
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(score, f, indent=4)

    md = []
    md.append("**Scorecard — {}**\n".format(score["timestamp"]))
    md.append("\n")
    md.append("- **Commit:** {}".format(score.get("git_head") or "unknown"))
    md.append("- **Evidencia:** {}".format(folder))
    md.append("- **Servicios verificados:** {}".format(score["services_checked"]))
    md.append(
        "- **Servicios arriba:** {}".format(",".join(score["services_up"]) or "none")
    )
    md.append(
        "- **Servicios no alcanzables:** {}".format(
            ",".join(score["services_down_or_unreachable"]) or "none"
        )
    )
    md.append(
        "- **SQLite:** quick_check={}, integrity_check={}, foreign_key_check={}".format(
            score["sqlite"].get("quick_check"),
            score["sqlite"].get("integrity_check"),
            score["sqlite"].get("foreign_key_check"),
        )
    )
    md.append(
        "- **DB map:** {}".format("generado" if score["db_map_generated"] else "no")
    )
    md.append(
        "- **Backup DB:** {}".format("presente" if score["backup_present"] else "no")
    )
    md.append(
        "- **Acciones recomendadas:** {}".format(
            ", ".join(score["recommended_actions"])
        )
    )

    with open(path_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


def main():
    folder = latest_audit_dir()
    if not folder:
        print("No audit folder found under docs/audit", file=sys.stderr)
        sys.exit(2)
    score = build_scorecard(folder)
    write_scorecard(folder, score)
    print("Wrote SCORECARD to", folder)


if __name__ == "__main__":
    main()
