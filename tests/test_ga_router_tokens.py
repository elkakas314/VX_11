from switch.ga_router import GARouter


class DummyGA:
    def __init__(self):
        self.elite = None
        self.generation = 0

    def get_population_summary(self):
        return {}


def test_ga_router_accepts_tokens_used():
    ga = DummyGA()
    router = GARouter(ga)

    # Replace metrics with dummy recorder to avoid side effects
    class DummyMetrics:
        def record_execution(self, *args, **kwargs):
            # simply accept the call
            return None

    router.metrics = DummyMetrics()

    # Should not raise when called with legacy kw `tokens_used`
    router.record_execution_result(
        engine_name="local",
        task_type="code",
        latency_ms=100,
        success=True,
        cost=0.0,
        tokens_used=123,
    )
