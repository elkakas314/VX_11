"""
Lightweight diagnostics shim for VX11 (safe, non-destructive).
Provides the functions expected by `hormiguero` without requiring external heavy deps.
"""

from typing import List, Dict
import psutil


def list_processes() -> List[Dict[str, str]]:
    """Return a flat list of running processes (pid, name, cmdline).
    Safe: only reads process info and returns minimal fields.
    """
    out = []
    try:
        for p in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
            info = p.info
            out.append({
                "pid": str(info.get("pid")) if info.get("pid") is not None else "",
                "name": info.get("name") or "",
                "cmdline": " ".join(info.get("cmdline") or []),
            })
    except Exception:
        return []
    return out


def list_systemd_units() -> List[Dict[str, str]]:
    """Return empty list by default; containers often don't run systemd.
    Kept as a safe stub to satisfy imports.
    """
    return []


def list_docker_ps() -> List[Dict[str, str]]:
    """Attempt to list docker containers; if docker SDK missing or not available, return empty list.
    This shim avoids importing heavy docker libs.
    """
    try:
        import subprocess
        res = subprocess.run(["docker", "ps", "--format", "{{.ID}} {{.Names}} {{.Status}}"], capture_output=True, text=True, timeout=3)
        out = []
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                parts = line.split(None, 2)
                if parts:
                    out.append({"id": parts[0], "name": parts[1] if len(parts) > 1 else "", "status": parts[2] if len(parts) > 2 else ""})
        return out
    except Exception:
        return []
