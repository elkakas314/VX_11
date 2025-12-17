def test_circuit_breaker_open_and_reset():
    import time
    from switch.main import CircuitBreaker

    cb = CircuitBreaker(max_failures=2, reset_timeout=1)
    p = "prov_test"
    assert cb.allow(p) is True
    cb.record_failure(p)
    assert cb.allow(p) is True
    cb.record_failure(p)
    assert cb.allow(p) is False
    # simulate timeout passed
    info = cb.state[p]
    info["opened_at"] = time.time() - 2
    cb.state[p] = info
    # now allow should transition to HALF_OPEN and return True
    assert cb.allow(p) is True


def test_score_provider_basic():
    from switch import main as sm

    # set scoring state and latency
    sm.scoring_state["provA"] = {"success": 3, "failures": 1, "latencies": [50]}
    sm.LATENCY_EMA["provA"] = 120.0

    # ensure breaker allows
    try:
        sm.breaker.record_success("provA")
    except Exception:
        pass

    score = sm._score_provider("provA")
    assert isinstance(score, float)
    assert score >= 0.0
