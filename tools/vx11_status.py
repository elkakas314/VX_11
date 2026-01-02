#!/usr/bin/env python3
"""
VX11 Status handoff generator.
Usage: python3 tools/vx11_status.py --format markdown|json
Output: Status report with git, docker, db, canon metrics
"""
import json
import subprocess
from datetime import datetime


def run_cmd(cmd):
    """Run shell command, return stdout."""
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "N/A"


def get_vx11_status() -> dict:
    """Collect VX11 system status."""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git": {
            "branch": run_cmd("git rev-parse --abbrev-ref HEAD"),
            "head": run_cmd("git rev-parse --short HEAD"),
            "remote": run_cmd("git remote get-url vx_11_remote"),
            "status": run_cmd("git status --short || echo 'clean'")
        },
        "docker": {
            "services": run_cmd("docker compose ps --services --filter status=running"),
            "health": run_cmd("docker compose ps --format 'table {{.Service}}\t{{.Status}}'")
        },
        "db": {
            "path": "data/runtime/vx11.db",
            "integrity": run_cmd("sqlite3 data/runtime/vx11.db 'PRAGMA integrity_check;' 2>/dev/null || echo 'N/A'")
        }
    }


if __name__ == "__main__":
    import sys
    fmt = sys.argv[1] if len(sys.argv) > 1 else "markdown"
    status = get_vx11_status()
    
    if fmt == "json":
        print(json.dumps(status, indent=2))
    else:
        print(f"# VX11 Status ({status['timestamp']})")
        print(f"\n## Git\n- Branch: {status['git']['branch']}\n- HEAD: {status['git']['head']}\n- Status: {status['git']['status']}")
        print(f"\n## Docker\n{status['docker']['health']}")
        print(f"\n## DB\n- Integrity: {status['db']['integrity']}")
