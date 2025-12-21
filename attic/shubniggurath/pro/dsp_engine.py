"""
Motor DSP avanzado con análisis LUFS, espectral, dinámico, detección de problemas.
Reutiliza audio_io, integra con shub_db.
"""

import numpy as np
import asyncio
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import warnings

import importlib

# librosa (opcional)
spec = importlib.util.find_spec("librosa")
if spec is not None:
    try:
        librosa = importlib.import_module("librosa")
        HAS_LIBROSA = True
    except Exception:
        HAS_LIBROSA = False
        warnings.warn("librosa no disponible; análisis espectral limitado")
else:
    HAS_LIBROSA = False
    warnings.warn("librosa no disponible; análisis espectral limitado")

# scipy (opcional) — cargar submódulos dinámicamente para evitar import estático de submódulos
spec = importlib.util.find_spec("scipy")
if spec is not None:
    signal = None
    stats = None
    try:
        signal = importlib.import_module("scipy.signal")
    except Exception:
        signal = None
    try:
        stats = importlib.import_module("scipy.stats")
    except Exception:
        stats = None

    # Considerar disponible sólo si el submódulo signal fue cargado (se usa signal.resample en este módulo)
    HAS_SCIPY = signal is not None
    if not HAS_SCIPY:
        warnings.warn("scipy presente pero 'scipy.signal' no disponible; análisis de picos limitado")
else:
    HAS_SCIPY = False
    warnings.warn("scipy no disponible; análisis de picos limitado")


@dataclass
class AudioAnalysisResult:
    """Resultado completo del análisis DSP"""
    duration: float
    sample_rate: int
    channels: int
    
    # Niveles
    peak_dbfs: float
    rms_dbfs: float
    lufs_integrated: float
    lufs_range: float
    true_peak_dbfs: float
    
    # Espectral
    spectral_centroid: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_flux: float = 0.0
    zero_crossing_rate: float = 0.0
    spectral_flatness: float = 0.0
    mfcc: List[float] = None
    chroma: List[float] = None
    spectral_contrast: List[float] = None
    
    # Dinámico
    dynamic_range: float = 0.0
    crest_factor: float = 0.0
    transients_count: int = 0
    transients: List[float] = None
    
    # Problemas
    clipping_samples: int = 0
    dc_offset: float = 0.0
    noise_floor_dbfs: float = 0.0
    phase_correlation: float = 0.0
    
    # Musical
    estimated_bpm: Optional[float] = None
    estimated_key: Optional[str] = None
    key_confidence: Optional[float] = None
    harmonic_complexity: float = 0.0
    percussiveness: float = 0.0
    
    # Clasificación
    instrument_class: Optional[str] = None
    genre_predicted: Optional[str] = None
    mood_predicted: Optional[str] = None
    
    # Issues y recomendaciones
    issues: List[Dict[str, Any]] = None
    recommendations: List[Dict[str, Any]] = None


