import os
import shlex
import subprocess
import datetime
import json
import sqlite3
from typing import List, Dict, Any
import shutil

def _default_repo_root() -> str:
    return (
        os.environ.get("VX11_REPO_ROOT")
        or os.environ.get("BASE_PATH")
        or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    )


REPO_ROOT = _default_repo_root()


def _default_audit_base() -> str:
    if os.environ.get("VX11_AUDIT_DIR"):
        return os.environ["VX11_AUDIT_DIR"]
    if os.path.isdir("docs/audit"):
        return "docs/audit"
    if os.path.isdir("/app/logs"):
        return "/app/logs/audit"
    return "logs/audit"


def make_out_dir(base: str = None, prefix: str = "madre_power_saver") -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    base = base or _default_audit_base()
    out = os.path.join(base, f"{prefix}_{ts}")
    os.makedirs(out, exist_ok=True)
    return out


def _run(cmd: str, cwd: str = None, env: Dict[str, str] = None) -> Dict[str, Any]:
    p = subprocess.run(
        cmd, shell=True, cwd=cwd or REPO_ROOT, env=env, capture_output=True, text=True
    )
    return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def snapshot(out_dir: str) -> Dict[str, str]:
    # Collect basic system snapshots and write to out_dir
    files = {}
    files["uptime.txt"] = _run("uptime")
    files["free.txt"] = _run("free -h")
    files["ss_listen.txt"] = _run("ss -ltnp")
    files["ps_top.txt"] = _run("ps aux --sort=-%cpu,-%mem | head -n 200")
    files["docker_ps.txt"] = _run("docker ps --no-trunc")
    for name, res in files.items():
        path = os.path.join(out_dir, name)
        with open(path, "w") as fh:
            fh.write(f"# CMD RESULT:\n")
            fh.write(res.get("stdout", ""))
            if res.get("stderr"):
                fh.write("\n# STDERR:\n")
                fh.write(res.get("stderr"))
    return files


def list_zombies() -> List[Dict[str, str]]:
    out = _run("ps axo pid,ppid,stat,cmd | awk '$3 ~ /Z/ {print}'")
    lines = out.get("stdout", "").strip().splitlines()
    z = []
    for l in lines:
        z.append({"raw": l})
    return z


def write_zombies(out_dir: str) -> None:
    z = list_zombies()
    path = os.path.join(out_dir, "zombies.txt")
    with open(path, "w") as fh:
        for item in z:
            fh.write(item.get("raw") + "\n")


def idle_min(out_dir: str, apply: bool = False) -> Dict[str, Any]:
    """
    If apply is False: produce a plan (list of actions) and write plan.txt
    If apply is True: attempt to `docker compose stop` if docker compose exists and
    send SIGTERM ONLY to node/uvicorn/gunicorn processes whose cmdline contains REPO_ROOT.
    """
    plan = {"actions": []}

    # detect docker compose presence
    dc_check = _run("command -v docker && docker compose version")
    if dc_check.get("returncode") == 0:
        plan["actions"].append({"action": "docker_compose_stop", "available": True})
    else:
        plan["actions"].append({"action": "docker_compose_stop", "available": False})

    # detect candidate processes
    ps_out = _run(
        "ps axo pid,ppid,stat,cmd | grep -E 'node|uvicorn|gunicorn' | grep \"/home/elkakas314/vx11\" || true"
    )
    candidates = []
    for line in ps_out.get("stdout", "").splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) >= 4:
            pid = parts[0]
            cmd = parts[3]
            candidates.append({"pid": pid, "cmd": cmd})

    plan["actions"].append({"action": "term_candidates", "candidates": candidates})

    # Write plan
    plan_path = os.path.join(out_dir, "plan.json")
    import json

    with open(plan_path, "w") as fh:
        json.dump(plan, fh, indent=2)

    results = {"plan": plan}

    if apply:
        # perform docker compose stop if available
        if plan["actions"][0].get("available"):
            results["docker_compose"] = _run("docker compose stop")

        # send SIGTERM to candidates (only if cmd contains REPO_ROOT)
        term_results = []
        for c in candidates:
            try:
                pid = int(c["pid"])
            except Exception:
                continue
            # double-check cmdline contains REPO_ROOT
            try:
                with open(f"/proc/{pid}/cmdline", "r") as fh:
                    cmdline = fh.read()
            except Exception:
                cmdline = c.get("cmd", "")
            if REPO_ROOT in cmdline:
                # safe terminate
                term_results.append({"pid": pid, "result": _run(f"kill -TERM {pid}")})
        results["term_results"] = term_results

    return results


