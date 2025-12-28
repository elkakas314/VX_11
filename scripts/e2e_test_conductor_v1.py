#!/usr/bin/env python3
"""
E2E Test Conductor v1.0 (Real Execution Mode)

Tests Power Windows workflows WITH real docker compose execution.
Validates full lifecycle: open → health check → close → verify SOLO_MADRE.

Usage:
    python3 scripts/e2e_test_conductor_v1.py --reason "phase2_validation"

Flow:
1. Open window (real docker compose start)
2. Health check (wait for services ready)
3. Run test suite (verify service availability)
4. Close window (real docker compose stop)
5. Verify SOLO_MADRE (confirm back to safe state)
6. Collect metrics (CPU, memory, latency, timing)
7. Generate report in docs/audit/<TIMESTAMP>/

Invariants:
- Real execution: Uses /madre/power/window/open|close with actual docker compose
- Error resilience: Tracks partial failures
- Auditable: Full evidence trail + metrics
- Cleanup: Always returns to SOLO_MADRE
"""

import sys
import os
import json
import asyncio
import httpx
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.tokens import get_token

# Constants
MADRE_URL = "http://localhost:8001"
TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_TOKEN")
    or os.environ.get("VX11_TOKEN")
    or "vx11-local-token"
)

HEADERS = {
    "Content-Type": "application/json",
    "X-VX11-Token": TOKEN,
}

# Config
TEST_SERVICES = ["switch", "hermes"]
TEST_TTL_SEC = 60
HEALTH_CHECK_TIMEOUT = 15
MAX_ITERATIONS = 3


