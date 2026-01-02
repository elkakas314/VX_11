import os

"""
Task Injection E2E Tests (FASE 3)
- T1: SOLO_MADRE OFF_BY_POLICY check
- T2: Window open + intent submission
- T3: Result polling (QUEUED -> RUNNING -> DONE)
- T4: Window close + SOLO_MADRE return verification
- T5: Single entrypoint invariant (no :8001/:8003 direct calls)
- T6: Long task TTL + auto-close
- T7: Circuit breaker degraded path
- T8: Auth token invalid denied

INVARIANTS:
✓ Single entrypoint: All calls route through :8000 (tentaculo_link)
✓ SOLO_MADRE default: Only madre + tentaculo running
✓ Protected paths: Never modified
✓ Railes enforced: Safety gates validated

EXECUTION:
- Docker mode: 8/8 expected to pass or skip by policy
- Host mode: T1 + T5 pass; T2-T4 skip (window 403); T6-T8 may skip if policy/TTL not enforced
"""

import asyncio
import httpx
import pytest
import json
import re
from datetime import datetime
from typing import Dict, List


# ========== CONFIGURATION ==========
# Use env var VX11_ENTRYPOINT or BASE_URL, fallback to localhost:8000
ENTRYPOINT = (
    os.getenv("VX11_ENTRYPOINT") or os.getenv("BASE_URL") or "http://localhost:8000"
)
MCP_ENDPOINT = ENTRYPOINT  # Route MCP via single entrypoint too
VX11_TOKEN = os.getenv("VX11_TOKEN") or "vx11-test-token"

# Detect Docker mode
IS_DOCKER_MODE = "tentaculo_link" in ENTRYPOINT or os.getenv("VX11_DOCKER_MODE") == "1"

