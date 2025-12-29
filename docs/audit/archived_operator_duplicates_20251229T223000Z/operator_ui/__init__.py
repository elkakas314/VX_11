"""Operator package shim: lightweight stdlib helpers + package marker.

Provide a minimal set of functions (eq, lt, gt, itemgetter, attrgetter,
methodcaller) that the stdlib imports (e.g., `collections`) expect, while
avoiding heavy imports. This allows the repository `operator` package to
coexist with stdlib usage during test startup.
"""


def eq(a, b):
    return a == b


def lt(a, b):
    return a < b


def gt(a, b):
    return a > b


def itemgetter(*items):
    if len(items) == 1:
        idx = items[0]
        return lambda obj: obj[idx]

    def _multi(obj):
        return tuple(obj[i] for i in items)

    return _multi


def attrgetter(*attrs):
    if len(attrs) == 1:
        name = attrs[0]
        return lambda obj: getattr(obj, name)

    def _multi(obj):
        return tuple(getattr(obj, a) for a in attrs)

    return _multi


def methodcaller(name, *args, **kwargs):
    return lambda obj: getattr(obj, name)(*args, **kwargs)


# Minimal __all__ (do not import backend here)
__all__ = [
    "eq",
    "lt",
    "gt",
    "itemgetter",
    "attrgetter",
    "methodcaller",
]

# Attempt to alias operator.backend -> operator_backend.backend for tests that
# patch "operator.backend.browser.async_playwright". Doing this here (in the
# lightweight package init) avoids circular imports and ensures the alias is
# present when tests run.
try:
    import importlib
    import sys

    _ob = importlib.import_module("operator_backend.backend")
    # Register in sys.modules under the dotted name
    sys.modules.setdefault("operator.backend", _ob)
    # Expose as attribute
    globals()["backend"] = _ob
except Exception:
    pass