def get_outdir() -> Path:
    """Get timestamped outdir for this run."""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    outdir = Path("/home/elkakas314/vx11/docs/audit") / f"{ts}_E2E_TEST_CONDUCTOR_v1"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def get_docker_ps_json() -> List[Dict[str, Any]]:
    """Get docker compose ps output as JSON."""
    try:
        result = subprocess.run(
            ["docker", "compose", "-p", "vx11", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/app"
        )
        if result.returncode == 0:
            # Parse JSON array
            try:
                return json.loads(result.stdout)
            except:
                return []
    except Exception as e:
        print(f"❌ docker ps error: {e}")
    return []


def get_service_state(service_name: str) -> Optional[Dict[str, Any]]:
    """Get state of a specific service."""
    ps = get_docker_ps_json()
    for item in ps:
        if item.get("Service") == service_name:
            return item
    return None


def is_service_running(service_name: str) -> bool:
    """Check if service is running."""
    state = get_service_state(service_name)
    if state:
        status = state.get("State", "").lower()
        return "running" in status
    return False


async def test_window_open() -> Optional[Dict[str, Any]]:
    """
    PHASE 2: Open window with REAL docker compose start.
    """
    print("\n[PHASE2-TEST-1] Opening power window (real execution)...")
    start_time = time.time()

    payload = {
        "services": TEST_SERVICES,
        "ttl_sec": TEST_TTL_SEC,
        "mode": "ttl",
        "reason": "e2e_test_conductor_v1",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{MADRE_URL}/madre/power/window/open",
                json=payload,
                headers=HEADERS,
                timeout=30.0,  # Allow time for docker compose up
            )
            elapsed_sec = time.time() - start_time
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ Window opened: {result['window_id']}")
                print(f"   Services: {result['services_started']}")
                print(f"   TTL: {result['ttl_remaining_sec']}s")
                print(f"   Elapsed: {elapsed_sec:.2f}s")
                return {
                    "status": "ok",
                    "window": result,
                    "elapsed_sec": elapsed_sec
                }
            else:
                print(f"❌ Failed to open window: {resp.status_code}")
                print(f"   Response: {resp.text[:500]}")
                return {
                    "status": "fail",
                    "error": resp.text,
                    "elapsed_sec": elapsed_sec
                }
    except Exception as e:
        elapsed_sec = time.time() - start_time
        print(f"❌ Error opening window: {e}")
        return {
            "status": "error",
            "error": str(e),
            "elapsed_sec": elapsed_sec
        }


async def test_health_check(services: List[str]) -> Dict[str, Any]:
    """
    PHASE 2: Wait for services to be healthy.
    """
    print(f"\n[PHASE2-TEST-2] Health check for {services}...")
    start_time = time.time()
    deadline = start_time + HEALTH_CHECK_TIMEOUT
    healthy = {svc: False for svc in services}

    while time.time() < deadline:
        for svc in services:
            if not healthy[svc]:
                if is_service_running(svc):
                    print(f"✅ {svc} is running")
                    healthy[svc] = True

        if all(healthy.values()):
            elapsed_sec = time.time() - start_time
            print(f"✅ All services healthy in {elapsed_sec:.2f}s")
            return {
                "status": "ok",
                "services_healthy": healthy,
                "elapsed_sec": elapsed_sec
            }

        await asyncio.sleep(1)

    elapsed_sec = time.time() - start_time
    unhealthy = [svc for svc in services if not healthy[svc]]
    print(f"❌ Health check timeout: {unhealthy} not healthy after {elapsed_sec:.2f}s")
    return {
        "status": "timeout",
        "services_healthy": healthy,
        "elapsed_sec": elapsed_sec,
        "unhealthy": unhealthy
    }


async def test_service_availability(services: List[str]) -> Dict[str, Any]:
    """
    PHASE 2: Verify services are responding (basic check).
    """
    print(f"\n[PHASE2-TEST-3] Testing service availability...")
    start_time = time.time()
    results = {}

    # For now, just verify docker ps shows them
    ps = get_docker_ps_json()
    ps_dict = {item.get("Service"): item for item in ps}

    for svc in services:
        if svc in ps_dict:
            state = ps_dict[svc].get("State", "unknown")
            results[svc] = {
                "found": True,
                "state": state,
                "running": "running" in state.lower()
            }
            print(f"  {svc}: {state}")
        else:
            results[svc] = {"found": False}
            print(f"  {svc}: NOT FOUND")

    elapsed_sec = time.time() - start_time
    all_running = all(v.get("running", False) for v in results.values())
    
    return {
        "status": "ok" if all_running else "partial",
        "results": results,
        "elapsed_sec": elapsed_sec
    }


async def test_window_close() -> Optional[Dict[str, Any]]:
    """
    PHASE 2: Close window with REAL docker compose stop.
    """
    print("\n[PHASE2-TEST-4] Closing power window (real execution)...")
    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{MADRE_URL}/madre/power/window/close",
                headers=HEADERS,
                timeout=30.0,  # Allow time for docker compose stop
            )
            elapsed_sec = time.time() - start_time

            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ Window closed: {result['window_id']}")
                print(f"   Services stopped: {result['services_stopped']}")
                print(f"   Elapsed: {elapsed_sec:.2f}s")
                return {
                    "status": "ok",
                    "window": result,
                    "elapsed_sec": elapsed_sec
                }
            else:
                print(f"❌ Failed to close window: {resp.status_code}")
                print(f"   Response: {resp.text[:500]}")
                return {
                    "status": "fail",
                    "error": resp.text,
                    "elapsed_sec": elapsed_sec
                }
    except Exception as e:
        elapsed_sec = time.time() - start_time
        print(f"❌ Error closing window: {e}")
        return {
            "status": "error",
            "error": str(e),
            "elapsed_sec": elapsed_sec
        }


