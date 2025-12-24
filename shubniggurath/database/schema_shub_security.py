"""
Shub Security Schema — VX11 Canonical v1.7.1

Tablas de seguridad para Shub:
- shub_request_nonces: replay protection (HMAC validation)
- shub_window_cache (opcional): window token validation cache

Esta es la única fuente de verdad para esquemas de seguridad de Shub.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional

DATABASE_PATH = os.getenv("VX11_DB_PATH", "data/runtime/vx11.db")


# =============================================================================
# SCHEMA DEFINITIONS (Canonical)
# =============================================================================

SCHEMA_REQUEST_NONCES = """
CREATE TABLE IF NOT EXISTS shub_request_nonces (
    nonce_id TEXT PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    ttl_seconds INTEGER DEFAULT 120,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nonce_id),
    INDEX idx_timestamp(timestamp)
);
"""

SCHEMA_WINDOW_CACHE = """
CREATE TABLE IF NOT EXISTS shub_window_cache (
    token_hash TEXT PRIMARY KEY,
    token_iat INTEGER NOT NULL,
    token_exp INTEGER NOT NULL,
    valid BOOLEAN DEFAULT 1,
    scopes TEXT NOT NULL,
    cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_token_exp(token_exp)
);
"""

INDICES = {
    "shub_request_nonces": [
        "CREATE INDEX IF NOT EXISTS idx_shub_nonce_timestamp ON shub_request_nonces(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_shub_nonce_created ON shub_request_nonces(created_at);",
    ],
    "shub_window_cache": [
        "CREATE INDEX IF NOT EXISTS idx_shub_cache_exp ON shub_window_cache(token_exp);",
    ],
}


# =============================================================================
# INITIALIZATION & MAINTENANCE
# =============================================================================


def init_security_schema(db_path: str = DATABASE_PATH) -> bool:
    """
    Initialize security tables if missing.

    Args:
        db_path: Path to vx11.db

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute(SCHEMA_REQUEST_NONCES)
        cursor.execute(SCHEMA_WINDOW_CACHE)

        # Create indices
        for table, index_stmts in INDICES.items():
            for stmt in index_stmts:
                cursor.execute(stmt)

        conn.commit()
        conn.close()

        return True
    except Exception as e:
        print(f"ERROR: init_security_schema failed: {e}")
        return False


def cleanup_expired_nonces(
    db_path: str = DATABASE_PATH, max_age_seconds: int = 300, limit: int = 1000
) -> int:
    """
    Delete expired nonces (garbage collection).

    Args:
        db_path: Path to vx11.db
        max_age_seconds: Delete nonces older than this (default 5 min)
        limit: Max rows to delete per call (prevent DB churn)

    Returns:
        Number of rows deleted
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)

        cursor.execute(
            """
            DELETE FROM shub_request_nonces
            WHERE created_at < ?
            LIMIT ?
            """,
            (cutoff_time.isoformat(), limit),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted
    except Exception as e:
        print(f"ERROR: cleanup_expired_nonces failed: {e}")
        return 0


def cleanup_expired_tokens(db_path: str = DATABASE_PATH, limit: int = 500) -> int:
    """
    Delete expired window tokens from cache.

    Args:
        db_path: Path to vx11.db
        limit: Max rows to delete per call

    Returns:
        Number of rows deleted
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        now_ts = int(datetime.now().timestamp())

        cursor.execute(
            """
            DELETE FROM shub_window_cache
            WHERE token_exp < ?
            LIMIT ?
            """,
            (now_ts, limit),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted
    except Exception as e:
        print(f"ERROR: cleanup_expired_tokens failed: {e}")
        return 0


# =============================================================================
# QUERY HELPERS (for EntryGuard + WindowGuard)
# =============================================================================


def check_nonce_exists(nonce_id: str, db_path: str = DATABASE_PATH) -> bool:
    """
    Check if nonce has been used (replay detection).

    Returns:
        True if nonce exists (replay detected), False if new
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM shub_request_nonces WHERE nonce_id = ? LIMIT 1", (nonce_id,)
        )

        result = cursor.fetchone() is not None
        conn.close()

        return result
    except Exception as e:
        print(f"ERROR: check_nonce_exists failed: {e}")
        return False


def insert_nonce(
    nonce_id: str, timestamp: int, ttl_seconds: int = 120, db_path: str = DATABASE_PATH
) -> bool:
    """
    Insert a new nonce (idempotent via PRIMARY KEY).

    Args:
        nonce_id: Unique nonce identifier
        timestamp: Unix timestamp
        ttl_seconds: Time-to-live (seconds)
        db_path: Path to vx11.db

    Returns:
        True if inserted, False if duplicate or error
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO shub_request_nonces (nonce_id, timestamp, ttl_seconds)
            VALUES (?, ?, ?)
            """,
            (nonce_id, timestamp, ttl_seconds),
        )

        conn.commit()
        conn.close()

        return True
    except sqlite3.IntegrityError:
        # Nonce already exists (duplicate/replay)
        return False
    except Exception as e:
        print(f"ERROR: insert_nonce failed: {e}")
        return False


def cache_window_token(
    token_hash: str,
    token_iat: int,
    token_exp: int,
    scopes: str,
    db_path: str = DATABASE_PATH,
) -> bool:
    """
    Cache a window token validation result.

    Args:
        token_hash: SHA256(token)
        token_iat: issued-at timestamp
        token_exp: expiration timestamp
        scopes: comma-separated scopes (e.g., "shub:mutate,shub:jobs:submit")
        db_path: Path to vx11.db

    Returns:
        True if cached, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO shub_window_cache
            (token_hash, token_iat, token_exp, scopes)
            VALUES (?, ?, ?, ?)
            """,
            (token_hash, token_iat, token_exp, scopes),
        )

        conn.commit()
        conn.close()

        return True
    except Exception as e:
        print(f"ERROR: cache_window_token failed: {e}")
        return False


def get_cached_token_scopes(
    token_hash: str, db_path: str = DATABASE_PATH
) -> Optional[str]:
    """
    Get cached scopes for a token (if not expired).

    Returns:
        Comma-separated scopes, or None if not cached / expired
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        now_ts = int(datetime.now().timestamp())

        cursor.execute(
            """
            SELECT scopes FROM shub_window_cache
            WHERE token_hash = ? AND token_exp > ?
            LIMIT 1
            """,
            (token_hash, now_ts),
        )

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None
    except Exception as e:
        print(f"ERROR: get_cached_token_scopes failed: {e}")
        return None
