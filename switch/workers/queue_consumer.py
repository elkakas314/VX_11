"""Minimal persistent queue consumer for Switch.

Reads from `switch_queue_v2` (SQLAlchemy model) in small batches and updates
status. Designed for low CPU usage and safe retries.
"""

from datetime import datetime, timedelta
import time
from typing import Callable, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select, update

from config.db_schema import SwitchQueueV2, get_session


class QueueConsumer:
    def __init__(
        self,
        session_factory: Callable[[], Session] = get_session,
        batch: int = 5,
        poll_interval: float = 0.5,
    ):
        self.session_factory = session_factory
        self.batch = batch
        self.poll_interval = poll_interval
        self._stopped = False

    def stop(self):
        self._stopped = True

    def _fetch_batch(self, session: Session) -> List[SwitchQueueV2]:
        stmt = (
            select(SwitchQueueV2)
            .where(SwitchQueueV2.status == "queued")
            .order_by(SwitchQueueV2.priority.asc(), SwitchQueueV2.created_at.asc())
            .limit(self.batch)
        )
        return session.execute(stmt).scalars().all()

    def _mark_dequeued(self, session: Session, row: SwitchQueueV2):
        row.status = "dequeued"
        row.started_at = datetime.utcnow()
        session.add(row)
        session.commit()

    def _mark_done(self, session: Session, row: SwitchQueueV2, result_size: int = 0):
        row.status = "done"
        row.finished_at = datetime.utcnow()
        row.result_size = result_size
        session.add(row)
        session.commit()

    def _mark_error(self, session: Session, row: SwitchQueueV2, error_message: str):
        row.status = "error"
        row.error_message = error_message[:500]
        row.finished_at = datetime.utcnow()
        session.add(row)
        session.commit()

    def process_item(self, session: Session, row: SwitchQueueV2):
        """Process a single SwitchQueueV2 row.

        By default this calls the local `/switch/task` endpoint to execute the
        structured task. If `VX11_MOCK_PROVIDERS=1` or `settings.testing_mode`
        is set, the call is mocked and a synthetic success result is returned.

        Designed to be safe for local testing (no heavy downloads) and to
        persist minimal result metadata back to the DB via the caller.
        """
        import os
        import json

        try:
            mock = os.getenv("VX11_MOCK_PROVIDERS", "0") == "1"
            # Avoid importing settings at module import time
            from config.settings import settings

            if mock or getattr(settings, "testing_mode", False):
                # Lightweight mocked response
                time.sleep(0.01)
                return {"status": "ok", "mock": True, "content": "mocked"}

            # Call local switch/task HTTP endpoint (assumes same host)
            import http.client
            import urllib.parse

            host = "127.0.0.1"
            port = 8002
            conn = http.client.HTTPConnection(host, port, timeout=30)
            payload = json.dumps(
                {
                    "task_type": row.task_type or "general",
                    "payload": {"payload_hash": row.payload_hash},
                    "source": row.source or "operator",
                }
            )
            headers = {"Content-Type": "application/json"}
            conn.request("POST", "/switch/task", body=payload, headers=headers)
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            try:
                return json.loads(body)
            except Exception:
                return {"status": "error", "raw": body, "code": resp.status}
        except Exception as e:
            # Never raise to keep consumer loop stable
            return {"status": "error", "error": str(e)}

    def run_once(self) -> int:
        """Fetch and process a single batch; return number processed."""
        session = self.session_factory()
        try:
            items = self._fetch_batch(session)
            if not items:
                return 0

            for row in items:
                try:
                    self._mark_dequeued(session, row)
                    res = self.process_item(session, row)
                    self._mark_done(session, row, result_size=len(str(res)))
                except Exception as e:
                    self._mark_error(session, row, str(e))
            return len(items)
        finally:
            session.close()

    def run_forever(self):
        while not self._stopped:
            processed = self.run_once()
            if processed == 0:
                time.sleep(self.poll_interval)


__all__ = ["QueueConsumer"]
