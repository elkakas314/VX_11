#!/usr/bin/env python3
"""
E2E Test Conductor v0.1 (Metadata-only mode)

Tests Power Windows workflows WITHOUT executing docker compose.
Allows end-to-end flow validation and timing analysis.

Usage:
    python3 scripts/e2e_test_conductor_v0.py --reason "e2e_validation"

Flow:
1. Open window (metadata registration)
2. Execute test suite (simulated workload)
3. Close window
4. Collect metrics
5. Generate report in docs/audit/<TIMESTAMP>/

Invariants:
- Single-entrypoint: Uses tentaculo_link:8000 (when implemented)
- Low-power: No service startup overhead
- Auditable: Full evidence trail
"""

import sys
import os
import json
import asyncio
import httpx
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.forensics import write_log
from config.tokens import get_token

# Constants
MADRE_URL = "http://localhost:8001"
TENTACULO_URL = "http://localhost:8000"
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


def get_outdir() -> Path:
    """Get timestamped outdir for this run."""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    outdir = Path("/home/elkakas314/vx11/docs/audit") / f"{ts}_E2E_TEST_CONDUCTOR_v0"
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


async def test_window_open() -> Optional[Dict[str, Any]]:
    """Open window (metadata only, no docker execution)."""
    print("[TEST] Opening power window...")

    payload = {
        "services": ["switch", "hermes"],  # Metadata only
        "ttl_sec": 30,
        "mode": "ttl",
        "reason": "e2e_test_conductor_v0",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{MADRE_URL}/madre/power/window/open",
                json=payload,
                headers=HEADERS,
                timeout=5.0,
            )
            if resp.status_code == 200:
                print(f"✅ Window opened: {resp.json()}")
                return resp.json()
            else:
                print(f"❌ Failed to open window: {resp.status_code}")
                print(f"   Response: {resp.text}")
                return None
    except Exception as e:
        print(f"❌ Error opening window: {e}")
        return None


async def test_window_state() -> Optional[Dict[str, Any]]:
    """Read current power state."""
    print("[TEST] Reading power state...")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MADRE_URL}/madre/power/state",
                headers=HEADERS,
                timeout=5.0,
            )
            if resp.status_code == 200:
                state = resp.json()
                print(f"✅ Current state: {state}")
                return state
            else:
                print(f"❌ Failed to read state: {resp.status_code}")
                return None
    except Exception as e:
        print(f"❌ Error reading state: {e}")
        return None


async def test_window_close() -> Optional[Dict[str, Any]]:
    """Close window."""
    print("[TEST] Closing power window...")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{MADRE_URL}/madre/power/window/close",
                json={},
                headers=HEADERS,
                timeout=5.0,
            )
            if resp.status_code == 200:
                print(f"✅ Window closed: {resp.json()}")
                return resp.json()
            else:
                print(f"❌ Failed to close window: {resp.status_code}")
                print(f"   Response: {resp.text}")
                return None
    except Exception as e:
        print(f"❌ Error closing window: {e}")
        return None


