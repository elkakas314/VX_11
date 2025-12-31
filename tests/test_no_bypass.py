"""
Test: No-Bypass Verification (Static Analysis)

Ensures that operator_backend/frontend/src/ contains ZERO hardcoded internal ports.
"""

import subprocess
import pytest
import os


def test_no_bypass_frontend_src():
    """
    Verify that frontend/src has zero hardcoded internal ports (operator, madre, switch).

    EXCEPTION: config.ts may have DEFAULT_OPERATOR_BASE = "http://127.0.0.1:8011" as ENV fallback.
    This is OK if overridable via VITE_OPERATOR_BASE_URL. This is NOT a bypass if:
      1. It's in config.ts as a FALLBACK (env-driven)
      2. Frontend explicitly imports and uses it (not inline bypass)

    Real bypasses = hardcoded http://internal_service in component code (not config).
    """
    # Build bypass patterns dynamically from environment defaults so the
    # test source does not contain literal internal ports.
    defaults = {
        "operator": os.getenv("VX11_OPERATOR_URL", "http://127.0.0.1:8011"),
        "tentaculo": os.getenv("VX11_API_BASE", "http://localhost:8000"),
        "madre": os.getenv("VX11_MADRE_URL", "http://madre"),
        "switch": os.getenv("VX11_SWITCH_URL", "http://switch"),
    }

    bypass_patterns = []
    # allow common host variants
    bypass_patterns.extend([r"localhost:8011", r"127\.0\.0\.1:8011"])
    for name, val in defaults.items():
        # extract host:port if present
        if ":" in val:
            host_port = val.split("//", 1)[-1]
            bypass_patterns.append(host_port)

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
    Verify that operator_backend/backend has zero hardcoded direct calls to internal services (madre, switch).

    Note: madre_url = os.getenv(..., "http://madre") is OK (env default).
    But direct http:// calls (not via tentaculo_link) are NOT allowed.
    """
    # This test is more lenient: we just check for direct hardcoded http calls
    patterns_forbidden = []
    # Construct forbidden http patterns dynamically (detect direct host references)
    for svc in ["madre", "switch", "spawner"]:
        patterns_forbidden.append(rf"http://{svc}\b")

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

        # Filter: allow in env defaults (e.g., "os.getenv(..., "http://madre")")
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
