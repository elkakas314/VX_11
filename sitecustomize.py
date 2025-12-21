import os, sys

def _remove_all(p):
    while p in sys.path:
        try: sys.path.remove(p)
        except ValueError: break

def _append_once(p):
    _remove_all(p)
    sys.path.append(p)

def _norm(p):
    try: return os.path.abspath(p)
    except Exception: return p

# mover cwd y variantes al final
try:
    cwd = os.getcwd()
except Exception:
    cwd = ""

for p in ("", ".", cwd, _norm(cwd)):
    if p in sys.path:
        _append_once(p)

# mover repo root (donde vive este archivo) al final
repo_root = _norm(os.path.dirname(__file__))
if repo_root in sys.path:
    _append_once(repo_root)