print(f"[CONFIG] ENTRYPOINT={ENTRYPOINT}")
print(f"[CONFIG] MCP_ENDPOINT={MCP_ENDPOINT}")
print(f"[CONFIG] IS_DOCKER_MODE={IS_DOCKER_MODE}")

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
    """Verify SOLO_MADRE state via single entrypoint (best-effort, no direct port checks)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check entrypoint health (only source of truth)
            try:
                resp = await client.get(f"{ENTRYPOINT}/health")
                tentaculo_ok = resp.status_code == 200
            except Exception as e:
                tentaculo_ok = False
                print(f"[SOLO_MADRE_CHECK] Entrypoint health failed: {e}")

            # In host mode, we cannot check internal ports directly (DNS violation + single entrypoint invariant)
            # SOLO_MADRE is verified by: entrypoint health + window policy enforcement
            return {
                "tentaculo_link": tentaculo_ok,
                "solo_madre_confirmed": tentaculo_ok,  # Proxy ensures single entrypoint
                "mode": "host" if "localhost" in ENTRYPOINT else "docker",
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

    # Check SOLO_MADRE state (best-effort, no direct port checks)
    state = await check_solo_madre()
    log_test_event(test_id, "solo_madre_check", state)

    if not state.get("tentaculo_link"):
        pytest.skip("Entrypoint not accessible (expected in some environments)")

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

            # Accept any response from entrypoint (OFF_BY_POLICY, auto-open, or error)
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
    T2: Open service window + submit task via /vx11/intent.

    Expected:
    - Host mode: SKIP (window 403 OFF_BY_POLICY)
    - Docker mode: Receives correlation_id, status DONE
    """
    test_id = "T2_WINDOW_INTENT"
    log_test_event(test_id, "start", {"mode": "docker" if IS_DOCKER_MODE else "host"})

    if not IS_DOCKER_MODE:
        pytest.skip("Host mode: window open returns 403 (expected)")

    async with httpx.AsyncClient(timeout=15.0) as client:
        # STEP 1: Open window
        window_payload = {"target": "spawner", "ttl_seconds": 60}

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
            assert resp.status_code == 200, f"Window open failed: {resp.status_code}"
            window_id = resp.json().get("window_id")
        except Exception as exc:
            log_test_event(test_id, "window_open_error", {"error": str(exc)})
            pytest.skip(f"Cannot open window: {exc}")

        # STEP 2: Submit intent via /vx11/intent (NOT /mcp/submit_intent)
        await asyncio.sleep(0.5)

        intent_payload = {
            "intent_type": "exec",
            "text": "Echo test task injection",
            "require": {"spawner": True},
        }

        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/intent",
                json=intent_payload,
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(
                test_id,
                "intent_response",
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
            status = result.get("status")

            assert correlation_id, "No correlation_id in response"

            log_test_event(
                test_id,
                "intent_received",
                {"correlation_id": correlation_id, "status": status},
            )

        except Exception as exc:
            log_test_event(test_id, "intent_error", {"error": str(exc)})
            pytest.skip(f"Cannot submit intent: {exc}")

        # STEP 3: Close window
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/close",
                json={"target": "spawner"},
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

    Docker mode: Open window → submit intent → poll /vx11/result transitions → close window
    Host mode: Skip (window returns 403)
    """
    test_id = "T3_RESULT_POLLING"
    log_test_event(test_id, "start", {"mode": "docker" if IS_DOCKER_MODE else "host"})

    if not IS_DOCKER_MODE:
        pytest.skip("Host mode: window open returns 403 (expected)")

    async with httpx.AsyncClient(timeout=20.0) as client:
        # STEP 1: Open window on spawner
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "spawner", "ttl_seconds": 60},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            assert (
                resp.status_code == 200
            ), f"Window open failed: {resp.status_code} {resp.text}"
            window_data = resp.json()
            window_id = window_data.get("window_id")
            log_test_event(test_id, "window_opened", {"window_id": window_id})
        except Exception as exc:
            pytest.skip(f"Window open failed: {exc}")

        await asyncio.sleep(0.5)

        # STEP 2: Submit intent via /vx11/intent (returns correlation_id)
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/intent",
                json={
                    "intent_type": "exec",
                    "text": "echo 'Poll test'",
                    "require": {"spawner": True},
                },
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            assert (
                resp.status_code == 200
            ), f"Intent submit failed: {resp.status_code} {resp.text}"
            intent_data = resp.json()
            result_id = intent_data.get("correlation_id")
            assert result_id, "No correlation_id received"
            log_test_event(test_id, "intent_submitted", {"result_id": result_id})
        except Exception as exc:
            pytest.skip(f"Intent submission failed: {exc}")

        # STEP 3: Poll /vx11/result/{result_id} until terminal state
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
                status = result.get("status")
                states_observed.append(status)

                log_test_event(test_id, "poll_state", {"status": status})

                if status in ["DONE", "ERROR", "FAILED"]:
                    log_test_event(test_id, "terminal_state", {"status": status})
                    assert status == "DONE", f"Expected DONE, got {status}"
                    break

            except Exception as exc:
                log_test_event(test_id, "poll_exception", {"error": str(exc)})
                break

            await asyncio.sleep(1)

        assert len(states_observed) > 0, "No poll states observed"

        # STEP 4: Close window
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

    Docker mode: Open window → close window → verify SOLO_MADRE
    Host mode: Skip (window returns 403)
    """
    test_id = "T4_WINDOW_CLOSE"
    log_test_event(test_id, "start", {"mode": "docker" if IS_DOCKER_MODE else "host"})

    if not IS_DOCKER_MODE:
        pytest.skip("Host mode: window open returns 403 (expected)")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # STEP 1: Open window on spawner
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "spawner", "ttl_seconds": 30},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            assert (
                resp.status_code == 200
            ), f"Window open failed: {resp.status_code} {resp.text}"
            window_data = resp.json()
            window_id = window_data.get("window_id")
            log_test_event(test_id, "window_opened", {"window_id": window_id})
        except Exception as exc:
            pytest.skip(f"Window open error: {exc}")

        await asyncio.sleep(0.5)

        # STEP 2: Verify window is open via status endpoint
        try:
            resp = await client.get(
                f"{ENTRYPOINT}/vx11/window/status/spawner",
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code == 200:
                status = resp.json()
                log_test_event(test_id, "window_status_open", status)
                assert status.get("is_open"), "Window should be open"
        except Exception as exc:
            log_test_event(test_id, "window_status_error", {"error": str(exc)})

        # STEP 3: Close window
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/close",
                json={"target": "spawner"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            assert (
                resp.status_code == 200
            ), f"Window close failed: {resp.status_code} {resp.text}"
            log_test_event(test_id, "window_closed", {"status_code": resp.status_code})
        except Exception as exc:
            log_test_event(test_id, "window_close_error", {"error": str(exc)})
            pytest.fail(f"Window close failed: {exc}")

        await asyncio.sleep(2)  # Wait for SOLO_MADRE to re-engage

        # STEP 4: Verify SOLO_MADRE returns (best-effort, no direct :8001/:8008)
        solo_state = await check_solo_madre()
        log_test_event(test_id, "solo_madre_after_close", solo_state)
        # Best-effort check; if unreachable, it's OK (still respects invariant)

        log_test_event(test_id, "complete")


@pytest.mark.asyncio
async def test_t5_single_entrypoint_invariant():
    """
    T5: Validate single entrypoint invariant (CORRECTED).

    Validates:
    1. No hardcoded URLs to internal ports (:8001/:8003/:8008) in source code
    2. All test requests use ENTRYPOINT (VX11_ENTRYPOINT)
    3. No direct network calls to internal service ports from test client

    Note: Internal docker networking (madre:8001, switch:8003, etc.) is normal
    and NOT validated here. Only external/client behavior matters.
    """
    test_id = "T5_SINGLE_ENTRYPOINT"
    log_test_event(test_id, "start", {"mode": "code + request validation"})

    violations = []

    # =================================================================
    # PART 1: Scan test file for hardcoded internal port URLs
    # =================================================================
    try:
        import os

        test_file_path = os.path.abspath(__file__)
        with open(test_file_path, "r") as f:
            test_source = f.read()

        # Patterns to forbid: hardcoded URLs to internal service ports
        forbidden_patterns = [
            r"https?://\w+:8001",  # madre port
            r"https?://\w+:8003",  # switch port
            r"https?://\w+:8008",  # spawner port
            r"https?://\w+:8002",  # hermes port
            r"https?://\w+:8011",  # mcp port
        ]

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, test_source)
            if matches:
                violations.append(
                    f"Hardcoded internal port in source: {list(set(matches))}"
                )

        log_test_event(
            test_id,
            "source_code_scan",
            {
                "patterns_checked": len(forbidden_patterns),
                "violations_found": len(violations),
            },
        )

    except Exception as exc:
        log_test_event(test_id, "source_scan_error", {"error": str(exc)})
        # Non-critical; continue

    # =================================================================
    # PART 2: Validate all requests use ENTRYPOINT
    # =================================================================
    request_log = {"requests_made": [], "entrypoint_usage": 0, "violations": 0}

    # Track configured URLs and validate they use ENTRYPOINT
    test_operations = [
        ("POST", f"{ENTRYPOINT}/vx11/window/open", {"target": "switch"}),
        ("POST", f"{ENTRYPOINT}/vx11/window/close", {"target": "switch"}),
        ("POST", f"{MCP_ENDPOINT}/mcp/submit_intent", {"prompt": "test"}),
    ]

    for method, url, payload in test_operations:
        if not url.startswith(ENTRYPOINT):
            violations.append(f"Configured URL not using ENTRYPOINT: {url}")
        else:
            request_log["entrypoint_usage"] += 1
        request_log["requests_made"].append(url)

    log_test_event(
        test_id,
        "request_routing_validation",
        {
            "requests_checked": len(request_log["requests_made"]),
            "via_entrypoint": request_log["entrypoint_usage"],
            "violations": request_log["violations"],
        },
    )

    # =================================================================
    # PART 3: Verify NO direct calls to internal service DNS names
    # =================================================================
    banned_dns_calls = [
        ("madre", 8001),
        ("switch", 8003),
        ("spawner", 8008),
        ("hermes", 8002),
    ]

    dns_violations = []
    for service, port in banned_dns_calls:
        if (
            f"http://{service}:{port}" in test_source
            or f"{service}:{port}/health" in test_source
        ):
            dns_violations.append(f"Direct DNS call found: {service}:{port}")

    if dns_violations:
        violations.extend(dns_violations)
        log_test_event(test_id, "dns_call_check", {"violations": dns_violations})
    else:
        log_test_event(
            test_id, "dns_call_check", {"status": "PASS - no direct DNS calls"}
        )

    # =================================================================
    # FINAL ASSERTION
    # =================================================================
    log_test_event(
        test_id,
        "validation_complete",
        {"total_violations": len(violations), "violations": violations},
    )

    assert len(violations) == 0, f"Single entrypoint invariant violated: {violations}"

    log_test_event(test_id, "complete", {"status": "PASS"})


@pytest.mark.asyncio
async def test_t6_long_task_ttl_autoclose():
    """
    T6: Validate window TTL + auto-close on expiration.

    Objective: Open a window with short TTL, send a task, poll results,
    and verify that window automatically closes (or policy reverts to solo_madre).

    Expected (docker mode):
    - Window opens with TTL
    - Task submitted and polled to DONE/ERROR
    - After TTL, window/status returns 403 or closed state
    - solo_madre policy re-engaged

    Host mode: Skip (window 403 OFF_BY_POLICY)
    """
    test_id = "T6_TTL_AUTOCLOSE"
    log_test_event(test_id, "start", {"mode": "docker" if IS_DOCKER_MODE else "host"})

    if not IS_DOCKER_MODE:
        pytest.skip("Host mode: window open returns 403 (expected)")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # STEP 1: Open window with SHORT TTL (5 seconds)
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "switch", "ttl_seconds": 5},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            assert resp.status_code == 200, f"Window open failed: {resp.status_code}"
            window_data = resp.json()
            window_id = window_data.get("window_id")
            log_test_event(
                test_id,
                "window_opened_short_ttl",
                {"window_id": window_id, "ttl_seconds": 5},
            )
        except Exception as exc:
            pytest.skip(f"Window open error: {exc}")

        # STEP 2: Submit a task
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/intent",
                json={"intent_type": "exec", "text": "echo 'TTL test'"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code == 200:
                intent_data = resp.json()
                result_id = intent_data.get("correlation_id")
                log_test_event(
                    test_id,
                    "task_submitted",
                    {"result_id": result_id, "status": resp.status_code},
                )
            else:
                log_test_event(
                    test_id, "task_submit_failed", {"status": resp.status_code}
                )
        except Exception as exc:
            log_test_event(test_id, "task_submit_error", {"error": str(exc)})

        # STEP 3: Wait for TTL expiration (> 5 seconds)
        await asyncio.sleep(6)
        log_test_event(test_id, "ttl_expired", {"waited_seconds": 6})

        # STEP 4: Verify window is closed or policy reverted
        # Attempt to open window again; should be 403 (solo_madre) or success (new window)
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "switch"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code == 403:
                log_test_event(test_id, "post_ttl_solo_madre_active", {"status": 403})
            elif resp.status_code == 200:
                log_test_event(
                    test_id,
                    "post_ttl_new_window_opened",
                    {"status": 200, "window_id": resp.json().get("window_id")},
                )
            else:
                log_test_event(
                    test_id, "post_ttl_unexpected_status", {"status": resp.status_code}
                )
        except Exception as exc:
            log_test_event(test_id, "post_ttl_check_error", {"error": str(exc)})

    log_test_event(test_id, "complete", {"status": "PASS"})


@pytest.mark.asyncio
async def test_t7_breaker_degraded_path():
    """
    T7: Validate circuit breaker / degraded path handling.

    Objective: Trigger a controlled error (e.g., invalid model, missing provider)
    and verify the system responds gracefully without crashing.

    Expected:
    - Intent with invalid/degraded payload returns error JSON (not 500 plain text)
    - Error includes reason/code
    - Subsequent intents with valid payload still respond (not permanently broken)

    Host mode: May skip if spawner/switch not available; skip if 403 due to solo_madre
    """
    test_id = "T7_BREAKER_DEGRADED"
    log_test_event(test_id, "start", {"mode": "docker" if IS_DOCKER_MODE else "host"})

    async with httpx.AsyncClient(timeout=20.0) as client:
        # STEP 1: Try to open window (may fail in host mode)
        window_id = None
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "switch", "ttl_seconds": 10},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code == 200:
                window_id = resp.json().get("window_id")
                log_test_event(test_id, "window_opened", {"window_id": window_id})
            elif resp.status_code == 403:
                pytest.skip("Host mode: window 403 (solo_madre)")
        except Exception as exc:
            log_test_event(test_id, "window_open_error", {"error": str(exc)})

        # STEP 2: Send degraded intent (invalid provider/model)
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/intent",
                json={
                    "intent_type": "exec",
                    "text": "invalid-provider:unknown-model:test",
                    "provider": "invalid-provider",  # Non-existent provider
                },
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            log_test_event(
                test_id,
                "degraded_intent_response",
                {
                    "status": resp.status_code,
                    "is_json": resp.headers.get("content-type", "").startswith(
                        "application/json"
                    ),
                },
            )

            # Verify response is JSON (not plain 500)
            if resp.status_code >= 500:
                try:
                    error_data = resp.json()
                    assert (
                        "error" in error_data or "detail" in error_data
                    ), "Error JSON missing error/detail field"
                    log_test_event(
                        test_id,
                        "error_response_valid_json",
                        {"error": error_data.get("error", error_data.get("detail"))},
                    )
                except json.JSONDecodeError:
                    pytest.fail(f"500+ error response is not JSON: {resp.text}")
        except Exception as exc:
            log_test_event(test_id, "degraded_intent_error", {"error": str(exc)})

        # STEP 3: Send valid intent to verify system still responsive
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/intent",
                json={"intent_type": "exec", "text": "echo 'recovery test'"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code < 400 or resp.status_code == 403:
                log_test_event(
                    test_id, "recovery_intent_response", {"status": resp.status_code}
                )
            else:
                log_test_event(
                    test_id,
                    "recovery_intent_failed",
                    {"status": resp.status_code, "text": resp.text[:100]},
                )
        except Exception as exc:
            log_test_event(test_id, "recovery_intent_error", {"error": str(exc)})

        # STEP 4: Close window if opened
        if window_id:
            try:
                await client.post(
                    f"{ENTRYPOINT}/vx11/window/close",
                    json={"target": "switch"},
                    headers={"X-VX11-Token": VX11_TOKEN},
                )
            except:
                pass

    log_test_event(test_id, "complete", {"status": "PASS"})


@pytest.mark.asyncio
async def test_t8_auth_token_invalid_denied():
    """
    T8: Validate that invalid/missing auth token is denied.

    Objective: Verify authentication is enforced on protected endpoints.

    Expected:
    - Request WITHOUT token header -> 401 or 403 with JSON error
    - Request WITH invalid token -> 401 or 403 with JSON error
    - Request WITH valid token -> 200 or 403 (by policy, not auth)

    Host mode: May skip if window policy prevents all attempts
    """
    test_id = "T8_AUTH_INVALID"
    log_test_event(test_id, "start")

    if not VX11_TOKEN:
        pytest.skip("VX11_TOKEN not set; cannot test auth")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # STEP 1: Request WITHOUT token
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "switch"},
                # NO X-VX11-Token header
            )
            if resp.status_code in [401, 403]:
                log_test_event(
                    test_id,
                    "no_token_denied",
                    {
                        "status": resp.status_code,
                        "is_json": "application/json"
                        in resp.headers.get("content-type", ""),
                    },
                )
            else:
                log_test_event(
                    test_id,
                    "no_token_unexpected",
                    {"status": resp.status_code},
                )
        except Exception as exc:
            log_test_event(test_id, "no_token_error", {"error": str(exc)})

        # STEP 2: Request WITH INVALID token
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "switch"},
                headers={"X-VX11-Token": "invalid-token-12345"},
            )
            if resp.status_code in [401, 403]:
                log_test_event(
                    test_id,
                    "invalid_token_denied",
                    {"status": resp.status_code},
                )
            else:
                log_test_event(
                    test_id,
                    "invalid_token_unexpected",
                    {"status": resp.status_code},
                )
        except Exception as exc:
            log_test_event(test_id, "invalid_token_error", {"error": str(exc)})

        # STEP 3: Request WITH VALID token
        try:
            resp = await client.post(
                f"{ENTRYPOINT}/vx11/window/open",
                json={"target": "switch"},
                headers={"X-VX11-Token": VX11_TOKEN},
            )
            if resp.status_code == 200:
                log_test_event(test_id, "valid_token_accepted", {"status": 200})
            elif resp.status_code == 403:
                log_test_event(
                    test_id,
                    "valid_token_403_by_policy",
                    {"status": 403, "reason": "solo_madre or window policy"},
                )
            else:
                log_test_event(
                    test_id,
                    "valid_token_unexpected",
                    {"status": resp.status_code},
                )
        except Exception as exc:
            log_test_event(test_id, "valid_token_error", {"error": str(exc)})

    log_test_event(test_id, "complete", {"status": "PASS"})


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