class DSPEngine:
    """Motor DSP basado en shub2.txt spec"""
    
    def __init__(self, sample_rate: int = 48000, fft_size: int = 4096, hop_length: int = 1024):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.hop_length = hop_length
        
        # Umbrales
        self.clipping_threshold = -0.5  # dBFS
        self.dc_offset_threshold = 0.01  # 1%
        self.noise_floor_threshold = -60  # dBFS
        self.phase_corr_threshold = 0.5
    
    async def analyze_file(self, file_path: str) -> AudioAnalysisResult:
        """Análisis completo de archivo de audio"""
        from .audio_io import load_audio
        
        samples, sr = load_audio(file_path)
        audio_data = np.array(samples, dtype=np.float32)
        
        return await self.analyze_audio(audio_data, sr)
    
    async def analyze_audio(self, audio_data: np.ndarray, sample_rate: int = None) -> AudioAnalysisResult:
        """Análisis completo de datos de audio"""
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        # Convertir a mono si estéreo
        if len(audio_data.shape) > 1:
            audio_mono = np.mean(audio_data, axis=1)
            channels = audio_data.shape[1]
        else:
            audio_mono = audio_data.copy()
            channels = 1
        
        # Análisis en paralelo
        tasks = [
            self._analyze_levels(audio_mono),
            self._analyze_dynamics(audio_mono),
            self._detect_issues(audio_mono, sample_rate),
        ]
        
        # Agregar análisis espectral si librosa disponible
        if HAS_LIBROSA:
            tasks.extend([
                self._analyze_spectral(audio_mono, sample_rate),
                self._analyze_musical(audio_mono, sample_rate),
            ])
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extraer resultados
        level_analysis = results[0] if not isinstance(results[0], Exception) else {}
        dynamic_analysis = results[1] if not isinstance(results[1], Exception) else {}
        issues_analysis = results[2] if not isinstance(results[2], Exception) else {}
        
        spectral_analysis = {}
        musical_analysis = {}
        
        if HAS_LIBROSA:
            spectral_analysis = results[3] if not isinstance(results[3], Exception) else {}
            musical_analysis = results[4] if not isinstance(results[4], Exception) else {}
        
        # Combinar resultados
        combined = {
            "duration": len(audio_mono) / sample_rate,
            "sample_rate": sample_rate,
            "channels": channels,
            **level_analysis,
            **dynamic_analysis,
            **spectral_analysis,
            **musical_analysis,
            **issues_analysis,
        }
        
        # Generar recomendaciones
        recommendations = await self._generate_recommendations(combined)
        combined["recommendations"] = recommendations
        
        return AudioAnalysisResult(**combined)
    
    async def _analyze_levels(self, audio: np.ndarray) -> Dict[str, Any]:
        """Análisis de niveles LUFS, RMS, Peak, True Peak"""
        audio_abs = np.abs(audio)
        
        # Peak
        peak_linear = np.max(audio_abs) if len(audio_abs) > 0 else 0
        peak_dbfs = 20 * np.log10(max(peak_linear, 1e-10))
        
        # RMS
        rms_linear = np.sqrt(np.mean(audio ** 2))
        rms_dbfs = 20 * np.log10(max(rms_linear, 1e-10))
        
        # LUFS (simplificado; en producción usar pyloudnorm)
        lufs_integrated = rms_dbfs - 23  # Aproximación
        
        # True Peak (interpolado)
        true_peak_dbfs = peak_dbfs
        if HAS_SCIPY:
            try:
                upsampled = signal.resample(audio, len(audio) * 4)
                true_peak = np.max(np.abs(upsampled))
                true_peak_dbfs = 20 * np.log10(max(true_peak, 1e-10))
            except Exception:
                pass
        
        # Loudness Range
        window_size = max(1, self.sample_rate // 10)
        windows = len(audio) // window_size
        loudness_values = []
        
        for i in range(windows):
            segment = audio[i*window_size:(i+1)*window_size]
            if len(segment) > 0:
                seg_rms = np.sqrt(np.mean(segment ** 2))
                loudness_values.append(20 * np.log10(max(seg_rms, 1e-10)))
        
        lufs_range = 0.0
        if len(loudness_values) > 1:
            lufs_range = np.percentile(loudness_values, 95) - np.percentile(loudness_values, 5)
        
        return {
            "peak_dbfs": float(peak_dbfs),
            "rms_dbfs": float(rms_dbfs),
            "lufs_integrated": float(lufs_integrated),
            "lufs_range": float(lufs_range),
            "true_peak_dbfs": float(true_peak_dbfs),
        }
    
    async def _analyze_dynamics(self, audio: np.ndarray) -> Dict[str, Any]:
        """Análisis de dinámica"""
        window_size = max(1, self.sample_rate // 10)
        windows = len(audio) // window_size
        
        rms_values = []
        for i in range(windows):
            segment = audio[i*window_size:(i+1)*window_size]
            if len(segment) > 0:
                rms = np.sqrt(np.mean(segment ** 2))
                rms_values.append(20 * np.log10(max(rms, 1e-10)))
        
        dynamic_range = 0.0
        if len(rms_values) > 1:
            dynamic_range = np.max(rms_values) - np.min(rms_values)
        
        # Crest Factor
        peak = np.max(np.abs(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        crest_factor = 20 * np.log10(peak / max(rms, 1e-10))
        
        # Transitorios
        transients = []
        transients_count = 0
        if HAS_LIBROSA:
            try:
                transients = librosa.onset.onset_detect(y=audio, sr=self.sample_rate, units='time').tolist()
                transients_count = len(transients)
            except Exception:
                pass
        
        return {
            "dynamic_range": float(dynamic_range),
            "crest_factor": float(crest_factor),
            "transients": transients,
            "transients_count": int(transients_count),
        }
    
    async def _analyze_spectral(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Análisis espectral (requiere librosa)"""
        if not HAS_LIBROSA:
            return {}
        
        try:
            stft = librosa.stft(audio, n_fft=self.fft_size, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=self.fft_size)
            
            # Centroide espectral
            spec_cent_data = np.sum(freqs * magnitude.sum(axis=1)) / max(np.sum(magnitude), 1e-10)
            
            # Roll-off (85%)
            total_energy = np.sum(magnitude)
            if total_energy > 0:
                target_energy = 0.85 * total_energy
                cumulative = np.cumsum(magnitude.sum(axis=1))
                rolloff_idx = np.searchsorted(cumulative, target_energy)
                rolloff_idx = min(rolloff_idx, len(freqs) - 1)
                spec_rolloff = freqs[rolloff_idx]
            else:
                spec_rolloff = 0.0
            
            # Zero Crossing Rate
            zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
            
            # MFCC
            mfcc = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
            mfcc_mean = np.mean(mfcc, axis=1).tolist()
            
            # Chroma
            chroma = librosa.feature.chroma_stft(y=audio, sr=sample_rate)
            chroma_mean = np.mean(chroma, axis=1).tolist()
            
            # Spectral Contrast
            spec_contrast = librosa.feature.spectral_contrast(y=audio, sr=sample_rate)
            spec_contrast_mean = np.mean(spec_contrast, axis=1).tolist()
            
            return {
                "spectral_centroid": float(spec_cent_data),
                "spectral_rolloff": float(spec_rolloff),
                "zero_crossing_rate": float(zcr),
                "mfcc": mfcc_mean,
                "chroma": chroma_mean,
                "spectral_contrast": spec_contrast_mean,
            }
        except Exception as e:
            warnings.warn(f"Error en análisis espectral: {e}")
            return {}
    
    async def _analyze_musical(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Análisis musical (BPM, key, etc.)"""
        if not HAS_LIBROSA:
            return {}
        
        try:
            # Estimación de tempo
            onset_env = librosa.onset.onset_strength(y=audio, sr=sample_rate)
            bpm = librosa.beat.tempo(y=audio, sr=sample_rate)[0]
            
            return {
                "estimated_bpm": float(bpm),
                "harmonic_complexity": 0.5,  # Placeholder
                "percussiveness": 0.3,  # Placeholder
            }
        except Exception as e:
            warnings.warn(f"Error en análisis musical: {e}")
            return {}
    
    async def _detect_issues(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Detección de problemas en audio"""
        issues = []
        
        # Clipping
        clipping_threshold_linear = 10 ** (self.clipping_threshold / 20)
        clipping_samples = np.sum(np.abs(audio) >= clipping_threshold_linear)
        
        if clipping_samples > 0:
            issues.append({
                "type": "clipping",
                "severity": min(1.0, float(clipping_samples) / len(audio) * 100),
                "samples": int(clipping_samples),
            })
        
        # DC Offset
        dc_offset = float(np.mean(audio))
        dc_offset_percent = abs(dc_offset) * 100
        
        if dc_offset_percent > self.dc_offset_threshold:
            issues.append({
                "type": "dc_offset",
                "severity": min(1.0, dc_offset_percent / 10),
                "offset": dc_offset,
            })
        
        # Noise Floor
        noise_floor = float(np.percentile(np.abs(audio), 10))
        noise_floor_dbfs = 20 * np.log10(max(noise_floor, 1e-10))
        
        if noise_floor_dbfs > self.noise_floor_threshold:
            issues.append({
                "type": "high_noise_floor",
                "severity": min(1.0, (noise_floor_dbfs - self.noise_floor_threshold) / 30),
                "noise_dbfs": noise_floor_dbfs,
            })
        
        return {
            "clipping_samples": int(clipping_samples),
            "dc_offset": dc_offset,
            "noise_floor_dbfs": noise_floor_dbfs,
            "issues": issues,
        }
    
    async def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generar recomendaciones basadas en análisis"""
        recommendations = []
        
        # Basadas en niveles
        if analysis.get("peak_dbfs", -100) > -3:
            recommendations.append({
                "area": "levels",
                "severity": "warning",
                "message": "Peak muy alto; considerar normalización",
            })
        
        if analysis.get("lufs_integrated", 0) > -14:
            recommendations.append({
                "area": "loudness",
                "severity": "info",
                "message": "Considerar conformarse a -14 LUFS (streaming)",
            })
        
        # Basadas en problemas
        issues = analysis.get("issues", [])
        if issues:
            recommendations.append({
                "area": "quality",
                "severity": "warning",
                "message": f"Se detectaron {len(issues)} problemas de audio",
            })
        
        return recommendations
