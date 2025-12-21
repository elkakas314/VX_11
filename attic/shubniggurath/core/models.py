from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class AudioAnalysis:
    duration: float = 0.0
    sample_rate: int = 44100
    channels: int = 1
    peak_dbfs: float = 0.0
    rms_dbfs: float = -60.0
    dynamic_range: float = 0.0
    issues: List[Any] = field(default_factory=list)


@dataclass
class FXChain:
    chain: List[Any] = field(default_factory=list)


@dataclass
class REAPERPreset:
    name: str = "default"
    content: dict = field(default_factory=dict)