def regen_dbmap(out_dir: str) -> Dict[str, Any]:
    cmd = "PYTHONPATH=. python3 scripts/generate_db_map_from_db.py"
    res = _run(cmd)
    path = os.path.join(out_dir, "regen_dbmap.txt")
    with open(path, "w") as fh:
        fh.write(res.get("stdout", ""))
        if res.get("stderr"):
            fh.write("\n# STDERR:\n")
            fh.write(res.get("stderr"))
    return res


def _load_cleanup_excludes() -> List[str]:
    path = os.path.join(REPO_ROOT, "docs", "audit", "CLEANUP_EXCLUDES_CORE.txt")
    excludes: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                excludes.append(raw.rstrip("/"))
    except Exception:
        return []
    return excludes


def _is_excluded(rel_path: str, excludes: List[str]) -> bool:
    for entry in excludes:
        if not entry:
            continue
        entry = entry.rstrip("/")
        if rel_path == entry or rel_path.startswith(entry + "/"):
            return True
    return False


def rotate_backups(
    out_dir: str,
    keep: int = 2,
    backups_dir: str = None,
    apply: bool = True,
) -> Dict[str, Any]:
    backups_dir = backups_dir or os.path.join(REPO_ROOT, "data", "backups")
    archive_dir = os.path.join(backups_dir, "archived")
    plan_path = os.path.join(out_dir, "backup_rotation_plan.json")
    result_path = os.path.join(out_dir, "backup_rotation_result.json")

    if not os.path.isdir(backups_dir):
        plan = {
            "status": "skipped",
            "reason": "backups_dir_missing",
            "backups_dir": backups_dir,
            "apply": apply,
        }
        with open(plan_path, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, indent=2)
        return plan

    files = []
    for name in os.listdir(backups_dir):
        if name == "archived":
            continue
        path = os.path.join(backups_dir, name)
        if os.path.isfile(path):
            files.append(path)

    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    keep_files = files[: max(keep, 0)]
    archive_files = files[max(keep, 0) :]

    excludes = _load_cleanup_excludes()
    blocked = []
    for path in archive_files:
        rel = os.path.relpath(path, REPO_ROOT)
        if _is_excluded(rel, excludes):
            blocked.append(rel)

    if blocked:
        plan = {
            "status": "aborted",
            "reason": "cleanup_excludes_core_block",
            "blocked": blocked,
            "apply": apply,
            "backups_dir": backups_dir,
            "archive_dir": archive_dir,
        }
        with open(plan_path, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, indent=2)
        return plan

    plan = {
        "status": "planned",
        "apply": apply,
        "backups_dir": backups_dir,
        "archive_dir": archive_dir,
        "keep": [os.path.relpath(p, REPO_ROOT) for p in keep_files],
        "archive": [os.path.relpath(p, REPO_ROOT) for p in archive_files],
    }
    with open(plan_path, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2)

    if not apply:
        return plan

    os.makedirs(archive_dir, exist_ok=True)
    moved = []
    errors = []
    for path in archive_files:
        try:
            dest = os.path.join(archive_dir, os.path.basename(path))
            shutil.move(path, dest)
            moved.append(os.path.relpath(dest, REPO_ROOT))
        except Exception as exc:
            errors.append({"path": os.path.relpath(path, REPO_ROOT), "error": str(exc)})

    result = {
        "status": "ok" if not errors else "partial",
        "moved": moved,
        "errors": errors,
    }
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    return result


