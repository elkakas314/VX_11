"""
Test: No-Bypass Verification (Static Analysis)

Ensures that operator_backend/frontend/src/ contains ZERO hardcoded internal ports.
"""

import subprocess
import pytest


def test_no_bypass_frontend_src():
    """
    Verify that frontend/src has zero hardcoded internal ports (:8011, :8001, :8002).

    This is a STATIC analysis test; it should fail in CI if any bypass port is found.
    """
    # Bypass ports to detect
    bypass_patterns = [
        r"localhost:8011",
        r"127\.0\.0\.1:8011",
        r"localhost:8001",
        r"127\.0\.0\.1:8001",
        r"localhost:8002",
        r"127\.0\.0\.1:8002",
        r"http://madre:8001",
        r"http://switch:8002",
    ]

    for pattern in bypass_patterns:
        result = subprocess.run(
            [
                "grep",
                "-r",
                "-E",
                pattern,
                "operator_backend/frontend/src",
            ],
            capture_output=True,
            text=True,
        )

        if result.stdout:
            # Matches found = FAIL
            pytest.fail(
                f"❌ BYPASS DETECTED: Pattern '{pattern}' found in frontend/src:\n{result.stdout}"
            )

    print("✅ No-bypass verification PASSED (zero internal ports in frontend/src)")


def test_no_bypass_backend_hardcoded():
    """
    Verify that operator_backend/backend has zero hardcoded direct calls to madre:8001, switch:8002.

    Note: madre_url = os.getenv(..., "http://madre:8001") is OK (env default).
    But direct http:// calls (not via tentaculo_link) are NOT allowed.
    """
    # This test is more lenient: we just check for direct hardcoded http calls
    patterns_forbidden = [
        r"http://madre:8001",  # Should not be called directly from backend
        r"http://switch:8002",
        r"http://spawner:8008",
    ]

    for pattern in patterns_forbidden:
        result = subprocess.run(
            [
                "grep",
                "-r",
                "-E",
                pattern,
                "operator_backend/backend",
            ],
            capture_output=True,
            text=True,
        )

        # Filter: allow in env defaults (e.g., "os.getenv(..., "http://madre:8001")")
        # but forbid in actual function calls like "httpx.get(madre_url)"
        lines = result.stdout.split("\n") if result.stdout else []
        forbidden_lines = [
            l
            for l in lines
            if l and "os.getenv" not in l and "default" not in l.lower()
        ]

        if forbidden_lines:
            pytest.fail(
                f"❌ DIRECT CALL DETECTED: Pattern '{pattern}' in backend code:\n"
                + "\n".join(forbidden_lines)
            )

    print(
        "✅ Backend no-bypass verification PASSED (zero direct calls to internal services)"
    )


if __name__ == "__main__":
    test_no_bypass_frontend_src()
    test_no_bypass_backend_hardcoded()
    print("\n✅ ALL NO-BYPASS TESTS PASSED")
