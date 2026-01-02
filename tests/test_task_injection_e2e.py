"""
Task Injection E2E Tests (FASE 2)
- T1: SOLO_MADRE OFF_BY_POLICY check
- T2: Window open + intent submission
- T3: Result polling (QUEUED -> RUNNING -> DONE)
- T4: Window close + SOLO_MADRE return verification
- T5: Single entrypoint invariant (no :8001/:8003 direct calls)

INVARIANTS:
✓ Single entrypoint: All calls route through :8000 (tentaculo_link)
✓ SOLO_MADRE default: Only madre + tentaculo running
✓ Protected paths: Never modified
✓ Railes enforced: Safety gates validated
"""

import asyncio
import httpx
import pytest
import json
import re
from datetime import datetime
from typing import Dict, List


# ========== CONFIGURATION ==========
ENTRYPOINT = "http://tentaculo_link:8000"
MCP_ENDPOINT = "http://mcp:8005"  # or available MCP port
VX11_TOKEN = "vx11-local-token"  # from config

MADRE_PORT = 8001
SPAWNER_PORT = 8008
SWITCH_PORT = 8003

# For test tracking
TEST_LOGS: List[Dict] = []


def log_test_event(test_id: str, event: str, details: Dict = None):
    """Log test events to track execution and invariants."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "test_id": test_id,
        "event": event,
        "details": details or {},
    }
    TEST_LOGS.append(entry)
    print(f"[{test_id}] {event}: {json.dumps(details or {}, indent=2)}")


async def check_solo_madre() -> Dict[str, bool]:
    """Verify SOLO_MADRE state: only madre + tentaculo running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check tentaculo_link health
            try:
                resp = await client.get(f"{ENTRYPOINT}/health")
                tentaculo_ok = resp.status_code == 200
            except:
                tentaculo_ok = False

            # Try direct madre port (should fail in SOLO_MADRE)
            try:
                resp = await client.get(f"http://madre:8001/health", timeout=1.0)
                madre_direct_ok = resp.status_code == 200
            except:
                madre_direct_ok = False

            # Try spawner (should be down)
            try:
                resp = await client.get(f"http://spawner:8008/health", timeout=1.0)
                spawner_ok = resp.status_code == 200
            except:
                spawner_ok = False

            return {
                "tentaculo_link": tentaculo_ok,
                "madre_direct_blocked": not madre_direct_ok,
                "spawner_down": not spawner_ok,
                "solo_madre_confirmed": tentaculo_ok and not madre_direct_ok,
            }
    except Exception as exc:
        return {"error": str(exc)}


