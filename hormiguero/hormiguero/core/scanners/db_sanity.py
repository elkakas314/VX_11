"""DB sanity scanner."""

from typing import Dict, List

try:
    from hormiguero.core.db.sqlite import get_connection
    from hormiguero.core.db import repo
except ModuleNotFoundError:
    from core.db.sqlite import get_connection
    from core.db import repo


def scan_db_sanity() -> Dict[str, object]:
    integrity = "unknown"
    with get_connection() as conn:
        cur = conn.execute("PRAGMA integrity_check;")
        row = cur.fetchone()
        if isinstance(row, dict):
            integrity = row.get("integrity_check", "unknown")
        elif row:
            integrity = row[0]
        if isinstance(integrity, str):
            integrity = integrity.strip()
    hijas_errors: List[dict] = repo.recent_hijas_errors(limit=20)
    return {
        "integrity_check": integrity,
        "hijas_errors": hijas_errors,
    }
