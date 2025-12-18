import os
import shlex
import subprocess
import datetime
from typing import List, Dict, Any

REPO_ROOT = "/home/elkakas314/vx11"


def make_out_dir(base: str = "docs/audit", prefix: str = "madre_power_saver") -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
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
