"""
Seed builder sandbox blueprints into rails_container_blueprints.
Run: python3 -m config.seed_builder_blueprints
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = Path("./data/runtime/vx11.db")


def _latest_map_version(conn: sqlite3.Connection) -> Optional[str]:
    cur = conn.execute(
        """
        SELECT version
        FROM rails_map_versions
        ORDER BY created_at DESC
        LIMIT 1
        """
    )
    row = cur.fetchone()
    return row[0] if row else None


def _blueprint_payloads() -> Dict[str, Dict[str, Any]]:
    policy = {
        "network_mode": "none",
        "read_only_root": True,
        "cap_drop": ["ALL"],
        "no_new_privileges": True,
        "allow_docker_sock": False,
    }
    mounts = [
        {"source": "/jobs", "target": "/jobs", "mode": "rw"},
        {"source": "/canon", "target": "/canon", "mode": "ro"},
    ]
    return {
        "builder_vx11_v1": {
            "purpose": "vx11_canonical_builder",
            "sandbox_policy": policy,
            "mounts": mounts,
            "network_config": "none",
            "cpu_limit_millicores": 500,
            "mem_limit_mb": 512,
            "ttl_sec": 300,
        },
        "builder_external_v1": {
            "purpose": "external_canonical_builder",
            "sandbox_policy": policy,
            "mounts": mounts,
            "network_config": "none",
            "cpu_limit_millicores": 500,
            "mem_limit_mb": 512,
            "ttl_sec": 300,
        },
    }


def seed_builder_blueprints(map_version: Optional[str] = None) -> str:
    if not DB_PATH.exists():
        raise RuntimeError(f"DB not found: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        if map_version is None:
            map_version = _latest_map_version(conn)
        if not map_version:
            raise RuntimeError("No rails_map_versions found; cannot seed blueprints")

        blueprints = _blueprint_payloads()
        for blueprint_id, payload in blueprints.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO rails_container_blueprints (
                    blueprint_id, purpose, sandbox_policy_json, mounts_json,
                    network_config, cpu_limit_millicores, mem_limit_mb, ttl_sec, map_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    blueprint_id,
                    payload["purpose"],
                    json.dumps(payload["sandbox_policy"]),
                    json.dumps(payload["mounts"]),
                    payload["network_config"],
                    payload["cpu_limit_millicores"],
                    payload["mem_limit_mb"],
                    payload["ttl_sec"],
                    map_version,
                ),
            )
        conn.commit()
        return map_version
    finally:
        conn.close()


if __name__ == "__main__":
    version = seed_builder_blueprints()
    print(f"seeded builder blueprints into map_version={version}")
