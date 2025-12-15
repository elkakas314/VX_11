def test_cli_registry_module_basic():
    from switch.hermes.cli_registry import get_cli_registry, EngineType

    reg = get_cli_registry()
    # After initialization, there should be several engines registered
    engines = reg.list_engines()
    assert len(engines) >= 1

    # Test list_available_engines (token env may hide some, but function should run)
    available = reg.list_available_engines()
    assert isinstance(available, list)

    # Suggest engine for local tasks should prefer LOCAL type if available
    suggestion = reg.suggest_engine_for_task("local")
    if suggestion:
        assert suggestion.engine_type == EngineType.LOCAL or suggestion.available

    # Update metrics and ranking should run without exceptions
    for e in engines[:2]:
        reg.update_metrics(e.name, latency_ms=100.0, success=True)

    ranking = reg.rank_engines()
    assert isinstance(ranking, list)
