"""Configuration for Hormiguero."""

import os


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


class Settings:
    db_path = os.getenv("HORMIGUERO_DB_PATH", "data/runtime/vx11.db")
    madre_url = os.getenv("HORMIGUERO_MADRE_URL", "http://127.0.0.1:8001")
    switch_url = os.getenv("HORMIGUERO_SWITCH_URL", "http://127.0.0.1:8002")
    manifestator_url = os.getenv("HORMIGUERO_MANIFESTATOR_URL", "http://127.0.0.1:8005")

    scan_interval_sec = _get_int("HORMIGUERO_SCAN_INTERVAL_SEC", 120)
    scan_jitter_sec = _get_int("HORMIGUERO_SCAN_JITTER_SEC", 20)
    scan_backoff_max_sec = _get_int("HORMIGUERO_SCAN_BACKOFF_MAX_SEC", 600)

    http_timeout_sec = _get_float("HORMIGUERO_HTTP_TIMEOUT_SEC", 2.5)
    actions_enabled = os.getenv("HORMIGUERO_ACTIONS_ENABLED", "0") == "1"

    fs_ignore_dirs = {
        ".git",
        "node_modules",
        ".venv",
        "__pycache__",
        "data/runtime",
        "docs/audit",
    }


settings = Settings()
