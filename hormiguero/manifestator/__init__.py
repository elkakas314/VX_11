"""
VX11 Manifestator Integration
hormiguero/manifestator/__init__.py

Module: manifestator (drift validation, patchplan generation, builder spec planning)
Role: Planning-only; NO execution; generates non-executable patchplans + builder specs
Integration: Hormiguero fs_drift detection → Manifestator patchplan + builder_spec

Endpoints exposed via tentáculo_link/routes/rails.py:
- GET /api/rails/lanes: List drift detection stages + validation lanes
- GET /api/rails: List all constraints/rules (manifestator_rails table)
- GET /api/rails/{lane_id}/status: Detailed lane status + findings
"""

__version__ = "7.2.0"
__module_name__ = "manifestator"

from .controller import RailsController, DriftEvidence

__all__ = [
    "RailsController",
    "DriftEvidence",
]