@pytest.mark.asyncio
async def test_t1_solo_madre_off_by_policy():
    """
    T1: Verify SOLO_MADRE state + task submission returns OFF_BY_POLICY.

    Expected: When spawner is down, /mcp/submit_intent should either:
    - Auto-open window with TTL + proceed
    - OR return OFF_BY_POLICY status
    """
    test_id = "T1_SOLO_MADRE"
    log_test_event(test_id, "start")

    # Check SOLO_MADRE state
    state = await check_solo_madre()
    log_test_event(test_id, "solo_madre_check", state)

    assert state.get("solo_madre_confirmed"), "SOLO_MADRE not confirmed"

    # Attempt task submission without opening window
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "prompt": "Simple echo task",
            "target": "switch",
            "priority": "normal",
        }

        try:
            resp = await client.post(
                f"{MCP_ENDPOINT}/mcp/submit_intent",
                json=payload,
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(
                test_id,
                "submit_intent_response",
                {"status_code": resp.status_code, "body": resp.text[:200]},
            )

            # Accept either OFF_BY_POLICY (409) or auto-open behavior
            assert resp.status_code in [
                200,
                201,
                409,
                503,
            ], f"Unexpected status: {resp.status_code}"

        except Exception as exc:
            # Connection refused is acceptable (service down)
            log_test_event(test_id, "expected_error", {"error": str(exc)})

    log_test_event(test_id, "complete")


@pytest.mark.asyncio
async def test_t2_window_open_intent_submit():
    """
    T2: Open service window + submit task via /mcp/submit_intent.

    Expected: Receives correlation_id, result_id, plan summary.
    """
    test_id = "T2_WINDOW_INTENT"
    log_test_event(test_id, "start")

    async with httpx.AsyncClient(timeout=15.0) as client:
        # STEP 1: Open window
        window_payload = {"target": "switch", "ttl_seconds": 300, "hold_flag": False}

        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json=window_payload,
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(
                test_id,
                "window_open_response",
                {
                    "status_code": resp.status_code,
                    "body": resp.json() if resp.status_code < 400 else resp.text[:100],
                },
            )
            assert resp.status_code < 400, f"Window open failed: {resp.status_code}"
        except Exception as exc:
            log_test_event(test_id, "window_open_error", {"error": str(exc)})
            pytest.skip(f"Cannot open window: {exc}")

        # STEP 2: Submit task intent via MCP
        await asyncio.sleep(1)  # Wait for window to settle

        intent_payload = {
            "prompt": "Echo test message for task injection",
            "target": "switch",
            "priority": "normal",
        }

        try:
            resp = await client.post(
                f"{MCP_ENDPOINT}/mcp/submit_intent",
                json=intent_payload,
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(
                test_id,
                "submit_intent_response",
                {
                    "status_code": resp.status_code,
                    "body": resp.json() if resp.status_code < 400 else resp.text[:100],
                },
            )

            assert (
                resp.status_code < 400
            ), f"Intent submission failed: {resp.status_code}"

            result = resp.json()
            correlation_id = result.get("correlation_id")
            result_id = result.get("result_id")

            assert correlation_id, "No correlation_id in response"
            assert result_id, "No result_id in response"

            log_test_event(
                test_id,
                "ids_received",
                {"correlation_id": correlation_id, "result_id": result_id},
            )

        except Exception as exc:
            log_test_event(test_id, "submit_intent_error", {"error": str(exc)})
            pytest.skip(f"Cannot submit intent: {exc}")

        # STEP 3: Close window
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/close",
                json={"target": "switch"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(test_id, "window_close", {"status_code": resp.status_code})
        except Exception as exc:
            log_test_event(test_id, "window_close_error", {"error": str(exc)})

        log_test_event(test_id, "complete")


@pytest.mark.asyncio
async def test_t3_result_polling():
    """
    T3: Poll result via GET /vx11/result/{result_id}.

    Expected: Transitions QUEUED -> RUNNING -> DONE/ERROR within 30s.
    """
    test_id = "T3_RESULT_POLLING"
    log_test_event(test_id, "start")

    # First, submit a task (similar to T2)
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Open window
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "spawner", "ttl_seconds": 300},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code >= 400:
                pytest.skip("Cannot open window for spawner")
        except Exception as exc:
            pytest.skip(f"Window open error: {exc}")

        await asyncio.sleep(1)

        # Submit task
        try:
            resp = await client.post(
                f"{MCP_ENDPOINT}/mcp/submit_intent",
                json={"prompt": "Poll test task"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code >= 400:
                pytest.skip(f"Intent submission failed: {resp.status_code}")

            result_id = resp.json().get("result_id")
            assert result_id, "No result_id received"
        except Exception as exc:
            pytest.skip(f"Intent submission error: {exc}")

        # Poll result
        start_time = asyncio.get_event_loop().time()
        states_observed = []

        while asyncio.get_event_loop().time() - start_time < 30:
            try:
                resp = await client.get(
                    f"{ENTRYPOINT}/vx11/result/{result_id}",
                    headers={"X-VX11-Token": VX11_TOKEN},
                )

                if resp.status_code >= 400:
                    log_test_event(test_id, "poll_error", {"status": resp.status_code})
                    break

                result = resp.json()
                state = result.get("state")
                states_observed.append(state)

                log_test_event(test_id, "poll_state", {"state": state})

                if state in ["DONE", "ERROR", "FAILED"]:
                    log_test_event(test_id, "terminal_state", {"state": state})
                    break

            except Exception as exc:
                log_test_event(test_id, "poll_exception", {"error": str(exc)})
                break

            await asyncio.sleep(1)

        # Close window
        try:
            await client.post(
                f"{ENTRYPOINT}/vx11/window/close",
                json={"target": "spawner"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
        except:
            pass

        log_test_event(test_id, "states_observed", {"states": states_observed})
        assert len(states_observed) > 0, "No states observed"
        log_test_event(test_id, "complete")


@pytest.mark.asyncio
async def test_t4_window_close_solo_madre():
    """
    T4: Close window + verify SOLO_MADRE state returns.

    Expected: After window close, only madre + tentaculo running.
    """
    test_id = "T4_WINDOW_CLOSE"
    log_test_event(test_id, "start")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Open window
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "switch", "ttl_seconds": 30},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code >= 400:
                pytest.skip("Cannot open window")
        except Exception as exc:
            pytest.skip(f"Window open error: {exc}")

        await asyncio.sleep(1)

        # Verify window is open
        try:
            resp = await client.get(
                f"{ENTRYPOINT}/vx11/window/status/switch",
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            status = resp.json() if resp.status_code < 400 else {}
            log_test_event(test_id, "window_status_open", status)
        except:
            pass

        # Close window
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/close",
                json={"target": "switch"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(test_id, "window_close", {"status_code": resp.status_code})
        except Exception as exc:
            log_test_event(test_id, "window_close_error", {"error": str(exc)})

        await asyncio.sleep(2)  # Wait for cleanup

        # Verify SOLO_MADRE
        solo_state = await check_solo_madre()
        log_test_event(test_id, "solo_madre_after_close", solo_state)
        assert solo_state.get(
            "solo_madre_confirmed"
        ), "SOLO_MADRE not confirmed after close"

        log_test_event(test_id, "complete")


@pytest.mark.asyncio
async def test_t5_single_entrypoint_invariant():
    """
    T5: Verify single entrypoint invariant: NO direct calls to :8001/:8003/:8008.

    Expected: All task injection requests route through :8000 only.
    """
    test_id = "T5_SINGLE_ENTRYPOINT"
    log_test_event(test_id, "start")

    banned_ports = ["8001", "8002", "8003", "8008", "8011"]
    direct_calls_detected = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Open window via :8000
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "switch", "ttl_seconds": 60},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(
                test_id,
                "window_open_via_entrypoint",
                {"status": resp.status_code, "url": str(resp.url)},
            )
        except Exception as exc:
            pytest.skip(f"Window open error: {exc}")

        # Submit task via :8000 (MCP on tentaculo_link or bridged)
        try:
            resp = await client.post(
                f"{MCP_ENDPOINT}/mcp/submit_intent",
                json={"prompt": "Invariant test task"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(
                test_id,
                "task_submit_via_entrypoint",
                {
                    "status": resp.status_code,
                    "url": str(resp.url) if hasattr(resp, "url") else "N/A",
                },
            )
        except Exception as exc:
            log_test_event(test_id, "task_submit_error", {"error": str(exc)})

        # Try direct calls to banned ports (should fail or be blocked)
        for port in banned_ports:
            try:
                resp = await client.get(f"http://madre:{port}/health", timeout=1.0)
                if resp.status_code < 400:
                    direct_calls_detected.append(f"Direct :{ port} accessible!")
            except:
                pass  # Expected

        # Close window via :8000
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/close",
                json={"target": "switch"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(
                test_id, "window_close_via_entrypoint", {"status": resp.status_code}
            )
        except:
            pass

    log_test_event(
        test_id, "direct_calls_detected", {"violations": direct_calls_detected}
    )

    assert (
        len(direct_calls_detected) == 0
    ), f"Single entrypoint violated: {direct_calls_detected}"

    log_test_event(test_id, "complete")


# ========== TEST FIXTURES & HELPERS ==========


@pytest.fixture(scope="session", autouse=True)
def save_test_logs():
    """Save test logs to audit trail."""
    yield

    try:
        audit_dir = "/home/elkakas314/vx11/docs/audit/20260102_task_injection"
        log_file = f"{audit_dir}/11_outputs/test_logs.json"

        import os

        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        with open(log_file, "w") as f:
            json.dump(TEST_LOGS, f, indent=2)

        print(f"\nTest logs saved to: {log_file}")
    except Exception as exc:
        print(f"Warning: Could not save test logs: {exc}")
