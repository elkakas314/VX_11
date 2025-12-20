"""Health scanner for core services."""

from typing import Dict
import requests

try:
    from hormiguero.config import settings
except ModuleNotFoundError:
    from config import settings


def scan_health() -> Dict[str, Dict[str, object]]:
    targets = {
        "tentaculo_link": f"{settings.tentaculo_url.rstrip('/')}/health",
        "madre": f"{settings.madre_url.rstrip('/')}/health",
        "switch": f"{settings.switch_url.rstrip('/')}/health",
        "spawner": f"{settings.spawner_url.rstrip('/')}/health",
        "manifestator": f"{settings.manifestator_url.rstrip('/')}/health",
    }
    results: Dict[str, Dict[str, object]] = {}
    for name, url in targets.items():
        try:
            resp = requests.get(url, timeout=settings.http_timeout_sec)
            results[name] = {
                "ok": resp.status_code == 200,
                "status_code": resp.status_code,
            }
        except Exception as exc:
            results[name] = {"ok": False, "error": str(exc)}
    return results
