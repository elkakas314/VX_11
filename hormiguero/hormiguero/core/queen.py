"""Queen orchestrator for Hormiguero."""

import asyncio
import random
from datetime import datetime
from typing import Dict, List, Optional

import requests

from hormiguero.config import settings
from hormiguero.core.ants import Ant
from hormiguero.core.db import repo
from hormiguero.core.scanners.db_sanity import scan_db_sanity
from hormiguero.core.scanners.fs_drift import scan_fs_drift
from hormiguero.core.scanners.health import scan_health


class Queen:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.rotation_index = 0
        self.last_scan: Dict[str, object] = {}
        self.backoff_sec = 0
        self.ants = [
            Ant("ant_fs", "fs_drift", "scanner", lambda: scan_fs_drift(root_path)),
            Ant("ant_health", "health", "scanner", scan_health),
            Ant("ant_db", "db_sanity", "scanner", scan_db_sanity),
        ]

    def _select_ants(self, all_checks: bool) -> List[Ant]:
        if all_checks or len(self.ants) == 1:
            return self.ants
        ant = self.ants[self.rotation_index % len(self.ants)]
        self.rotation_index += 1
        return [ant]

    def scan_once(self, all_checks: bool = True) -> Dict[str, object]:
        results: Dict[str, object] = {}
        incidents_created = []
        for ant in self._select_ants(all_checks):
            try:
                result = ant.scanner()
                results[ant.name] = result
                now = datetime.utcnow().isoformat() + "Z"
                repo.upsert_hormiga_state(
                    hormiga_id=ant.ant_id,
                    name=ant.name,
                    role=ant.role,
                    enabled=True,
                    aggression_level=1,
                    scan_interval_sec=settings.scan_interval_sec,
                    last_scan_at=now,
                    last_ok_at=now,
                    last_error_at=None,
                    last_error=None,
                    stats_json=result,
                )
                incidents_created.extend(self._handle_results(ant.name, result))
            except Exception as exc:
                results[ant.name] = {"error": str(exc)}
                now = datetime.utcnow().isoformat() + "Z"
                repo.upsert_hormiga_state(
                    hormiga_id=ant.ant_id,
                    name=ant.name,
                    role=ant.role,
                    enabled=True,
                    aggression_level=1,
                    scan_interval_sec=settings.scan_interval_sec,
                    last_scan_at=now,
                    last_ok_at=None,
                    last_error_at=now,
                    last_error=str(exc),
                    stats_json={"error": str(exc)},
                )
        self.last_scan = {"results": results, "incidents": incidents_created}
        return self.last_scan

    def _handle_results(self, name: str, result: Dict[str, object]) -> List[str]:
        created = []
        if name == "fs_drift":
            status = result.get("status")
            if status == "no_canon":
                incident_id = repo.upsert_incident(
                    kind="fs_drift",
                    severity="info",
                    status="open",
                    title="FS canonical map missing",
                    description="CANONICAL*.json not found for drift scan",
                    source="hormiguero",
                    evidence=result,
                )
                created.append(incident_id)
            elif status == "ok":
                missing = result.get("missing", [])
                extra = result.get("extra", [])
                if missing or extra:
                    incident_id = repo.upsert_incident(
                        kind="fs_drift",
                        severity="warning",
                        status="open",
                        title="FS drift detected",
                        description="Filesystem drift vs canonical map",
                        source="hormiguero",
                        evidence={"missing": missing, "extra": extra},
                    )
                    created.append(incident_id)
                    self._consult_switch(incident_id, result)
                    self._notify_madre_intent(incident_id, result)
        elif name == "health":
            for svc, payload in result.items():
                if not payload.get("ok"):
                    incident_id = repo.upsert_incident(
                        kind="health",
                        severity="high",
                        status="open",
                        title=f"Health check failed: {svc}",
                        description="Core service health check failed",
                        source="hormiguero",
                        evidence={svc: payload},
                    )
                    created.append(incident_id)
        elif name == "db_sanity":
            integrity = result.get("integrity_check")
            if integrity and integrity != "ok":
                incident_id = repo.upsert_incident(
                    kind="db_sanity",
                    severity="critical",
                    status="open",
                    title="DB integrity_check failed",
                    description=str(integrity),
                    source="hormiguero",
                    evidence={"integrity_check": integrity},
                )
                created.append(incident_id)
            hijas_errors = result.get("hijas_errors") or []
            if hijas_errors:
                incident_id = repo.upsert_incident(
                    kind="hijas_runtime",
                    severity="warning",
                    status="open",
                    title="Hijas runtime errors",
                    description="Recent hijas runtime errors/timeouts",
                    source="hormiguero",
                    evidence={"count": len(hijas_errors)},
                )
                created.append(incident_id)
        return created

    def _consult_switch(self, incident_id: str, payload: Dict[str, object]) -> None:
        try:
            resp = requests.post(
                f"{settings.switch_url.rstrip('/')}/switch/advice",
                json={"incident_summary": payload, "context": {"incident_id": incident_id}},
                timeout=settings.http_timeout_sec,
            )
            if resp.status_code == 200:
                repo.set_incident_suggestions(incident_id, resp.json())
        except Exception:
            pass

    def _notify_madre_intent(self, incident_id: str, payload: Dict[str, object]) -> None:
        try:
            requests.post(
                f"{settings.madre_url.rstrip('/')}/madre/intent",
                json={
                    "type": "organize",
                    "payload": payload,
                    "correlation_id": incident_id,
                    "source": "hormiguero",
                },
                timeout=settings.http_timeout_sec,
            )
        except Exception:
            pass

    async def run_loop(self) -> None:
        while True:
            try:
                self.scan_once(all_checks=False)
                self.backoff_sec = 0
            except Exception:
                self.backoff_sec = min(
                    max(self.backoff_sec * 2, 5), settings.scan_backoff_max_sec
                )
            sleep_for = settings.scan_interval_sec + random.randint(
                -settings.scan_jitter_sec, settings.scan_jitter_sec
            )
            if self.backoff_sec:
                sleep_for = max(sleep_for, self.backoff_sec)
            await asyncio.sleep(max(5, sleep_for))
