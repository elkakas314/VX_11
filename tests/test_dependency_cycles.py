import ast
from pathlib import Path

import pytest


ROOTS = [
    "madre",
    "tentaculo_link",
    "switch",
    "spawner",
    "operator",
    "manifestator",
    "hormiguero",
    "mcp",
    "shubniggurath",
]


def _collect_imports(py_file: Path) -> set[str]:
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def _detect_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, stack: list[str]) -> None:
        if node in visiting:
            cycle_start = stack.index(node)
            cycles.append(stack[cycle_start:] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for neighbor in graph.get(node, set()):
            visit(neighbor, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node, [])
    return cycles


@pytest.mark.unit
def test_no_cross_module_cycles():
    """Detect cycles between top-level module roots."""
    repo_root = Path(__file__).resolve().parent.parent
    graph: dict[str, set[str]] = {root: set() for root in ROOTS}

    for root in ROOTS:
        for py_file in (repo_root / root).rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue
            imports = _collect_imports(py_file)
            for imported in imports:
                imported_root = imported.split(".", 1)[0]
                if imported_root in ROOTS and imported_root != root:
                    graph[root].add(imported_root)

    cycles = _detect_cycles(graph)
    assert not cycles, f"Cross-module cycles detected: {cycles}"
