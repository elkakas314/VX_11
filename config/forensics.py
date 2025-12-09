from pathlib import Path
import hashlib
import json
import datetime
import os
import tarfile
import shutil
import traceback


REPO_ROOT = Path(__file__).resolve().parents[1]
FORENSIC_ROOT = REPO_ROOT / "forensic"


def _now_ts():
    return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def ensure_forensic_dirs(module: str):
    """Ensure forensic directories for a module exist."""
    (FORENSIC_ROOT / module / "logs").mkdir(parents=True, exist_ok=True)
    (FORENSIC_ROOT / module / "hashes").mkdir(parents=True, exist_ok=True)
    (FORENSIC_ROOT / "snapshots").mkdir(parents=True, exist_ok=True)
    (FORENSIC_ROOT / "crashes").mkdir(parents=True, exist_ok=True)


def compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_repo_hashes(filter_exts=None) -> dict:
    """Compute SHA256 hashes for files in the repo. Optionally filter by extensions."""
    data = {}
    for p in REPO_ROOT.rglob("*"):
        if p.is_file():
            if filter_exts and p.suffix not in filter_exts:
                continue
            try:
                data[str(p.relative_to(REPO_ROOT))] = compute_file_hash(p)
            except Exception:
                data[str(p.relative_to(REPO_ROOT))] = "<error>"
    return data


def write_hash_manifest(module: str, filter_exts=None) -> Path:
    ensure_forensic_dirs(module)
    manifest = compute_repo_hashes(filter_exts=filter_exts)
    ts = _now_ts()
    out = FORENSIC_ROOT / module / "hashes" / f"manifest_{ts}.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump({"timestamp": ts, "manifest": manifest}, f, indent=2, ensure_ascii=False)
    return out


def write_log(module: str, message: str, level: str = "INFO") -> Path:
    ensure_forensic_dirs(module)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    logdir = FORENSIC_ROOT / module / "logs"
    out = logdir / f"{date}.log"
    with out.open("a", encoding="utf-8") as f:
        f.write(f"{ts} [{level}] {message}\n")
    return out


def record_crash(module: str, exc: Exception = None):
    ensure_forensic_dirs(module)
    ts = _now_ts()
    crash_dir = FORENSIC_ROOT / "crashes" / f"CRASH_{ts}"
    crash_dir.mkdir(parents=True, exist_ok=True)
    info_path = crash_dir / f"{module}_trace.txt"
    with info_path.open("w", encoding="utf-8") as f:
        f.write("Timestamp: " + ts + "\n")
        if exc is not None:
            f.write("Exception:\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
        else:
            f.write("No exception object provided.\n")
    # copy a small set of important files for context
    candidates = [REPO_ROOT / "tentaculo_link" / "main.py", REPO_ROOT / "switch" / "main.py"]
    for c in candidates:
        if c.exists():
            try:
                shutil.copy2(c, crash_dir / c.name)
            except Exception:
                pass
    return crash_dir


def create_snapshot(name: str = None) -> Path:
    ensure_forensic_dirs("snapshot")
    ts = _now_ts()
    if not name:
        name = f"snapshot_{ts}"
    out = FORENSIC_ROOT / "snapshots" / f"{name}.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        # archive repo contents excluding forensic and tmp
        for p in REPO_ROOT.iterdir():
            if p.name in ("forensic", ".tmp_copilot", ".git"):
                continue
            tar.add(p, arcname=p.name)
    return out


def quick_health_check() -> dict:
    """Return a small health report for the repo structure."""
    report = {
        "forensic_root": str(FORENSIC_ROOT),
        "exists": FORENSIC_ROOT.exists(),
        "modules": {},
    }
    for mod in ("tentaculo_link", "madre", "switch", "hormiguero", "manifestator", "mcp", "shubniggurath", "hermes"):
        mod_path = REPO_ROOT / mod / "main.py"
        report["modules"][mod] = {"exists": mod_path.exists()}
    return report


def rotate_crashes(retain: int = 10):
    """Keep only the most recent `retain` crash dirs; remove older ones."""
    crash_root = FORENSIC_ROOT / "crashes"
    if not crash_root.exists():
        return []
    entries = sorted([p for p in crash_root.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    removed = []
    for old in entries[retain:]:
        try:
            shutil.rmtree(old)
            removed.append(str(old))
        except Exception:
            pass
    return removed


def prune_snapshots(limit: int = 5):
    """Keep only `limit` most recent snapshots."""
    snap_root = FORENSIC_ROOT / "snapshots"
    if not snap_root.exists():
        return []
    entries = sorted([p for p in snap_root.iterdir() if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)
    removed = []
    for old in entries[limit:]:
        try:
            old.unlink()
            removed.append(str(old))
        except Exception:
            pass
    return removed


def forensic_usage_summary() -> dict:
    """Return a small summary of forensic storage usage."""
    total = 0
    parts = {}
    if FORENSIC_ROOT.exists():
        for p in FORENSIC_ROOT.rglob('*'):
            if p.is_file():
                try:
                    sz = p.stat().st_size
                    total += sz
                except Exception:
                    sz = 0
    parts['bytes_total'] = total
    return parts


# ========== LEDGER EN BD ==========
def record_ledger_event(session, event: str, payload: str = ""):
    """
    Registra evento en tabla forensic_ledger (append-only).
    """
    try:
        from config.db_schema import ForensicLedger

        h = ForensicLedger.compute_hash(event, payload or "")
        entry = ForensicLedger(event=event, payload=payload or "", hash=h)
        session.add(entry)
        session.commit()
    except Exception:
        # En caso de error se registra a archivo para no perder el evento
        write_log("forensic", f"ledger_fallback:{event}:{payload}")


def ttl_cleanup(session, days: int = 30):
    """
    Archiva registros antiguos a archivo simple (append-only, no borra de tabla).
    """
    try:
        from datetime import datetime, timedelta
        from config.db_schema import ForensicLedger

        cutoff = datetime.utcnow() - timedelta(days=days)
        old = session.query(ForensicLedger).filter(ForensicLedger.created_at < cutoff).all()
        if not old:
            return 0
        archive_dir = FORENSIC_ROOT / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        out = archive_dir / f"ledger_archive_{_now_ts()}.log"
        with out.open("a", encoding="utf-8") as f:
            for row in old:
                f.write(f"{row.created_at.isoformat()}Z {row.event} {row.payload}\n")
        session.commit()
        return len(old)
    except Exception as e:
        write_log("forensic", f"ttl_cleanup_error:{e}", level="ERROR")
        return 0
