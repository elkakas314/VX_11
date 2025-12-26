"""
VX11 — Main package init (for module resolution in IDEs and runtime).
Exposes subpackages: hormiguero, spawner, mcp, etc.
"""

import sys
import os
from pathlib import Path

# Ensure subpackages are discoverable
_vx11_root = Path(__file__).parent.absolute()
if str(_vx11_root) not in sys.path:
    sys.path.insert(0, str(_vx11_root))

# Re-export critical submodules for IDE/Pylance resolution
try:
    from hormiguero import core, config  # noqa: F401
    import hormiguero  # noqa: F401
except ImportError:
    pass

try:
    # Make hormiguero.inee available as inee for backwards compatibility
    from hormiguero import inee  # noqa: F401
except ImportError:
    pass

__version__ = "7.0.0"
__all__ = ["hormiguero", "inee"]
