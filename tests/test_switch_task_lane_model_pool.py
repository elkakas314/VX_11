from switch.main import ModelPool


def test_model_pool_select_for_task_keeps_active_and_warm():
    pool = ModelPool(limit=10)
    initial_active = pool.active
    first = pool.select_for_task("audio", metadata={"task_type": "audio"})
    assert pool.active == first
    assert pool.warm is not None
    if initial_active and pool.active != initial_active:
        assert pool.warm == initial_active
    second = pool.select_for_task("audio", metadata={"task_type": "audio"})
    assert pool.active == second
