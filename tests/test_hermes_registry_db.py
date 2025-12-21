def test_model_and_cli_registry_db_crud():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.db_schema import Base, ModelRegistry, CLIRegistry

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()

    # Create ModelRegistry entry
    m = ModelRegistry(
        name="m1",
        path="/tmp/m1.gguf",
        size_bytes=1024,
        provider="gguf",
        type="chat",
        tags='["local"]',
    )
    s.add(m)
    s.commit()

    fetched = s.query(ModelRegistry).filter_by(name="m1").first()
    assert fetched is not None
    assert fetched.path == "/tmp/m1.gguf"

    # Update
    fetched.size_bytes = 2048
    s.add(fetched)
    s.commit()
    updated = s.query(ModelRegistry).filter_by(name="m1").first()
    assert updated.size_bytes == 2048

    # Delete
    s.delete(updated)
    s.commit()
    assert s.query(ModelRegistry).filter_by(name="m1").first() is None

    # CLI Registry DB model CRUD
    c = CLIRegistry(
        name="cli_tool", bin_path="/usr/bin/cli_tool", available=True, cli_type="devops"
    )
    s.add(c)
    s.commit()
    cf = s.query(CLIRegistry).filter_by(name="cli_tool").first()
    assert cf is not None and cf.bin_path == "/usr/bin/cli_tool"

    cf.available = False
    s.add(cf)
    s.commit()
    assert s.query(CLIRegistry).filter_by(name="cli_tool").first().available is False

    s.delete(cf)
    s.commit()
    assert s.query(CLIRegistry).filter_by(name="cli_tool").first() is None
