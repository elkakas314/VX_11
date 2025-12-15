def test_ensure_cli_registry_enqueues_discovery():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.db_schema import Base, CLIRegistry, TaskQueue

    # create in-memory DB and tables
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()

    # Ensure no CLIRegistry entries
    assert s.query(CLIRegistry).count() == 0

    # Import helper and call with session
    from switch.main import _ensure_cli_registry_or_enqueue

    enqueued = _ensure_cli_registry_or_enqueue(db_session=s)
    assert enqueued is True

    # Confirm TaskQueue row was created
    tq = s.query(TaskQueue).filter_by(source="switch").first()
    assert tq is not None
    assert tq.status == "queued"