def _resolve_db_path(db_path: str = None) -> str:
    if db_path:
        return db_path
    if os.environ.get("VX11_DB_PATH"):
        return os.environ["VX11_DB_PATH"]

    candidates = ["./data/runtime/vx11.db", "/app/data/runtime/vx11.db"]
    for c in candidates:
        if os.path.exists(c):
            return c

    try:
        from config.database import DATABASE_URL  # type: ignore

        if isinstance(DATABASE_URL, str) and DATABASE_URL.startswith("sqlite:"):
            raw = DATABASE_URL[len("sqlite:") :]
            while raw.startswith("/"):
                raw = raw[1:]
            return raw
    except Exception:
        pass

    return "./data/runtime/vx11.db"


def db_retention_cleanup(
    out_dir: str,
    apply: bool = False,
    db_path: str = None,
) -> Dict[str, Any]:
    """
    Plan (apply=False) or execute (apply=True) DB retention cleanup on the unified vx11 SQLite DB.

    Writes evidence files into out_dir:
    - db_retention_plan.json
    - db_retention_result.json (only when apply=True)
    """
    db_path = _resolve_db_path(db_path)

    def _env_int(name: str, default: int) -> int:
        raw = os.environ.get(name)
        if raw is None:
            return default
        try:
            return int(raw)
        except Exception:
            return default

    def _profile() -> str:
        val = (
            os.environ.get("VX11_RETENTION_PROFILE")
            or os.environ.get("VX11_POWER_PROFILE")
            or os.environ.get("VX11_POWER_MODE")
        )
        if val:
            return val.strip().lower()
        if os.environ.get("ULTRA_LOW_MEMORY", "").strip().lower() in ("1", "true", "yes", "on"):
            return "low_power"
        return "default"

    profile = _profile()
    default_log_days = _env_int("VX11_RETENTION_LOG_DAYS", 30)
    low_power_log_days = _env_int("VX11_RETENTION_LOG_DAYS_LOW_POWER", 7)

    def _days_for(table: str, default: int, kind: str = "log") -> int:
        env_name = f"VX11_RETENTION_{table.upper()}_DAYS"
        if env_name in os.environ:
            return _env_int(env_name, default)
        if kind == "log" and profile in ("low_power", "ultra_low_memory"):
            return low_power_log_days
        if kind == "log":
            return default_log_days
        return default

    rules = [
        {"table": "incidents", "ts_col": "detected_at", "days": _days_for("incidents", 90, kind="state")},
        {"table": "pheromone_log", "ts_col": "created_at", "days": _days_for("pheromone_log", 14, kind="log")},
        {"table": "routing_events", "ts_col": "timestamp", "days": _days_for("routing_events", 30, kind="log")},
        {"table": "cli_usage_stats", "ts_col": "timestamp", "days": _days_for("cli_usage_stats", 30, kind="log")},
        {"table": "system_events", "ts_col": "timestamp", "days": _days_for("system_events", 30, kind="log")},
        {"table": "scheduler_history", "ts_col": "timestamp", "days": _days_for("scheduler_history", 30, kind="log")},
        {"table": "intents_log", "ts_col": "created_at", "days": _days_for("intents_log", 30, kind="log")},
        {"table": "ia_decisions", "ts_col": "created_at", "days": _days_for("ia_decisions", 30, kind="log")},
        {
            "table": "model_usage_stats",
            "ts_col": "created_at",
            "days": _days_for("model_usage_stats", 90, kind="state"),
        },
    ]

    plan: Dict[str, Any] = {
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "db_path": db_path,
        "apply": apply,
        "profile": profile,
        "defaults": {
            "log_days_default": default_log_days,
            "log_days_low_power": low_power_log_days,
        },
        "rules": rules,
        "actions": [],
        "errors": [],
    }

    os.makedirs(out_dir, exist_ok=True)
    plan_path = os.path.join(out_dir, "db_retention_plan.json")

    def _record_error(msg: str) -> None:
        plan["errors"].append(msg)

    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout=5000;")
        cur.execute("PRAGMA foreign_keys=ON;")

        for r in rules:
            table = r["table"]
            ts_col = r["ts_col"]
            days = int(r["days"])
            cutoff = f"-{days} days"

            try:
                total = cur.execute(f"SELECT COUNT(1) FROM {table}").fetchone()[0]
                to_delete = cur.execute(
                    f"SELECT COUNT(1) FROM {table} WHERE {ts_col} IS NOT NULL AND {ts_col} < datetime('now', ?)",
                    (cutoff,),
                ).fetchone()[0]
            except Exception as e:
                _record_error(f"{table}: precheck_failed: {e}")
                continue

            plan["actions"].append(
                {
                    "table": table,
                    "ts_col": ts_col,
                    "days": days,
                    "total_rows": total,
                    "rows_eligible": to_delete,
                    "index_sql": f"CREATE INDEX IF NOT EXISTS idx_{table}_{ts_col} ON {table}({ts_col});",
                    "delete_sql": f"DELETE FROM {table} WHERE {ts_col} IS NOT NULL AND {ts_col} < datetime('now', '-{days} days');",
                }
            )

        with open(plan_path, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, indent=2, ensure_ascii=False)

        if not apply:
            conn.close()
            return {"status": "planned", "db_path": db_path, "plan_path": plan_path}

        result = {
            "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
            "db_path": db_path,
            "applied": True,
            "tables": [],
            "checkpoint": None,
            "errors": [],
        }

        try:
            cur.execute("BEGIN;")
            for a in plan["actions"]:
                table = a["table"]
                try:
                    cur.execute(a["index_sql"])
                except Exception as e:
                    result["errors"].append(f"{table}: index_failed: {e}")

                try:
                    cutoff = f"-{int(a['days'])} days"
                    before = cur.execute(f"SELECT COUNT(1) FROM {table}").fetchone()[0]
                    cur.execute(
                        f"DELETE FROM {table} WHERE {a['ts_col']} IS NOT NULL AND {a['ts_col']} < datetime('now', ?)",
                        (cutoff,),
                    )
                    deleted = cur.rowcount
                    after = cur.execute(f"SELECT COUNT(1) FROM {table}").fetchone()[0]
                    result["tables"].append(
                        {
                            "table": table,
                            "deleted": deleted,
                            "rows_before": before,
                            "rows_after": after,
                        }
                    )
                except Exception as e:
                    result["errors"].append(f"{table}: delete_failed: {e}")
            cur.execute("COMMIT;")
        except Exception as e:
            try:
                cur.execute("ROLLBACK;")
            except Exception:
                pass
            result["errors"].append(f"transaction_failed: {e}")

        try:
            chk = cur.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchall()
            result["checkpoint"] = [tuple(r) for r in chk]
        except Exception as e:
            result["errors"].append(f"checkpoint_failed: {e}")

        try:
            cur.execute("PRAGMA optimize;")
        except Exception as e:
            result["errors"].append(f"optimize_failed: {e}")

        result_path = os.path.join(out_dir, "db_retention_result.json")
        with open(result_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)

        conn.close()
        return {
            "status": "applied",
            "db_path": db_path,
            "plan_path": plan_path,
            "result_path": result_path,
        }
    except Exception as e:
        _record_error(f"db_retention_cleanup_failed: {e}")
        with open(plan_path, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, indent=2, ensure_ascii=False)
        return {
            "status": "error",
            "db_path": db_path,
            "plan_path": plan_path,
            "error": str(e),
        }


def final_report(out_dir: str) -> str:
    # produce a short md with links to created files
    files = os.listdir(out_dir)
    md = [
        "# Power Saver Report",
        "",
        f"Timestamp: {datetime.datetime.utcnow().isoformat()}",
        "",
        "## Files",
    ]
    for f in sorted(files):
        md.append(f"- {f}")
    path = os.path.join(out_dir, "POWER_SAVER_REPORT.md")
    with open(path, "w") as fh:
        fh.write("\n".join(md))
    return path
