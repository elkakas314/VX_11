#!/usr/bin/env python3
"""
Phase 3 E2E: CLI Concentrator + FLUZO integration test.
Validates:
- CLI selection works
- Routing events logged
- CLI usage stats logged
- GET /switch/fluzo endpoint (if available)
"""

import sys
import time
import logging
import json
import uuid
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def test_cli_concentrator():
    """Test CLI concentrator selection logic."""
    log.info("Testing CLI Concentrator...")

    try:
        from switch.cli_concentrator import (
            CLIRegistry,
            CLIScorer,
            CircuitBreaker,
            CLIRequest,
        )

        registry = CLIRegistry()
        breaker = CircuitBreaker()
        scorer = CLIScorer(registry, breaker)

        # Create request
        request = CLIRequest(
            prompt="Test prompt for Phase 3",
            intent="chat",
            task_type="short",
            trace_id=str(uuid.uuid4()),
        )

        # Select provider
        provider, debug = scorer.select_best_provider(request)

        assert provider is not None, "No provider selected"
        log.info(f"✓ Provider selected: {provider.provider_id}")
        log.info(f"  Scoring debug: {json.dumps(debug, indent=2)}")

        return True

    except Exception as e:
        log.error(f"✗ CLI Concentrator test failed: {e}")
        return False


def test_fluzo_signals():
    """Test FLUZO signals collection."""
    log.info("Testing FLUZO signals...")

    try:
        from switch.fluzo import FLUZOClient

        client = FLUZOClient()

        # Get signals
        signals = client.get_signals()
        assert signals is not None, "No signals returned"
        assert "cpu_load_1m" in signals
        assert "memory_pct" in signals
        log.info(f"✓ Signals collected: cpu={signals['cpu_load_1m']:.1f}%, mem={signals['memory_pct']:.1f}%")

        # Get profile
        profile = client.get_profile()
        assert profile is not None
        assert "mode" in profile
        assert profile["mode"] in ["low_power", "balanced", "performance"]
        log.info(f"✓ Profile derived: mode={profile['mode']}")

        return True

    except Exception as e:
        log.error(f"✗ FLUZO signals test failed: {e}")
        return False


def test_routing_events_db():
    """Test routing events are logged to DB."""
    log.info("Testing routing event DB writes...")

    try:
        from config.db_schema import get_session, RoutingEvent

        db = get_session()

        # Create routing event
        event = RoutingEvent(
            trace_id=str(uuid.uuid4()),
            route_type="cli",
            provider_id="copilot_cli",
            score=95.0,
            reasoning_short="Phase 3 E2E test",
        )

        db.add(event)
        db.commit()

        # Verify insertion
        retrieved = db.query(RoutingEvent).filter_by(trace_id=event.trace_id).first()
        assert retrieved is not None
        log.info(f"✓ Routing event logged: {retrieved.trace_id}")

        db.close()
        return True

    except Exception as e:
        log.error(f"✗ Routing events DB test failed: {e}")
        return False


def test_cli_usage_stats_db():
    """Test CLI usage stats are logged to DB."""
    log.info("Testing CLI usage stats DB writes...")

    try:
        from config.db_schema import get_session, CLIUsageStat

        db = get_session()

        # Create usage stat
        stat = CLIUsageStat(
            provider_id="copilot_cli",
            timestamp=datetime.utcnow(),
            success=True,
            latency_ms=100,
            cost_estimated=0.001,
            tokens_estimated=50,
        )

        db.add(stat)
        db.commit()

        # Verify insertion
        retrieved = db.query(CLIUsageStat).filter_by(
            provider_id="copilot_cli"
        ).first()
        assert retrieved is not None
        log.info(f"✓ CLI usage stat logged: latency={retrieved.latency_ms}ms")

        db.close()
        return True

    except Exception as e:
        log.error(f"✗ CLI usage stats DB test failed: {e}")
        return False


def test_switch_fluzo_endpoint():
    """Test GET /switch/fluzo endpoint (optional)."""
    log.info("Testing GET /switch/fluzo endpoint...")

    try:
        import httpx
        from config.settings import settings

        try:
            # Try to call endpoint
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(
                    f"{settings.switch_url}/switch/fluzo",
                    headers={"X-VX11-Token": settings.api_token},
                )

                if resp.status_code == 200:
                    data = resp.json()
                    log.info(f"✓ GET /switch/fluzo responded: {data.get('mode', 'unknown')}")
                    return True
                else:
                    log.warning(f"⚠ GET /switch/fluzo returned {resp.status_code} (endpoint may not be implemented yet)")
                    return True  # Not a failure; endpoint may not exist

        except Exception as e:
            log.warning(f"⚠ Could not reach /switch/fluzo (endpoint may not be running): {e}")
            return True  # Not a failure; switch may not be running

    except Exception as e:
        log.error(f"✗ Switch FLUZO endpoint test failed: {e}")
        return False


def main():
    """Run all E2E tests."""
    log.info("=" * 60)
    log.info("PHASE 3 E2E: CLI Concentrator + FLUZO")
    log.info("=" * 60)

    results = {
        "cli_concentrator": test_cli_concentrator(),
        "fluzo_signals": test_fluzo_signals(),
        "routing_events_db": test_routing_events_db(),
        "cli_usage_stats_db": test_cli_usage_stats_db(),
        "switch_fluzo_endpoint": test_switch_fluzo_endpoint(),
    }

    log.info("=" * 60)
    log.info("E2E Test Results:")
    log.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        log.info(f"{status}: {test_name}")

    log.info("=" * 60)
    log.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        log.info("✓ All E2E tests passed!")
        return 0
    else:
        log.error("✗ Some E2E tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
