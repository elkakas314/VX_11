"""
P0 Test: Operator frontend CANNOT call internal ports directly
Validates single entrypoint + no-bypass invariant
"""

import re
import os


def test_no_hardcoded_ports():
    """Grep frontend source for hardcoded internal ports in fetch/http calls (NOT comments/data)"""
    frontend_dir = "operator/frontend/src"
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
                    for port in internal_ports:
                        pattern_fetch = (
                            rf"fetch\s*\(\s*['\"`].*(?:localhost|127\.0\.0\.1):{port}\b"
                        )
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


def test_api_base_is_env_driven():
    """Verify api.ts uses VITE_API_BASE or relative base (no localhost hardcode)."""
    config_file = "operator/frontend/src/services/api.ts"

    with open(config_file, "r") as f:
        content = f.read()

    assert "VITE_API_BASE" in content, "api.ts must reference VITE_API_BASE"
    assert "localhost:8000" not in content, "api.ts must not hardcode localhost:8000"

    print(f"✅ {config_file} uses env-driven API base")


if __name__ == "__main__":
    test_no_hardcoded_ports()
    test_api_base_is_env_driven()
    print("✅ All P0 no-bypass tests PASSED")
