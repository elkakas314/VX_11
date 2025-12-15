"""Minimal operator package marker (safe).

This file exists so the repository can provide `operator.backend` as a
local subpackage for tests. It intentionally does not override stdlib
`operator` functions; instead, it imports ALL stdlib `operator` symbols
and re-exports them so that third-party libraries succeed.

Purpose: Avoid import shadowing of stdlib `operator` module.
"""

__all__ = ["backend"]

# Copy ALL symbols from stdlib `operator` to this namespace
try:
    import sys
    import operator as _stdlib_operator

    # Copy all non-private attributes from stdlib operator
    for _attr in dir(_stdlib_operator):
        if not _attr.startswith("_"):
            globals()[_attr] = getattr(_stdlib_operator, _attr)

    # Ensure critical symbols are definitely available
    from operator import (
        eq,
        ne,
        lt,
        le,
        gt,
        ge,
        add,
        sub,
        mul,
        truediv,
        floordiv,
        mod,
        pow,
        abs as _abs,
        neg,
        pos,
        itemgetter,
        attrgetter,
        methodcaller,
        index,
        length_hint,
        countOf,
        delitem,
        getitem,
        setitem,
        and_,
        or_,
        xor,
        not_,
        concat,
        contains,
        is_,
        is_not,
    )

except ImportError as e:
    # Fallback: provide minimal stubs (shouldn't reach here)
    def eq(a, b):
        return a == b

    def itemgetter(*items):
        class IG:
            def __init__(self, *items):
                self.items = items

            def __call__(self, obj):
                if len(self.items) == 1:
                    return obj[self.items[0]]
                return tuple(obj[i] for i in self.items)

        return IG(*items)

    def methodcaller(name, *args, **kwargs):
        class MC:
            def __call__(self, obj):
                return getattr(obj, name)(*args, **kwargs)

        return MC()
