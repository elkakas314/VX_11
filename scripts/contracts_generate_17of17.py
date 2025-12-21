#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import List, Tuple


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(cmd: List[str]) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as exc:
        return exc.returncode, exc.output.decode("utf-8", errors="replace")


def _health_check(url: str) -> Tuple[bool, str]:
    code, out = _run(["curl", "-s", "-S", "-m", "3", "-w", "%{http_code}", url])
    if code != 0:
        return False, out
    if len(out) >= 3:
        body, status = out[:-3], out[-3:]
    else:
        body, status = out, ""
    ok = status == "200"
    return ok, f"status={status} body={body[:500]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    raw_dir = outdir / "raw" / "contracts_17of17"
    raw_dir.mkdir(parents=True, exist_ok=True)

    contracts = []

    def add_contract(cid: int, name: str, status: str, evidence: List[str], notes: str = ""):
        contracts.append(
            {
                "id": cid,
                "name": name,
                "status": status,
                "evidence_paths": evidence,
                "notes": notes,
            }
        )

    # 1) Canonical files present
    canonical_files = [
        "docs/CANONICAL_MASTER_VX11.json",
        "docs/CANONICAL_RUNTIME_POLICY_VX11.json",
        "docs/CANONICAL_FS_VX11.json",
        "docs/CANONICAL_SEMANTIC_VX11.json",
        "docs/CANONICAL_FLOWS_VX11.json",
    ]
    presence_lines = []
    missing = []
    for f in canonical_files:
        if Path(f).exists():
            presence_lines.append(f"PRESENT {f}")
        else:
            presence_lines.append(f"MISSING {f}")
            missing.append(f)
    presence_path = raw_dir / "canonical_presence_check.txt"
    _write(presence_path, "\n".join(presence_lines) + "\n")
    add_contract(
        1,
        "Canonical files present",
        "PASS" if not missing else "FAIL",
        [str(presence_path)],
        "missing=" + ",".join(missing) if missing else "",
    )

    # 2) Alias canonical byte-identical
    alias_path = raw_dir / "canonical_alias_hashes.txt"
    alias_lines = []
    alias_ok = True
    for module in ["manifestator", "shubniggurath"]:
        files = sorted(Path(f"docs/canonical/modules/{module}").glob("*canonical*.json"))
        alias_lines.append(f"{module}:")
        if len(files) < 2:
            alias_ok = False
            alias_lines.append("  missing canonical alias pair")
            continue
        hashes = []
        for f in files:
            h = _sha256(f)
            hashes.append(h)
            alias_lines.append(f"  {f} {h}")
        if len(set(hashes)) != 1:
            alias_ok = False
    _write(alias_path, "\n".join(alias_lines) + "\n")
    add_contract(
        2,
        "Alias canonical byte-identical",
        "PASS" if alias_ok else "FAIL",
        [str(alias_path)],
    )

    # 3) Runtime policy solo_madre and defaults OFF manifestator/shub
    policy_path = Path("docs/CANONICAL_RUNTIME_POLICY_VX11.json")
    policy_text = policy_path.read_text() if policy_path.exists() else ""
    solo = "solo_madre" in policy_text
    try:
        policy_json = json.loads(policy_text) if policy_text else {}
        solo = solo or policy_json.get("default_mode") == "solo_madre"
    except json.JSONDecodeError:
        pass
    manifestator_off = bool(re.search(r"manifestator.*(off|disabled)", policy_text, re.I))
    shub_off = bool(re.search(r"shubniggurath.*(off|disabled)", policy_text, re.I))
    policy_ev = raw_dir / "runtime_policy_extract.txt"
    _write(
        policy_ev,
        "\n".join(
            [
                f"solo_madre_in_file: {solo}",
                f"manifestator_off_hint: {manifestator_off}",
                f"shubniggurath_off_hint: {shub_off}",
            ]
        )
        + "\n",
    )
    add_contract(
        3,
        "Runtime policy solo_madre + defaults OFF manifestator/shub",
        "PASS" if (solo and manifestator_off and shub_off) else "FAIL",
        [str(policy_ev)],
    )

    # 4) Madre /health OK
    ok, detail = _health_check("http://127.0.0.1:8001/health")
    madre_ev = raw_dir / "madre_health.txt"
    _write(madre_ev, detail + "\n")
    add_contract(4, "Madre /health OK", "PASS" if ok else "FAIL", [str(madre_ev)])

    # 5) Tentaculo_link /health OK
    ok, detail = _health_check("http://127.0.0.1:8000/health")
    tent_ev = raw_dir / "tentaculo_link_health.txt"
    _write(tent_ev, detail + "\n")
    add_contract(5, "Tentaculo_link /health OK", "PASS" if ok else "FAIL", [str(tent_ev)])

    # 6) OpenAPI accessible (core)
    ok, detail = _health_check("http://127.0.0.1:8001/openapi.json")
    openapi_ev = raw_dir / "madre_openapi.txt"
    _write(openapi_ev, detail + "\n")
    add_contract(6, "OpenAPI accessible (core)", "PASS" if ok else "FAIL", [str(openapi_ev)])

    # 7) DB integrity_check OK
    db_path = "data/runtime/vx11.db"
    integrity_ev = raw_dir / "db_integrity_check.txt"
    code, out = _run(["sqlite3", db_path, "PRAGMA integrity_check;"])
    _write(integrity_ev, out)
    add_contract(7, "DB integrity_check OK", "PASS" if "ok" in out.lower() else "FAIL", [str(integrity_ev)])

    # 8) DB quick_check OK
    quick_ev = raw_dir / "db_quick_check.txt"
    code, out = _run(["sqlite3", db_path, "PRAGMA quick_check;"])
    _write(quick_ev, out)
    add_contract(8, "DB quick_check OK", "PASS" if "ok" in out.lower() else "FAIL", [str(quick_ev)])

    # 9) DB foreign_key_check OK
    fk_ev = raw_dir / "db_foreign_key_check.txt"
    code, out = _run(["sqlite3", db_path, "PRAGMA foreign_keys=ON; PRAGMA foreign_key_check;"])
    _write(fk_ev, out)
    add_contract(9, "DB foreign_key_check OK", "PASS" if out.strip() == "" else "FAIL", [str(fk_ev)])

    # 10) Module assignment mapping available (DB_MAP)
    db_map = Path("docs/audit/DB_MAP_v7_FINAL.md")
    count = 0
    if db_map.exists():
        count = sum(1 for line in db_map.read_text().splitlines() if line.lstrip().startswith("### "))
    map_ev = raw_dir / "db_map_presence.txt"
    _write(map_ev, f"db_map_exists: {db_map.exists()}\nheading_count: {count}\n")
    add_contract(10, "Module assignment mapping available (DB_MAP)", "PASS" if count > 0 else "FAIL", [str(map_ev)])

    # 11) No secrets in tree (heuristic, redacted)
    secrets_ev = raw_dir / "secrets_scan_files.txt"
    pattern = "(token|api_key|secret|password)"
    rg_cmd = [
        "rg",
        "--files-with-matches",
        "--no-messages",
        "-i",
        "-e",
        pattern,
        "-g",
        "!tokens.env",
        "-g",
        "!tokens.env.master",
        "-g",
        "!.venv/**",
        "-g",
        "!data/backups/**",
        "-g",
        "!node_modules/**",
    ]
    code, out = _run(rg_cmd)
    _write(secrets_ev, out)
    secrets_ok = (code == 1 and out.strip() == "") or (code == 0 and out.strip() == "")
    add_contract(11, "No secrets in tree (heuristic)", "PASS" if secrets_ok else "FAIL", [str(secrets_ev)])

    # 12) No prohibited ports listening in solo_madre
    ports_ev = raw_dir / "listening_ports.txt"
    code, out = _run(["ss", "-ltn"])
    _write(ports_ev, out)
    prohibited = []
    for line in out.splitlines():
        m = re.search(r":(\\d+)\\s", line)
        if not m:
            continue
        port = int(m.group(1))
        if 8002 <= port <= 8020:
            prohibited.append(port)
    add_contract(12, "No prohibited ports listening in solo_madre", "PASS" if not prohibited else "FAIL", [str(ports_ev)], "prohibited=" + ",".join(map(str, prohibited)) if prohibited else "")

    # 13) Scripts safety guards present (cleanup excludes)
    cleanup_excludes = Path("docs/audit/CLEANUP_EXCLUDES_CORE.txt")
    cleanup_ev = raw_dir / "cleanup_excludes_present.txt"
    _write(cleanup_ev, f"exists: {cleanup_excludes.exists()}\nsize: {cleanup_excludes.stat().st_size if cleanup_excludes.exists() else 0}\n")
    add_contract(13, "Scripts safety guards present (cleanup excludes)", "PASS" if cleanup_excludes.exists() else "FAIL", [str(cleanup_ev)])

    # 14) Switch/Hermes canonical path
    switch_hermes = Path("switch/hermes")
    hermes_root = Path("hermes")
    hermes_ev = raw_dir / "hermes_path_check.txt"
    _write(
        hermes_ev,
        f"switch/hermes exists: {switch_hermes.exists()}\nroot hermes exists: {hermes_root.exists()}\n",
    )
    add_contract(14, "Hermes lives in switch/hermes", "PASS" if switch_hermes.exists() else "FAIL", [str(hermes_ev)])

    # 15) Operator passive mode (no active backend)
    operator_ev = raw_dir / "operator_passive_check.txt"
    code, out = _run(["docker", "ps", "--format", "{{.Names}}"])
    running = "operator-backend" in out or "operator_backend" in out
    code, ports_out = _run(["ss", "-ltn"])
    listening_8011 = "8011" in ports_out
    _write(operator_ev, f"container_running: {running}\nlistening_8011: {listening_8011}\n")
    add_contract(15, "Operator mode passive (no controlling endpoints)", "PASS" if (not running and not listening_8011) else "FAIL", [str(operator_ev)])

    # 16) Manifestator plan-only and OFF
    manifest_ev = raw_dir / "manifestator_policy_check.txt"
    manifest_text = policy_text + (Path("docs/CANONICAL_MASTER_VX11.json").read_text() if Path("docs/CANONICAL_MASTER_VX11.json").exists() else "")
    manifest_off = bool(re.search(r"manifestator[^\\n]*?(off|disabled)", manifest_text, re.I))
    manifest_plan = bool(re.search(r"manifestator[^\\n]*?plan[_\\s-]?only[^\\n]*?(true|1)", manifest_text, re.I))
    _write(manifest_ev, f"manifestator_off: {manifest_off}\nmanifestator_plan_only: {manifest_plan}\n")
    add_contract(16, "Manifestator plan-only and OFF", "PASS" if (manifest_off and manifest_plan) else "FAIL", [str(manifest_ev)])

    # 17) Shub madre-managed and OFF
    shub_ev = raw_dir / "shub_policy_check.txt"
    shub_off = bool(re.search(r"shubniggurath[^\\n]*?(off|disabled)", policy_text, re.I))
    shub_managed = bool(re.search(r"shubniggurath[^\\n]*?madre", policy_text, re.I))
    _write(shub_ev, f"shub_off: {shub_off}\nshub_madre_managed: {shub_managed}\n")
    add_contract(17, "Shub madre-managed and OFF", "PASS" if (shub_off and shub_managed) else "FAIL", [str(shub_ev)])

    out_path = outdir / "contracts_17of17.json"
    out_path.write_text(json.dumps(contracts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