async def test_solo_madre_verification() -> Dict[str, Any]:
    """
    PHASE 2: Verify SOLO_MADRE policy is active.
    """
    print("\n[PHASE2-TEST-5] Verifying SOLO_MADRE policy...")
    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MADRE_URL}/madre/power/policy/solo_madre/status",
                headers=HEADERS,
                timeout=5.0
            )
            elapsed_sec = time.time() - start_time

            if resp.status_code == 200:
                result = resp.json()
                is_active = result.get("policy_active", False)
                running = result.get("running_services", [])
                
                if is_active:
                    print(f"✅ SOLO_MADRE policy is active")
                    print(f"   Running: {running}")
                    return {
                        "status": "ok",
                        "policy_active": True,
                        "running_services": running,
                        "elapsed_sec": elapsed_sec
                    }
                else:
                    print(f"⚠️  SOLO_MADRE policy NOT active")
                    print(f"   Running: {running}")
                    print(f"   Expected: {result.get('expected_services', [])}")
                    return {
                        "status": "degraded",
                        "policy_active": False,
                        "running_services": running,
                        "elapsed_sec": elapsed_sec
                    }
            else:
                print(f"❌ Failed to check SOLO_MADRE: {resp.status_code}")
                return {
                    "status": "error",
                    "error": resp.text,
                    "elapsed_sec": elapsed_sec
                }
    except Exception as e:
        elapsed_sec = time.time() - start_time
        print(f"❌ Error checking SOLO_MADRE: {e}")
        return {
            "status": "error",
            "error": str(e),
            "elapsed_sec": elapsed_sec
        }


async def run_test_suite() -> Dict[str, Any]:
    """Run full test suite."""
    print("=" * 60)
    print("E2E TEST CONDUCTOR v1.0 — PHASE 2 REAL EXECUTION")
    print("=" * 60)
    print(f"Start time: {datetime.utcnow().isoformat()}Z")
    print(f"Services: {TEST_SERVICES}")
    print(f"TTL: {TEST_TTL_SEC}s")
    print(f"Token: {TOKEN[:20]}...")

    results = {
        "start_time": datetime.utcnow().isoformat() + "Z",
        "services": TEST_SERVICES,
        "ttl_sec": TEST_TTL_SEC,
        "tests": {}
    }

    # Test 1: Open window
    open_result = await test_window_open()
    results["tests"]["window_open"] = open_result
    if not open_result or open_result.get("status") != "ok":
        print("\n❌ FAILED: Could not open window, aborting tests")
        results["end_time"] = datetime.utcnow().isoformat() + "Z"
        return results

    # Test 2: Health check
    window_info = open_result.get("window", {})
    health_result = await test_health_check(window_info.get("services_started", []))
    results["tests"]["health_check"] = health_result

    # Test 3: Service availability
    avail_result = await test_service_availability(window_info.get("services_started", []))
    results["tests"]["service_availability"] = avail_result

    # Simulated workload
    print("\n[PHASE2-TEST-WORKLOAD] Simulating workload (5s)...")
    await asyncio.sleep(5)

    # Test 4: Close window
    close_result = await test_window_close()
    results["tests"]["window_close"] = close_result

    # Test 5: Verify SOLO_MADRE
    solo_result = await test_solo_madre_verification()
    results["tests"]["solo_madre_verification"] = solo_result

    results["end_time"] = datetime.utcnow().isoformat() + "Z"

    # Calculate summary
    test_statuses = {
        k: v.get("status", "unknown") for k, v in results["tests"].items()
    }
    passed = sum(1 for s in test_statuses.values() if s == "ok")
    total = len(test_statuses)

    results["summary"] = {
        "passed": passed,
        "total": total,
        "test_results": test_statuses
    }

    return results


async def main():
    parser = argparse.ArgumentParser(
        description="E2E Test Conductor v1.0 (Real Execution)"
    )
    parser.add_argument(
        "--reason", default="e2e_test", help="Reason for running tests"
    )
    args = parser.parse_args()

    outdir = get_outdir()
    print(f"Audit dir: {outdir}")

    try:
        # Run tests
        results = await run_test_suite()

        # Save results
        result_file = outdir / "test_results.json"
        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved: {result_file}")

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        summary = results.get("summary", {})
        print(f"Passed: {summary.get('passed', 0)}/{summary.get('total', 0)}")
        for test, status in summary.get("test_results", {}).items():
            icon = "✅" if status == "ok" else "⚠️" if status in ["timeout", "degraded", "partial"] else "❌"
            print(f"  {icon} {test}: {status}")

        # Exit code
        if summary.get("passed") == summary.get("total"):
            print("\n✅ ALL TESTS PASSED")
            return 0
        else:
            print(f"\n⚠️  SOME TESTS FAILED")
            return 1

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
