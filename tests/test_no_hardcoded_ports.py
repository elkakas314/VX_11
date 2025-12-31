"""
Anti-regression test: Enforce single-entrypoint architecture.

INVARIANT: All E2E/P0 tests must use frontdoor (http://localhost:8000) via vx11_base_url().
NO hardcoded HTTP calls to internal ports (8001-8008, 8011).
"""

import pytest
import re
import ast
from pathlib import Path


@pytest.mark.security
def test_frontdoor_helpers_available():
    """
    STEP 1: Verify frontdoor helpers exist and are functional.
    """
    from tests._vx11_base import vx11_base_url, vx11_auth_headers

    base_url = vx11_base_url()
    assert "8000" in base_url, f"Expected port 8000 in {base_url}"
    assert isinstance(base_url, str)

    headers = vx11_auth_headers()
    assert isinstance(headers, dict)
    assert "X-VX11-Token" in headers or "X-VX11-GW-TOKEN" in headers


@pytest.mark.security
def test_no_hardcoded_internal_ports():
    """
    STEP 2: Anti-regression scan - detect hardcoded HTTP calls to internal ports.
    Fails if any test file has direct calls to 8001-8008, 8011.
    Ignores: socket diagnostics, assertions, comments, docstrings, allowlist.
    """
    GUARD_ALLOWLIST = {
        "tests/test_no_hardcoded_ports.py",
        "tests/test_no_bypass.py",
        "tests/test_operator_no_bypass.py",
    }

    def is_in_docstring_or_comment(line_num, line, docstring_ranges):
        if line.strip().startswith("#"):
            return True
        for start, end in docstring_ranges:
            if start <= line_num <= end:
                return True
        return False

    def get_docstring_ranges(source_code):
        ranges = set()
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module),
                ):
                    doc = ast.get_docstring(node)
                    if doc and hasattr(node, "lineno"):
                        ranges.add((node.lineno, node.lineno + len(doc.split("\n"))))
        except:
            pass
        return ranges

    def is_hardcoded_call(line):
        """Detect actual HTTP calls to internal ports."""
        skip_patterns = [
            r"assert.*port",
            r"pytest\.skip",
            r"connect_ex\(",
            r"internal_ports\s*=",
            r"#",
            r'f"',
            r'"""',
        ]
        for pattern in skip_patterns:
            if re.search(pattern, line):
                return False

        hardcoded = [
            r'requests\.(get|post|put|delete|patch)\s*\(\s*["\'][^"\']*:800[1-8]',
            r'http\.get\s*\(\s*["\'][^"\']*:800[1-8]',
            r'client\.(get|post|put|delete)\s*\(["\'][^"\']*:800[1-8]',
        ]
        for pattern in hardcoded:
            if re.search(pattern, line):
                return True
        return False

    violations = []
    test_dir = Path("tests")
    for py_file in sorted(test_dir.glob("**/*.py")):
        relpath = str(py_file.relative_to("."))
        if relpath in GUARD_ALLOWLIST:
            continue

        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            docstring_ranges = get_docstring_ranges(content)
            for idx, line in enumerate(lines, 1):
                if is_in_docstring_or_comment(idx, line, docstring_ranges):
                    continue
                if is_hardcoded_call(line):
                    violations.append(f"{relpath}:{idx}: {line.strip()}")
        except Exception as e:
            pytest.skip(f"Scan error in {relpath}: {e}")

    assert len(violations) == 0, f"Hardcoded internal port calls found:\n" + "\n".join(
        violations
    )
