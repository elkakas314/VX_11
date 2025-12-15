from switch.intelligence_layer import RoutingResult, RoutingDecision


def test_routingresult_has_cost_alias():
    r = RoutingResult(
        decision=RoutingDecision.FALLBACK, primary_engine="stub", estimated_cost=3.14
    )
    assert hasattr(r, "cost")
    assert r.cost == 3.14
