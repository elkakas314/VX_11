"""DSP Audio Engine - Core audio processing"""

import asyncio
import librosa
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple
from scipy import signal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioAnalysisResult:
    """DSP analysis result container"""
    loudness_lufs: float
    loudness_range_lu: float
    true_peak_dbfs: float
    dynamic_range_dr: float
    crest_factor: float
    spectral_centroid: float
    spectral_rolloff: float
    spectral_flux: float
    zero_crossing_rate: float
    mfcc_features: np.ndarray
    chroma_features: np.ndarray
    spectral_contrast: np.ndarray
    spectral_flatness: float
    bpm: float
    bpm_confidence: float
    key: str
    key_confidence: float
    scale_type: str
    harmonic_complexity: float
    percussiveness: float
    onset_strength: float
    acoustic_fingerprint: bytes
    musical_fingerprint: bytes
    noise_floor_dbfs: float
    clipping_count: int
    dc_offset: float
    phase_correlation: float
    transient_sharpness: float
    signal_to_noise_ratio: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class DSPEngine:
    """Professional DSP audio analysis engine"""
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.n_mfcc = 13
        self.n_chroma = 12
        self.n_contrast_bands = 6
        self.hop_length = 512
        self.n_fft = 4096
        
    async def analyze_audio(self, audio_data: np.ndarray, sr: int = None) -> AudioAnalysisResult:
        """
        Comprehensive audio analysis pipeline
        
        Args:
            audio_data: Audio signal (mono or stereo)
            sr: Sample rate (default: self.sample_rate)
            
        Returns:
            AudioAnalysisResult with complete DSP analysis
        """
        if sr is None:
            sr = self.sample_rate
            
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_mono = np.mean(audio_data, axis=0)
        else:
            audio_mono = audio_data
            
        # Normalization
        audio_mono = audio_mono / (np.max(np.abs(audio_mono)) + 1e-8)
        
        # Parallel analysis tasks
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, self._compute_loudness, audio_mono),
            loop.run_in_executor(None, self._compute_spectral_features, audio_mono, sr),
            loop.run_in_executor(None, self._compute_temporal_features, audio_mono, sr),
            loop.run_in_executor(None, self._compute_timbral_features, audio_mono, sr),
            loop.run_in_executor(None, self._compute_pitch_features, audio_mono, sr),
            loop.run_in_executor(None, self._compute_quality_metrics, audio_mono),
        ]
        
        (loudness_dict, spectral_dict, temporal_dict, timbral_dict, 
         pitch_dict, quality_dict) = await asyncio.gather(*tasks)
        
        # Merge results
        result = AudioAnalysisResult(
            **loudness_dict,
            **spectral_dict,
            **temporal_dict,
            **timbral_dict,
            **pitch_dict,
            **quality_dict,
        )
        
        logger.info(f"Analysis complete: {result.loudness_lufs:.2f} LUFS")
        return result
    
    def _compute_loudness(self, audio: np.ndarray) -> Dict[str, float]:
        """Compute loudness metrics (ITU-R BS.1770)"""
        # Simplified loudness computation
        rms = np.sqrt(np.mean(audio ** 2))
        loudness_lufs = 20 * np.log10(rms + 1e-8) - 23.0  # Offset for LUFS
        
        # Range: compute LU percentiles
        frame_size = int(0.4 * self.sample_rate)  # 400ms frames
        loudness_frames = []
        for i in range(0, len(audio) - frame_size, frame_size):
            frame_rms = np.sqrt(np.mean(audio[i:i+frame_size] ** 2))
            frame_lufs = 20 * np.log10(frame_rms + 1e-8) - 23.0
            loudness_frames.append(frame_lufs)
        
        loudness_frames = np.array(loudness_frames)
        loudness_range_lu = np.percentile(loudness_frames, 95) - np.percentile(loudness_frames, 5)
        
        # True peak
        true_peak_dbfs = 20 * np.log10(np.max(np.abs(audio)) + 1e-8)
        
        # Dynamic range (peak - noise floor)
        noise_floor = np.percentile(np.abs(audio), 1) * 20
        noise_floor_dbfs = 20 * np.log10(noise_floor + 1e-8) - 96.0
        dynamic_range_dr = true_peak_dbfs - noise_floor_dbfs
        
        # Crest factor
        crest_factor = np.max(np.abs(audio)) / (np.sqrt(np.mean(audio ** 2)) + 1e-8)
        
        return {
            "loudness_lufs": float(loudness_lufs),
            "loudness_range_lu": float(loudness_range_lu),
            "true_peak_dbfs": float(true_peak_dbfs),
            "dynamic_range_dr": float(dynamic_range_dr),
            "crest_factor": float(crest_factor),
            "noise_floor_dbfs": float(noise_floor_dbfs),
        }
    
    def _compute_spectral_features(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Compute spectral features"""
        S = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        S_db = librosa.power_to_db(np.abs(S) ** 2, ref=np.max)
        
        # Spectral centroids/rolloff
        centroid = librosa.feature.spectral_centroid(S=S_db, sr=sr)[0]
        rolloff = librosa.feature.spectral_rolloff(S=S_db, sr=sr)[0]
        
        # Spectral flux
        mag = np.abs(S)
        flux = np.sqrt(np.sum(np.diff(mag, axis=1) ** 2, axis=0))
        
        # Spectral contrast
        contrast = librosa.feature.spectral_contrast(S=S_db, sr=sr, n_bands=self.n_contrast_bands)
        
        # Spectral flatness
        mag_sum = np.sum(mag, axis=0) + 1e-8
        flatness = (np.prod(mag + 1e-8, axis=0) ** (1 / mag.shape[0])) / (mag_sum / mag.shape[0])
        
        return {
            "spectral_centroid": float(np.mean(centroid)),
            "spectral_rolloff": float(np.mean(rolloff)),
            "spectral_flux": float(np.mean(flux)),
            "spectral_contrast": contrast.tolist(),
            "spectral_flatness": float(np.mean(flatness)),
        }
    
    def _compute_temporal_features(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Compute temporal features"""
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)[0]
        
        # Onset strength
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_strength = np.mean(onset_env)
        
        # Transient sharpness (first derivative of envelope)
        envelope = np.abs(signal.hilbert(audio))
        envelope_smooth = signal.medfilt(envelope, kernel_size=201)
        transient = np.mean(np.abs(np.diff(envelope_smooth)))
        
        # DC offset
        dc_offset = np.mean(audio)
        
        return {
            "zero_crossing_rate": float(np.mean(zcr)),
            "onset_strength": float(onset_strength),
            "transient_sharpness": float(transient),
            "dc_offset": float(dc_offset),
        }
    
    def _compute_timbral_features(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Compute timbral features (MFCC, Chroma)"""
        # MFCC
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=self.n_mfcc)
        
        # Chroma
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr, n_chroma=self.n_chroma)
        
        # Spectral centroid ratio (harmonicity proxy)
        S = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        mag = np.abs(S)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)
        centroid = np.sum(freqs[:, np.newaxis] * mag, axis=0) / (np.sum(mag, axis=0) + 1e-8)
        harmonic_complexity = np.std(centroid) / (np.mean(centroid) + 1e-8)
        
        # Percussiveness (onset vs sustained)
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        percussiveness = np.mean(onset_env) / (np.mean(np.abs(audio)) + 1e-8)
        
        return {
            "mfcc_features": mfcc.tolist(),
            "chroma_features": chroma.tolist(),
            "harmonic_complexity": float(harmonic_complexity),
            "percussiveness": float(np.clip(percussiveness, 0, 1)),
        }
    
    def _compute_pitch_features(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Compute pitch features (BPM, Key detection)"""
        # Tempo/BPM
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        tempogram = librosa.feature.tempogram(onset_env=onset_env, sr=sr)
        bpm = librosa.tempo(onset_env=onset_env, sr=sr)[0]
        bpm_confidence = 0.8  # Placeholder
        
        # Chroma-based key detection
        chroma = librosa.feature.chroma_cqt(y=audio, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        key_idx = np.argmax(chroma_mean)
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key = key_names[key_idx]
        key_confidence = float(chroma_mean[key_idx] / (np.sum(chroma_mean) + 1e-8))
        
        # Scale type (major/minor heuristic)
        scale_type = "major" if key_confidence > 0.3 else "minor"
        
        return {
            "bpm": float(bpm),
            "bpm_confidence": float(bpm_confidence),
            "key": key,
            "key_confidence": float(key_confidence),
            "scale_type": scale_type,
        }
    
    def _compute_quality_metrics(self, audio: np.ndarray) -> Dict[str, Any]:
        """Compute quality and fingerprint metrics"""
        # Phase correlation (stereo if applicable)
        phase_correlation = 1.0  # Mono default
        
        # Clipping detection
        clipping_threshold = 0.99
        clipping_count = int(np.sum(np.abs(audio) > clipping_threshold))
        
        # SNR (simple estimation)
        noise_floor = np.percentile(np.abs(audio), 1)
        signal_power = np.mean(audio ** 2)
        snr_linear = signal_power / (noise_floor ** 2 + 1e-8)
        snr_db = 10 * np.log10(snr_linear)
        
        # Fingerprints (simple hashing)
        acoustic_fp = hash(audio.tobytes()) & 0xFFFFFFFFFFFFFFFF
        musical_fp = hash(audio[:len(audio)//2].tobytes()) & 0xFFFFFFFFFFFFFFFF
        
        return {
            "phase_correlation": float(phase_correlation),
            "clipping_count": int(clipping_count),
            "signal_to_noise_ratio": float(np.clip(snr_db, 0, 120)),
            "acoustic_fingerprint": acoustic_fp.to_bytes(8, 'big'),
            "musical_fingerprint": musical_fp.to_bytes(8, 'big'),
        }
