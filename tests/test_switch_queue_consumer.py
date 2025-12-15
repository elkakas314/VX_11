import time
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.db_schema import Base, SwitchQueueV2
from switch.workers.queue_consumer import QueueConsumer


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_queue_consumer_processes_item():
    Session = sessionmaker
    # create engine + session
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # insert one queued item (use required columns)
    row = SwitchQueueV2(source="test", priority=1, task_type="chat", payload_hash="hash1", status="queued")
    session.add(row)
    session.commit()

    # consumer using this session factory
    def sf():
        return SessionLocal()

    consumer = QueueConsumer(session_factory=sf, batch=2, poll_interval=0.01)

    processed = consumer.run_once()
    assert processed == 1

    # verify row updated
    s2 = SessionLocal()
    r = s2.query(SwitchQueueV2).filter_by(id=row.id).first()
    assert r is not None
    assert r.status == "done"
