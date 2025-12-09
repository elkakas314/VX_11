"""
Shub Pro: motor avanzado de procesamiento/mezcla para VX11 v6.3.

Este paquete vive dentro de VX11 y no altera la topología existente.
Se apoya en SQLite unificada `data/runtime/vx11.db` o en `SHUB_PRO_DB_URL`.
"""

__all__ = [
    "core",
    "audio_io",
    "dsp",
    "analysis",
    "mixing",
    "project_db",
    "pipeline",
    "exporter",
    "metadata_manager",
    "interface_api",
    "integration_switch",
    "studio_agent",
]
