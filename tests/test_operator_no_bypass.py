"""
P0 Test: Operator frontend CANNOT call internal ports directly
Validates single entrypoint + no-bypass invariant
"""

import re
import os


def test_no_hardcoded_ports():
    """Grep frontend source for hardcoded internal ports in fetch/http calls (NOT comments/data)"""
    frontend_dir = "operator_backend/frontend/src"
    internal_ports = ["8001", "8002", "8003", "8011"]

    found_violations = []

    for root, dirs, files in os.walk(frontend_dir):
        # Skip node_modules, dist
        if "node_modules" in root or "dist" in root:
            continue

        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()
                    # Look for fetch/http patterns with internal ports
                    # Patterns: fetch("http://localhost:PORT"), fetch(`...${PORT}...`), url: "...PORT"
                    for port in internal_ports:
                        # Match fetch calls with explicit localhost/127.0.0.1:PORT
                        pattern_fetch = (
                            rf"fetch\s*\(\s*['\"`].*(?:localhost|127\.0\.0\.1):{port}\b"
                        )
                        # Match axios/http calls
                        pattern_http = rf"(?:http|axios)\s*\.(?:get|post|put|delete)\s*\(\s*['\"`].*:{port}\b"

                        if re.search(pattern_fetch, content) or re.search(
                            pattern_http, content
                        ):
                            found_violations.append(
                                f"{filepath}: port {port} in fetch/http call"
                            )

    assert (
        not found_violations
    ), f"Bypass violations found (fetch/http calls):\n" + "\n".join(found_violations)
    print(f"✅ No hardcoded internal ports in fetch/http calls in {frontend_dir}")


def test_config_uses_entrypoint():
    """Verify config.ts uses OPERATOR_BASE_URL = http://127.0.0.1:8000"""
    config_file = "operator_backend/frontend/src/config.ts"

    with open(config_file, "r") as f:
        content = f.read()

    # Check for OPERATOR_BASE_URL definition
    assert "OPERATOR_BASE_URL" in content, "config.ts must define OPERATOR_BASE_URL"
    assert (
        "127.0.0.1:8000" in content
        or "http://localhost:8000" in content
        or "tentaculo_link:8000" in content
    ), "OPERATOR_BASE_URL must default to entrypoint (8000)"

    print(f"✅ {config_file} correctly uses entrypoint")


if __name__ == "__main__":
    test_no_hardcoded_ports()
    test_config_uses_entrypoint()
    print("✅ All P0 no-bypass tests PASSED")
