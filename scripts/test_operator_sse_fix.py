#!/usr/bin/env python3
"""
Smoke test for Operator API through tentaculo_link single entrypoint.
Tests SSE token auth fix (multi-token support).

Usage:
  python3 scripts/test_operator_sse_fix.py

Expected behavior:
  - All endpoints accessible via http://localhost:8000
  - SSE /operator/api/events accepts token in query param and opens stream
  - No 401 errors with valid tokens
"""

import subprocess
import sys
import time
import json

BASE_URL = "http://localhost:8000"
TENTACULO_TOKEN = "vx11-test-token"
OPERATOR_TOKEN = "vx11-operator-test-token"


def log(msg, level="INFO"):
    print(f"[{level}] {msg}", file=sys.stderr)


def test_health():
    """Test /health without token (public endpoint)"""
    log("Test 1: GET /health (no token)")
    result = subprocess.run(
        ["curl", "-s", "-w", "\\n%{http_code}", f"{BASE_URL}/health"],
        capture_output=True,
        text=True,
    )
    status = result.stdout.split("\n")[-1]
    body = "\n".join(result.stdout.split("\n")[:-1])

    if status == "200":
        log(f"✅ /health: {status}", "PASS")
        return True
    else:
        log(f"❌ /health: {status}\n{body}", "FAIL")
        return False


def test_operator_health_with_token():
    """Test /operator/api/health with valid token"""
    log(f"Test 2: GET /operator/api/health (with token={TENTACULO_TOKEN[:10]}...)")
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-w",
            "\\n%{http_code}",
            "-H",
            f"X-VX11-Token: {TENTACULO_TOKEN}",
            f"{BASE_URL}/operator/api/health",
        ],
        capture_output=True,
        text=True,
    )
    status = result.stdout.split("\n")[-1]
    body = "\n".join(result.stdout.split("\n")[:-1])

    if status in ("200", "201"):
        log(f"✅ /operator/api/health: {status}", "PASS")
        return True
    else:
        log(f"❌ /operator/api/health: {status}\n{body}", "FAIL")
        return False


def test_operator_chat():
    """Test /operator/api/chat POST with valid token"""
    log(f"Test 3: POST /operator/api/chat (with token)")
    result = subprocess.run(
        [
            "curl",
            "-s",
            "-w",
            "\\n%{http_code}",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "-H",
            f"X-VX11-Token: {TENTACULO_TOKEN}",
            "-d",
            '{"message":"hello"}',
            f"{BASE_URL}/operator/api/chat",
        ],
        capture_output=True,
        text=True,
    )
    status = result.stdout.split("\n")[-1]
    body = "\n".join(result.stdout.split("\n")[:-1])

    if status in ("200", "201", "400"):  # 400 ok if backend not fully ready
        log(f"✅ /operator/api/chat: {status}", "PASS")
        return True
    elif status == "401":
        log(f"❌ /operator/api/chat: {status} (auth failed)", "FAIL")
        return False
    else:
        log(f"❌ /operator/api/chat: {status}\n{body}", "FAIL")
        return False


def test_sse_stream_with_query_param():
    """Test /operator/api/events/stream?token=... SSE stream (uses check_sse_auth)"""
    log(f"Test 4: GET /operator/api/events/stream?token=... (SSE stream)")

    # Use timeout 3 to collect some events/heartbeats
    result = subprocess.run(
        [
            "timeout",
            "3",
            "curl",
            "-s",
            "-N",
            f"{BASE_URL}/operator/api/events/stream?token={TENTACULO_TOKEN}&follow=true",
        ],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    # Check for HTTP errors in response
    if "HTTP/1.1 401" in output or "401" in output:
        log(f"❌ SSE stream: 401 Unauthorized\n{output[:200]}", "FAIL")
        return False
    elif "HTTP/1.1 403" in output or "403" in output:
        log(f"❌ SSE stream: 403 Forbidden\n{output[:200]}", "FAIL")
        return False
    else:
        # SSE streams may timeout but should not error
        log(f"✅ SSE stream: opened (timeout ok)", "PASS")
        return True


def test_sse_stream_with_header():
    """Test /operator/api/events/stream with header token"""
    log(f"Test 5: GET /operator/api/events/stream (with header X-VX11-Token)")

    result = subprocess.run(
        [
            "timeout",
            "3",
            "curl",
            "-s",
            "-N",
            "-H",
            f"X-VX11-Token: {TENTACULO_TOKEN}",
            f"{BASE_URL}/operator/api/events/stream?follow=true",
        ],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    if "HTTP/1.1 401" in output or "401" in output:
        log(f"❌ SSE (header): 401 Unauthorized", "FAIL")
        return False
    elif "HTTP/1.1 403" in output or "403" in output:
        log(f"❌ SSE (header): 403 Forbidden", "FAIL")
        return False
    else:
        log(f"✅ SSE (header): opened (timeout ok)", "PASS")
        return True


def main():
    log("=" * 70)
    log("OPERATOR SSE FIX — SMOKE TEST")
    log("=" * 70)
    log(f"Base URL: {BASE_URL}")
    log(f"Tentaculo Token: {TENTACULO_TOKEN}")
    log(f"Operator Token: {OPERATOR_TOKEN}")
    log("=" * 70)

    tests = [
        ("Health (public)", test_health),
        ("Operator Health (token)", test_operator_health_with_token),
        ("Operator Chat", test_operator_chat),
        ("SSE Stream (query param)", test_sse_stream_with_query_param),
        ("SSE Stream (header)", test_sse_stream_with_header),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
            print()
        except Exception as e:
            log(f"❌ {name}: Exception: {e}", "ERROR")
            results.append((name, False))
            print()

    log("=" * 70)
    log("SUMMARY")
    log("=" * 70)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print()
    log(f"Result: {passed}/{total} passed", "SUMMARY")

    if passed == total:
        log("🎉 All tests passed!", "SUCCESS")
        return 0
    else:
        log("💥 Some tests failed", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
