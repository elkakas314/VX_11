import ast
import re
from pathlib import Path

import pytest

BAD_PORTS = {8011, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008}
ALLOWLIST = {
    "tests/test_no_hardcoded_ports.py",
    "tests/test_no_bypass.py",
    "tests/test_operator_no_bypass.py",
}

HTTP_CALL_NAMES = [
    # common clients
    ("requests", {"get", "post", "put", "delete", "patch"}),
    ("httpx", {"get", "post", "put", "delete", "patch"}),
]

CLIENT_METHODS = {"get", "post", "put", "delete", "patch"}

URL_PORT_RE = re.compile(r"https?://[^\"']*:(800[1-8]|8011)\b", re.IGNORECASE)


@pytest.mark.security
def test_frontdoor_helpers_available():
    from tests._vx11_base import vx11_base_url, vx11_auth_headers

    base = vx11_base_url()
    assert isinstance(base, str) and base
    assert "8000" in base or "localhost" in base

    hdr = vx11_auth_headers()
    assert isinstance(hdr, dict) and hdr
    assert ("X-VX11-Token" in hdr) or ("X-VX11-GW-TOKEN" in hdr)


def _extract_violations_from_ast(src: str, relpath: str):
    """
    Detect hardcoded internal ports ONLY in real HTTP call sites (AST-based).
    Avoid false positives from comments/docstrings because they don't produce Call nodes.
    """
    violations = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        violations.append((relpath, 0, f"SyntaxError parsing file: {e}"))
        return violations

    def str_contains_bad_port(s: str) -> bool:
        if not s:
            return False
        m = URL_PORT_RE.search(s)
        return bool(m)

    def node_contains_bad_port(node) -> bool:
        # strings like "http://localhost:8001/..."
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return str_contains_bad_port(node.value)
        # f-strings
        if isinstance(node, ast.JoinedStr):
            txt = ""
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    txt += v.value
            return str_contains_bad_port(txt)
        # integers like 8001 passed around
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value in BAD_PORTS
        # recursive
        for child in ast.iter_child_nodes(node):
            if node_contains_bad_port(child):
                return True
        return False

    def call_is_http_client(call: ast.Call) -> bool:
        # requests.get(...)
        if isinstance(call.func, ast.Attribute) and isinstance(
            call.func.value, ast.Name
        ):
            base = call.func.value.id
            meth = call.func.attr
            for client, methods in HTTP_CALL_NAMES:
                if base == client and meth in methods:
                    return True
        # client.get(...) (generic)
        if isinstance(call.func, ast.Attribute) and call.func.attr in CLIENT_METHODS:
            # allow socket diagnostics: sock.connect_ex(("localhost", 8001))
            if call.func.attr == "connect_ex":
                return False
            return True
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and call_is_http_client(node):
            # Skip known non-HTTP diagnostics patterns
            if isinstance(node.func, ast.Attribute) and node.func.attr == "connect_ex":
                continue
            # If any arg/kw contains a bad port in URL or as int, flag.
            bad = False
            for a in node.args:
                if node_contains_bad_port(a):
                    bad = True
                    break
            if not bad:
                for kw in node.keywords or []:
                    if kw.value and node_contains_bad_port(kw.value):
                        bad = True
                        break
            if bad:
                lineno = getattr(node, "lineno", 0)
                violations.append(
                    (relpath, lineno, "Hardcoded internal port in HTTP call")
                )
    return violations


@pytest.mark.security
def test_no_hardcoded_internal_ports():
    root = Path("tests")
    violations = []

    for p in root.rglob("*.py"):
        rel = p.as_posix()
        if rel in ALLOWLIST:
            continue
        src = p.read_text(encoding="utf-8", errors="replace")
        violations.extend(_extract_violations_from_ast(src, rel))

    if violations:
        lines = ["Hardcoded internal port calls found (must use frontdoor :8000):"]
        for f, ln, msg in violations[:50]:
            lines.append(f"- {f}:{ln}: {msg}")
        raise AssertionError("\n".join(lines))
