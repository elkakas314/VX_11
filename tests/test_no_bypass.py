"""
Test: No-Bypass Verification (Static Analysis)

Ensures that operator_backend/frontend/src/ contains ZERO hardcoded internal ports.
"""

import subprocess
import pytest


def test_no_bypass_frontend_src():
    """
    Verify that frontend/src has zero hardcoded internal ports (:8011, :8001, :8002).

    EXCEPTION: config.ts may have DEFAULT_OPERATOR_BASE = "http://127.0.0.1:8011" as ENV fallback.
    This is OK if overridable via VITE_OPERATOR_BASE_URL. This is NOT a bypass if:
      1. It's in config.ts as a FALLBACK (env-driven)
      2. Frontend explicitly imports and uses it (not inline bypass)

    Real bypasses = hardcoded http://internal_service in component code (not config).
    """
    # Bypass ports to detect (in component code, not config.ts)
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

    # Exclude config.ts (allowed to have env-driven fallback)
    exclude_files = ["config.ts"]

    for pattern in bypass_patterns:
        result = subprocess.run(
            [
                "grep",
                "-r",
                "-E",
                pattern,
                "operator/frontend/src",
                "--exclude=*.ts.bak",  # Exclude backups
            ],
            capture_output=True,
            text=True,
        )

        if result.stdout:
            # Filter out config.ts lines
            lines = [
                line
                for line in result.stdout.split("\n")
                if line and not any(exc in line for exc in exclude_files)
            ]
            if lines:
                pytest.fail(
                    f"❌ BYPASS DETECTED: Pattern '{pattern}' found in frontend/src (outside config.ts):\n"
                    + "\n".join(lines)
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
                "operator/backend",
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
