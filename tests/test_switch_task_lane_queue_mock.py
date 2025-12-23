import hashlib
import time

import pytest

from config.db_schema import SwitchQueueV2, get_session
from switch.workers.queue_consumer import QueueConsumer


@pytest.mark.integration
def test_queue_consumer_processes_mock_batch(monkeypatch):
    monkeypatch.setenv("VX11_MOCK_PROVIDERS", "1")

    session = get_session("vx11")
    ids = []
    try:
        for i in range(3):
            payload_hash = hashlib.sha256(f"mock-{time.time()}-{i}".encode()).hexdigest()
            row = SwitchQueueV2(
                source="operator",
                priority=5,
                task_type="general",
                payload_hash=payload_hash,
                status="queued",
            )
            session.add(row)
            session.commit()
            ids.append(row.id)
    finally:
        session.close()

    consumer = QueueConsumer()
    processed = consumer.run_once()
    assert processed >= 1

    session = get_session("vx11")
    try:
        rows = session.query(SwitchQueueV2).filter(SwitchQueueV2.id.in_(ids)).all()
        assert rows
        assert all(r.status == "done" for r in rows)
    finally:
        for row_id in ids:
            try:
                session.query(SwitchQueueV2).filter_by(id=row_id).delete()
                session.commit()
            except Exception:
                session.rollback()
        session.close()
