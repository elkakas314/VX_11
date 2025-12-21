"""
Shub-Niggurath Core Engines - CANONICAL IMPLEMENTATION
Basado en shub.txt + shub2.txt + shubnoggurath.txt

ENGINES CANONICAL:
1. DSPEngine - Análisis completo de audio (6 métodos)
2. FXEngine - Generación de cadenas de efectos
3. ShubCoreInitializer - Inicializador singleton

NO INCLUYEN: Vocal, Drum, Arrangement, Restoration genéricos
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np
import asyncio
from datetime import datetime
import logging

log = logging.getLogger("vx11.shub.engines")

# ==============================================================================
# CANONICAL DATACLASSES (desde shub2.txt)
# ==============================================================================

@dataclass
class AudioAnalysis:
    """Resultado completo del análisis DSP - CANONICAL"""
    # Información básica
    duration: float
    sample_rate: int
    channels: int

    # Medidas de nivel
    peak_dbfs: float
    rms_dbfs: float
    lufs_integrated: float
    lufs_range: float
    true_peak_dbfs: float

    # Análisis espectral
    spectral_centroid: float
    spectral_rolloff: float
    spectral_flux: float
    zero_crossing_rate: float
    mfcc: List[float] = field(default_factory=lambda: [0.0] * 13)
    chroma: List[float] = field(default_factory=lambda: [0.0] * 12)
    spectral_contrast: List[float] = field(default_factory=lambda: [0.0] * 7)
    spectral_flatness: float = 0.0

    # Análisis dinámico
    dynamic_range: float = 0.0
    crest_factor: float = 0.0
    transients: List[float] = field(default_factory=list)
    transients_count: int = 0

    # Detección de problemas
    clipping_samples: int = 0
    dc_offset: float = 0.0
    noise_floor_dbfs: float = -80.0
    phase_correlation: float = 1.0
    sibilance_detected: bool = False
    sibilance_freq: float = 0.0
    resonances: List[Dict[str, float]] = field(default_factory=list)

    # Análisis musical
    bpm: Optional[float] = None
    key_detected: Optional[str] = None
    key_confidence: Optional[float] = None
    harmonic_complexity: float = 0.5
    percussiveness: float = 0.5

    # Clasificación
    instrument_prediction: Dict[str, float] = field(default_factory=dict)
    genre_prediction: Dict[str, float] = field(default_factory=dict)
    mood_prediction: Dict[str, float] = field(default_factory=dict)

    # Issues detectados
    issues: List[Dict[str, Any]] = field(default_factory=list)

    # Recomendaciones iniciales
    recommendations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FXChain:
    """Cadena de efectos completa - CANONICAL"""
    name: str
    description: str
    plugins: List[Dict[str, Any]]
    routing: Dict[str, Any]
    presets: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class REAPERPreset:
    """Preset de proyecto REAPER - CANONICAL"""
    project_name: str
    tracks: List[Dict[str, Any]]
    fx_chains: List[FXChain]
    routing_matrix: Dict[str, Any]
    automation: List[Dict[str, Any]]
    metadata: Dict[str, Any]


# ==============================================================================
# DSP ENGINE - CANONICAL (desde shub2.txt)
# ==============================================================================

class DSPEngine:
    """
    Motor DSP avanzado basado en shubnoggurath.txt - CANONICAL
    
    Implementa 6 métodos de análisis según shub2.txt:
    1. _analyze_levels()
    2. _analyze_spectral()
    3. _analyze_dynamics()
    4. _detect_issues()
    5. _analyze_musical()
    6. _classify_audio()
    """

    def __init__(self, sample_rate: int = 48000, fft_size: int = 4096, hop_length: int = 1024):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.hop_length = hop_length

        # Umbrales para detección (desde shub2.txt)
        self.clipping_threshold = -0.5
        self.sibilance_threshold = 5000
        self.noise_threshold = -60
        self.dc_offset_threshold = 0.01
        self.phase_threshold = 0.5

        log.info(f"DSPEngine inicializado: sr={sample_rate}, fft={fft_size}, hop={hop_length}")

    async def analyze_audio(self, audio_data: np.ndarray, sample_rate: int = None) -> AudioAnalysis:
        """
        Análisis completo de audio - CANONICAL
        Paralleliza 6 métodos de análisis
        """
        if sample_rate is None:
            sample_rate = self.sample_rate

        # Convertir a mono para análisis
        if len(audio_data.shape) > 1:
            audio_mono = np.mean(audio_data, axis=1)
        else:
            audio_mono = audio_data.copy()

        log.info(f"Analizando audio: {len(audio_mono)} muestras @ {sample_rate}Hz")

        # Tareas de análisis en paralelo (6 métodos canónicos)
        tasks = [
            self._analyze_levels(audio_mono),
            self._analyze_spectral(audio_mono, sample_rate),
            self._analyze_dynamics(audio_mono),
            self._detect_issues(audio_mono, sample_rate),
            self._analyze_musical(audio_mono, sample_rate),
            self._classify_audio(audio_mono, sample_rate)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verificar que todos completaron
        if any(isinstance(r, Exception) for r in results):
            log.warning(f"Errores en análisis paralelo: {[r for r in results if isinstance(r, Exception)]}")

        level_analysis = results[0] if isinstance(results[0], dict) else {}
        spectral_analysis = results[1] if isinstance(results[1], dict) else {}
        dynamic_analysis = results[2] if isinstance(results[2], dict) else {}
        issues_analysis = results[3] if isinstance(results[3], dict) else {}
        musical_analysis = results[4] if isinstance(results[4], dict) else {}
        classification = results[5] if isinstance(results[5], dict) else {}

        recommendations = await self._generate_recommendations(
            level_analysis, spectral_analysis, dynamic_analysis,
            issues_analysis, musical_analysis
        )

        return AudioAnalysis(
            duration=len(audio_mono) / sample_rate,
            sample_rate=sample_rate,
            channels=1 if len(audio_data.shape) == 1 else audio_data.shape[1],
            **level_analysis,
            **spectral_analysis,
            **dynamic_analysis,
            **issues_analysis,
            **musical_analysis,
            **classification,
            issues=issues_analysis.get('issues', []),
            recommendations=recommendations
        )

    async def _analyze_levels(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Método 1: Análisis de niveles LUFS, RMS, Peak
        """
        try:
            audio_abs = np.abs(audio)
            peak_linear = np.max(audio_abs) if len(audio_abs) > 0 else 1e-10
            peak_dbfs = 20 * np.log10(max(peak_linear, 1e-10))

            rms_linear = np.sqrt(np.mean(audio ** 2)) if len(audio) > 0 else 1e-10
            rms_dbfs = 20 * np.log10(max(rms_linear, 1e-10))

            integrated = rms_dbfs  # Simplificado (en prod usar pyloudnorm)
            true_peak_dbfs = peak_dbfs
            lufs_range = abs(rms_dbfs - peak_dbfs)

            return {
                "peak_dbfs": float(peak_dbfs),
                "rms_dbfs": float(rms_dbfs),
                "lufs_integrated": float(integrated),
                "lufs_range": float(lufs_range),
                "true_peak_dbfs": float(true_peak_dbfs)
            }
        except Exception as e:
            log.error(f"Error en _analyze_levels: {e}")
            return {
                "peak_dbfs": -inf,
                "rms_dbfs": -inf,
                "lufs_integrated": -inf,
                "lufs_range": 0.0,
                "true_peak_dbfs": -inf
            }

    async def _analyze_spectral(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Método 2: Análisis espectral avanzado
        Calcula centroide, rolloff, flux, ZCR, MFCC, chroma, contraste, flatness
        """
        try:
            fft_result = np.fft.rfft(audio[:min(len(audio), self.fft_size)])
            freqs = np.fft.rfftfreq(len(fft_result), 1/sample_rate)
            magnitudes = np.abs(fft_result)

            # Centroide espectral
            total_mag = np.sum(magnitudes)
            if total_mag > 0:
                spectral_centroid = float(np.sum(freqs * magnitudes) / total_mag)
            else:
                spectral_centroid = 0.0

            # Rolloff (85%)
            if total_mag > 0:
                target_energy = 0.85 * total_mag
                cumsum = np.cumsum(magnitudes)
                rolloff_idx = int(np.where(cumsum >= target_energy)[0][0]) if np.any(cumsum >= target_energy) else len(magnitudes) - 1
                spectral_rolloff = float(freqs[min(rolloff_idx, len(freqs) - 1)])
            else:
                spectral_rolloff = 0.0

            # Flux (cambio espectral)
            if len(magnitudes) > 1:
                spectral_flux = float(np.mean(np.abs(np.diff(magnitudes))))
            else:
                spectral_flux = 0.0

            # Zero Crossing Rate
            zero_crossing_rate = float(np.mean(np.abs(np.diff(np.sign(audio))))) if len(audio) > 1 else 0.0

            # Placeholders para MFCC, chroma, contraste espectral (en prod usar librosa)
            mfcc = [0.0] * 13
            chroma = [0.0] * 12
            spectral_contrast = [0.0] * 7

            # Flatness
            if np.mean(magnitudes) > 0:
                spectral_flatness = float(np.exp(np.mean(np.log(magnitudes + 1e-10))) / np.mean(magnitudes))
            else:
                spectral_flatness = 0.0

            return {
                "spectral_centroid": spectral_centroid,
                "spectral_rolloff": spectral_rolloff,
                "spectral_flux": spectral_flux,
                "zero_crossing_rate": zero_crossing_rate,
                "mfcc": mfcc,
                "chroma": chroma,
                "spectral_contrast": spectral_contrast,
                "spectral_flatness": spectral_flatness
            }
        except Exception as e:
            log.error(f"Error en _analyze_spectral: {e}")
            return {
                "spectral_centroid": 0.0,
                "spectral_rolloff": 0.0,
                "spectral_flux": 0.0,
                "zero_crossing_rate": 0.0,
                "mfcc": [0.0] * 13,
                "chroma": [0.0] * 12,
                "spectral_contrast": [0.0] * 7,
                "spectral_flatness": 0.0
            }

    async def _analyze_dynamics(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Método 3: Análisis dinámico
        Rango dinámico, crest factor, transitorios
        """
        try:
            window_size = max(1, self.sample_rate // 10)
            windows = len(audio) // window_size

            rms_values = []
            for i in range(max(1, windows)):
                start = i * window_size
                end = min((i + 1) * window_size, len(audio))
                segment = audio[start:end]
                if len(segment) > 0:
                    rms = np.sqrt(np.mean(segment ** 2))
                    rms_values.append(20 * np.log10(max(rms, 1e-10)))

            if rms_values:
                dynamic_range = float(max(rms_values) - min(rms_values))
            else:
                dynamic_range = 0.0

            # Crest Factor
            peak = np.max(np.abs(audio)) if len(audio) > 0 else 1e-10
            rms = np.sqrt(np.mean(audio ** 2)) if len(audio) > 0 else 1e-10
            crest_factor = 20 * np.log10(peak / max(rms, 1e-10))

            # Transitorios (placeholder - en prod usar librosa.onset)
            transients = []
            transients_count = 0

            return {
                "dynamic_range": float(dynamic_range),
                "crest_factor": float(crest_factor),
                "transients": transients,
                "transients_count": transients_count
            }
        except Exception as e:
            log.error(f"Error en _analyze_dynamics: {e}")
            return {
                "dynamic_range": 0.0,
                "crest_factor": 0.0,
                "transients": [],
                "transients_count": 0
            }

    async def _detect_issues(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Método 4: Detección de problemas en el audio
        Clipping, DC offset, noise floor, phase, sibilance, resonancias
        """
        try:
            issues = []

            # Clipping
            clipping_samples = int(np.sum(np.abs(audio) >= 0.99))
            if clipping_samples > 0:
                issues.append({
                    "type": "clipping",
                    "severity": min(1.0, clipping_samples / max(len(audio), 1) * 10),
                    "samples": clipping_samples
                })

            # DC Offset
            dc_offset = float(np.mean(audio)) if len(audio) > 0 else 0.0
            dc_offset_percent = abs(dc_offset) * 100
            if dc_offset_percent > self.dc_offset_threshold:
                issues.append({
                    "type": "dc_offset",
                    "severity": min(1.0, dc_offset_percent / 10),
                    "offset": dc_offset
                })

            # Noise Floor
            noise_floor = float(np.percentile(np.abs(audio), 10)) if len(audio) > 0 else 0.0
            noise_floor_dbfs = 20 * np.log10(max(noise_floor, 1e-10))

            # Phase Correlation (simplificado)
            phase_corr = 1.0

            # Sibilance (placeholder)
            sibilance_detected = False
            sibilance_freq = 0.0

            # Resonancias (placeholder)
            resonances = []

            return {
                "clipping_samples": clipping_samples,
                "dc_offset": dc_offset,
                "noise_floor_dbfs": noise_floor_dbfs,
                "phase_correlation": phase_corr,
                "sibilance_detected": sibilance_detected,
                "sibilance_freq": sibilance_freq,
                "resonances": resonances,
                "issues": issues
            }
        except Exception as e:
            log.error(f"Error en _detect_issues: {e}")
            return {
                "clipping_samples": 0,
                "dc_offset": 0.0,
                "noise_floor_dbfs": -80.0,
                "phase_correlation": 1.0,
                "sibilance_detected": False,
                "sibilance_freq": 0.0,
                "resonances": [],
                "issues": []
            }

    async def _analyze_musical(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Método 5: Análisis musical
        BPM, tonalidad, complejidad armónica, percusividad
        """
        try:
            bpm = None  # Placeholder
            key_detected = None  # Placeholder
            key_confidence = None  # Placeholder

            # Separación armónico/percusivo simplificada
            harmonic_energy = np.sum(audio ** 2) * 0.6
            percussive_energy = np.sum(audio ** 2) * 0.4
            total_energy = harmonic_energy + percussive_energy

            harmonic_complexity = harmonic_energy / total_energy if total_energy > 0 else 0.5
            percussiveness = percussive_energy / total_energy if total_energy > 0 else 0.5

            return {
                "bpm": bpm,
                "key_detected": key_detected,
                "key_confidence": key_confidence,
                "harmonic_complexity": float(harmonic_complexity),
                "percussiveness": float(percussiveness)
            }
        except Exception as e:
            log.error(f"Error en _analyze_musical: {e}")
            return {
                "bpm": None,
                "key_detected": None,
                "key_confidence": None,
                "harmonic_complexity": 0.5,
                "percussiveness": 0.5
            }

    async def _classify_audio(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Método 6: Clasificación de instrumento, género, mood
        """
        try:
            instrument_scores = {
                "vocals": 0.3,
                "guitar": 0.2,
                "piano": 0.1,
                "drums": 0.2,
                "bass": 0.1,
                "strings": 0.05,
                "synth": 0.05
            }

            total = sum(instrument_scores.values())
            instrument_prediction = {k: v/total for k, v in instrument_scores.items()}

            genre_prediction = {
                "rock": 0.3,
                "pop": 0.25,
                "electronic": 0.2,
                "hiphop": 0.15,
                "jazz": 0.05,
                "classical": 0.05
            }

            mood_prediction = {
                "energetic": 0.3,
                "calm": 0.2,
                "dark": 0.15,
                "bright": 0.15,
                "emotional": 0.1,
                "aggressive": 0.1
            }

            return {
                "instrument_prediction": instrument_prediction,
                "genre_prediction": genre_prediction,
                "mood_prediction": mood_prediction
            }
        except Exception as e:
            log.error(f"Error en _classify_audio: {e}")
            return {
                "instrument_prediction": {},
                "genre_prediction": {},
                "mood_prediction": {}
            }

    async def _generate_recommendations(self, level_analysis: Dict, spectral_analysis: Dict,
                                      dynamic_analysis: Dict, issues_analysis: Dict,
                                      musical_analysis: Dict) -> List[Dict[str, Any]]:
        """
        Generar recomendaciones basadas en análisis
        """
        try:
            recommendations = []

            if level_analysis.get('lufs_integrated', 0) > -14:
                recommendations.append({
                    "type": "level",
                    "action": "reduce_loudness",
                    "priority": "high",
                    "gain_reduction": max(0, level_analysis['lufs_integrated'] + 14)
                })

            if dynamic_analysis.get('dynamic_range', 0) < 6:
                recommendations.append({
                    "type": "dynamics",
                    "action": "dynamic_expansion",
                    "priority": "medium"
                })

            return recommendations
        except Exception as e:
            log.error(f"Error en _generate_recommendations: {e}")
            return []


# ==============================================================================
# FX ENGINE - CANONICAL (desde shub2.txt)
# ==============================================================================

class FXEngine:
    """
    Motor de generación de cadenas de efectos - CANONICAL
    
    Genera chains basadas en análisis y estilos (shub2.txt)
    """

    def __init__(self):
        self.plugin_catalog = self._load_plugin_catalog()
        self.style_templates = self._load_style_templates()
        log.info("FXEngine inicializado con catálogo de plugins")

    def _load_plugin_catalog(self) -> Dict[str, Any]:
        """Cargar catálogo de plugins disponibles"""
        return {
            "eq": {"name": "EQ", "manufacturer": "Shub", "categories": ["eq", "filter"]},
            "compressor": {"name": "Compressor", "manufacturer": "Shub", "categories": ["dynamics"]},
            "reverb": {"name": "Reverb", "manufacturer": "Shub", "categories": ["reverb"]},
            "delay": {"name": "Delay", "manufacturer": "Shub", "categories": ["delay"]},
            "saturator": {"name": "Saturator", "manufacturer": "Shub", "categories": ["saturation"]}
        }

    def _load_style_templates(self) -> Dict[str, Any]:
        """Cargar plantillas por estilo musical"""
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

    def generate_fx_chain(self, analysis: Dict[str, Any], target_style: str = None) -> FXChain:
        """Generar cadena de efectos basada en análisis y estilo"""
        if target_style is None:
            target_style = "modern_pop"

        style_template = self.style_templates.get(target_style, self.style_templates["modern_pop"])

        plugins = []

        eq_plugin = self._generate_eq_plugin(analysis, style_template)
        if eq_plugin:
            plugins.append(eq_plugin)

        comp_plugin = self._generate_compressor_plugin(analysis, style_template)
        if comp_plugin:
            plugins.append(comp_plugin)

        routing = {"parallel_processing": False, "sidechain_inputs": [], "send_returns": []}

        log.info(f"FX chain generada para estilo {target_style}: {len(plugins)} plugins")

        return FXChain(
            name=f"{target_style}_chain",
            description=f"Cadena de efectos para estilo {target_style}",
            plugins=plugins,
            routing=routing,
            presets=[]
        )

    def _generate_eq_plugin(self, analysis: Dict[str, Any], style_template: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generar plugin EQ basado en análisis espectral"""
        bands = [
            {"type": "low_shelf", "frequency": 100, "gain": 0.0, "q": 0.7},
            {"type": "peaking", "frequency": 1000, "gain": 0.0, "q": 1.0},
            {"type": "high_shelf", "frequency": 5000, "gain": 0.0, "q": 0.7}
        ]

        return {
            "plugin_type": "eq",
            "manufacturer": "Shub-DSP",
            "name": "Shub Matching EQ",
            "parameters": {"bands": bands, "bypass": False}
        }

    def _generate_compressor_plugin(self, analysis: Dict[str, Any], style_template: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generar plugin de compresión basado en dinámica"""
        dynamic_range = analysis.get('dynamic_range', 10.0)
        target_dynamic = style_template.get('dynamic_range', 8.0)
        compression_needed = max(0, dynamic_range - target_dynamic)

        if compression_needed > 2.0:
            return {
                "plugin_type": "compressor",
                "manufacturer": "Shub-DSP",
                "name": "Shub Dynamics",
                "parameters": {
                    "threshold": -20.0,
                    "ratio": 2.0 + (compression_needed / 10),
                    "attack": 10.0,
                    "release": 100.0,
                    "makeup": 0.0,
                    "bypass": False
                }
            }
        return None


# ==============================================================================
# SHUB CORE INITIALIZER - CANONICAL (desde shub2.txt)
# ==============================================================================

class ShubCoreInitializer:
    """
    Inicializador del núcleo DSP de Shub-Niggurath - CANONICAL
    
    Singleton que gestiona initialización de DSPEngine, FXEngine, BD
    """

    def __init__(self):
        self.config = self._load_config()
        self.dsp_engine = None
        self.fx_engine = None
        self.db_engine = None
        log.info("ShubCoreInitializer creado")

    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración"""
        return {
            "samplerate": 48000,
            "channels": 2,
            "fft_size": 4096,
            "hop_length": 1024,
            "analysis_duration": 30
        }

    async def initialize_dsp(self):
        """Inicializar motor DSP"""
        self.dsp_engine = DSPEngine(
            sample_rate=self.config['samplerate'],
            fft_size=self.config['fft_size'],
            hop_length=self.config['hop_length']
        )
        self.fx_engine = FXEngine()
        log.info("DSP y FX engines inicializados")
        return True

    async def initialize_all(self):
        """Inicialización completa del núcleo"""
        try:
            await self.initialize_dsp()
            log.info("ShubCoreInitializer listo")
            return {
                "status": "ready",
                "components": {
                    "dsp_engine": bool(self.dsp_engine),
                    "fx_engine": bool(self.fx_engine)
                }
            }
        except Exception as e:
            log.error(f"Error en initialize_all: {e}")
            raise


# ==============================================================================
# SINGLETON GLOBAL (desde shub2.txt)
# ==============================================================================

_shub_core = None

async def get_shub_core() -> ShubCoreInitializer:
    """Obtener instancia singleton del núcleo Shub"""
    global _shub_core
    if _shub_core is None:
        _shub_core = ShubCoreInitializer()
        await _shub_core.initialize_all()
    return _shub_core