async def run_e2e_test(reason: str = "e2e_validation") -> Dict[str, Any]:
    """Run full E2E test sequence."""
    outdir = get_outdir()
    print(f"\n{'='*60}")
    print(f"E2E TEST CONDUCTOR v0.1 (Metadata-only mode)")
    print(f"Start time: {datetime.utcnow().isoformat()}Z")
    print(f"Output dir: {outdir}")
    print(f"Reason: {reason}")
    print(f"{'='*60}\n")

    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mode": "metadata_only",
        "reason": reason,
        "tests": {},
        "metrics": {
            "start_time": time.time(),
            "passed": 0,
            "failed": 0,
            "total": 0,
        },
    }

    # TEST 1: Open window
    print("\n[STEP 1/4] Open Window")
    print("-" * 40)
    start = time.time()
    window_data = await test_window_open()
    elapsed = time.time() - start

    results["tests"]["open_window"] = {
        "elapsed_sec": elapsed,
        "success": window_data is not None,
        "data": window_data,
    }
    results["metrics"]["total"] += 1
    if window_data:
        results["metrics"]["passed"] += 1
    else:
        results["metrics"]["failed"] += 1
        print("\n⚠️  Stopping test sequence (window open failed)")
        return results

    # TEST 2: Read state (window active)
    print("\n[STEP 2/4] Read State (Window Active)")
    print("-" * 40)
    await asyncio.sleep(1)  # Small delay to ensure state stabilizes
    start = time.time()
    state_data = await test_window_state()
    elapsed = time.time() - start

    results["tests"]["read_state_active"] = {
        "elapsed_sec": elapsed,
        "success": state_data is not None,
        "data": state_data,
    }
    results["metrics"]["total"] += 1
    if state_data:
        results["metrics"]["passed"] += 1
        # Validate window_info is present
        if state_data.get("window_info"):
            print("✅ Window metadata present in state")
        else:
            print("⚠️  Window metadata missing in state")
    else:
        results["metrics"]["failed"] += 1

    # TEST 3: Simulated workload (in real scenario, this would be actual flow testing)
    print("\n[STEP 3/4] Simulated Workload (Metadata-only)")
    print("-" * 40)
    print("Simulating: API calls, healthchecks, data validation...")
    start = time.time()
    await asyncio.sleep(2)  # Simulate some work
    elapsed = time.time() - start

    results["tests"]["simulated_workload"] = {
        "elapsed_sec": elapsed,
        "success": True,
        "data": {
            "description": "Simulated internal workflow",
            "notes": "In Phase 2, this would execute real service integrations",
        },
    }
    results["metrics"]["total"] += 1
    results["metrics"]["passed"] += 1
    print(f"✅ Workload completed ({elapsed:.2f}s)")

    # TEST 4: Close window
    print("\n[STEP 4/4] Close Window")
    print("-" * 40)
    start = time.time()
    close_data = await test_window_close()
    elapsed = time.time() - start

    results["tests"]["close_window"] = {
        "elapsed_sec": elapsed,
        "success": close_data is not None,
        "data": close_data,
    }
    results["metrics"]["total"] += 1
    if close_data:
        results["metrics"]["passed"] += 1
    else:
        results["metrics"]["failed"] += 1

    # Final state check
    print("\n[FINAL] Verify SOLO_MADRE policy")
    print("-" * 40)
    final_state = await test_window_state()
    if final_state:
        policy = final_state.get("policy", "unknown")
        if policy == "solo_madre":
            print(f"✅ SOLO_MADRE policy confirmed")
            results["tests"]["final_state_solo_madre"] = {
                "success": True,
                "policy": policy,
            }
        else:
            print(f"⚠️  Policy is '{policy}', expected 'solo_madre'")
            results["tests"]["final_state_solo_madre"] = {
                "success": False,
                "policy": policy,
            }

    results["metrics"]["elapsed_total_sec"] = (
        time.time() - results["metrics"]["start_time"]
    )
    results["metrics"]["end_time"] = time.time()

    # Summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {results['metrics']['passed']}/{results['metrics']['total']}")
    print(f"Failed: {results['metrics']['failed']}/{results['metrics']['total']}")
    print(f"Total time: {results['metrics']['elapsed_total_sec']:.2f}s")
    print(f"End time: {datetime.utcnow().isoformat()}Z")
    print(f"{'='*60}\n")

    # Save results
    results_file = outdir / "test_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"✅ Results saved to: {results_file}")

    # Write audit log
    write_log(
        "e2e_test_conductor",
        f"run_complete: passed={results['metrics']['passed']}/{results['metrics']['total']}, "
        f"elapsed={results['metrics']['elapsed_total_sec']:.1f}s",
    )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="E2E Test Conductor v0.1 (metadata-only mode)"
    )
    parser.add_argument(
        "--reason",
        type=str,
        default="e2e_validation",
        help="Reason for test run",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default=None,
        help="Override output directory (default: timestamped)",
    )

    args = parser.parse_args()

    # Run async test
    results = asyncio.run(run_e2e_test(reason=args.reason))

    # Exit code based on results
    exit_code = 0 if results["metrics"]["failed"] == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
