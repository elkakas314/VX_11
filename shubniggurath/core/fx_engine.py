"""
FXEngine: Generación automática de cadenas de efectos basadas en análisis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import json


@dataclass
class FXPlugin:
    """Representa un plugin de efectos."""
    plugin_type: str  # eq, compressor, reverb, deesser, limiter
    manufacturer: str
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    bypass: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_type": self.plugin_type,
            "manufacturer": self.manufacturer,
            "name": self.name,
            "parameters": self.parameters,
            "bypass": self.bypass
        }


@dataclass
class FXChain:
    """Cadena de efectos completa."""
    name: str
    description: str
    plugins: List[FXPlugin] = field(default_factory=list)
    routing: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "plugins": [p.to_dict() for p in self.plugins],
            "routing": self.routing
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class FXEngine:
    """Motor de generación de cadenas de efectos."""

    def __init__(self):
        self.style_templates = self._load_style_templates()

    def _load_style_templates(self) -> Dict[str, Any]:
        """Plantillas de estilo musical."""
        return {
            "modern_pop": {
                "target_lufs": -14.0,
                "target_true_peak": -1.0,
                "spectral_balance": {"low": 0.3, "mid": 0.4, "high": 0.3},
                "dynamic_range": 8.0
            },
            "rock": {
                "target_lufs": -12.0,
                "target_true_peak": -1.0,
                "spectral_balance": {"low": 0.4, "mid": 0.4, "high": 0.2},
                "dynamic_range": 10.0
            },
            "electronic": {
                "target_lufs": -8.0,
                "target_true_peak": -1.0,
                "spectral_balance": {"low": 0.5, "mid": 0.3, "high": 0.2},
                "dynamic_range": 6.0
            },
            "acoustic": {
                "target_lufs": -16.0,
                "target_true_peak": -1.0,
                "spectral_balance": {"low": 0.3, "mid": 0.5, "high": 0.2},
                "dynamic_range": 12.0
            }
        }

    def generate_fx_chain(self, analysis: Dict[str, Any],
                         target_style: str = "modern_pop") -> FXChain:
        """
        Generar cadena de efectos basada en análisis.
        
        Args:
            analysis: resultado de AnalyzerEngine.analyze_audio() como dict
            target_style: rock, pop, electronic, acoustic
        
        Returns:
            FXChain con plugins configurados
        """
        style_template = self.style_templates.get(target_style, 
                                                   self.style_templates["modern_pop"])

        plugins = []

        # 1. EQ basado en espectral
        eq_plugin = self._generate_eq_plugin(analysis, style_template)
        if eq_plugin:
            plugins.append(eq_plugin)

        # 2. Compresor basado en dinámica
        comp_plugin = self._generate_compressor_plugin(analysis, style_template)
        if comp_plugin:
            plugins.append(comp_plugin)

        # 3. Plugins de reparación (si hay issues)
        repair_plugins = self._generate_repair_plugins(analysis)
        plugins.extend(repair_plugins)

        # 4. Master limiter (siempre)
        limiter = FXPlugin(
            plugin_type="limiter",
            manufacturer="Shub-DSP",
            name="Shub Master Limiter",
            parameters={
                "threshold": -1.0,
                "release": 50.0
            }
        )
        plugins.append(limiter)

        chain_name = f"{target_style}_chain"
        chain_desc = f"Cadena automática para {target_style}"

        return FXChain(
            name=chain_name,
            description=chain_desc,
            plugins=plugins,
            routing={"parallel": False, "sidechain": []}
        )

    def _generate_eq_plugin(self, analysis: Dict[str, Any],
                           style_template: Dict[str, Any]) -> Optional[FXPlugin]:
        """Generar plugin EQ."""
        spectral_centroid = analysis.get('spectral_centroid', 1000)

        bands = [
            {
                "type": "low_shelf",
                "frequency": 100,
                "gain": 0.0,
                "q": 0.7
            },
            {
                "type": "peaking",
                "frequency": 1000,
                "gain": 0.0,
                "q": 1.0
            },
            {
                "type": "high_shelf",
                "frequency": 5000,
                "gain": 0.0,
                "q": 0.7
            }
        ]

        return FXPlugin(
            plugin_type="eq",
            manufacturer="Shub-DSP",
            name="Shub Matching EQ",
            parameters={"bands": bands}
        )

    def _generate_compressor_plugin(self, analysis: Dict[str, Any],
                                   style_template: Dict[str, Any]) -> Optional[FXPlugin]:
        """Generar plugin compresor."""
        dynamic_range = analysis.get('dynamic_range', 10.0)
        target_dynamic = style_template.get('dynamic_range', 8.0)
        compression_needed = max(0, dynamic_range - target_dynamic)

        if compression_needed > 2.0:
            return FXPlugin(
                plugin_type="compressor",
                manufacturer="Shub-DSP",
                name="Shub Dynamics",
                parameters={
                    "threshold": -20.0,
                    "ratio": 2.0 + (compression_needed / 10),
                    "attack": 10.0,
                    "release": 100.0,
                    "makeup": 0.0
                }
            )
        return None

    def _generate_repair_plugins(self, analysis: Dict[str, Any]) -> List[FXPlugin]:
        """Generar plugins de reparación basados en issues."""
        plugins = []
        issues = analysis.get('issues', [])

        for issue in issues:
            if issue.get('type') == 'sibilance':
                plugins.append(FXPlugin(
                    plugin_type="deesser",
                    manufacturer="Shub-DSP",
                    name="Shub Deesser",
                    parameters={
                        "frequency": analysis.get('sibilance_freq', 7000),
                        "threshold": -30.0,
                        "reduction": -6.0
                    }
                ))
            elif issue.get('type') == 'dc_offset':
                plugins.append(FXPlugin(
                    plugin_type="dc_remover",
                    manufacturer="Shub-DSP",
                    name="Shub DC Remover",
                    parameters={"frequency": 20.0}
                ))

        return plugins
