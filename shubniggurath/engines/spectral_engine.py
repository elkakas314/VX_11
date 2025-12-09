"""Spectral Engine: Análisis espectral avanzado."""

from typing import Dict, Any, List
import numpy as np


class SpectralEngine:
    """Motor de análisis espectral avanzado."""

    def __init__(self, fft_size: int = 4096, hop_length: int = 1024):
        self.fft_size = fft_size
        self.hop_length = hop_length

    async def analyze_spectrum(self, audio: np.ndarray, 
                              sample_rate: int) -> Dict[str, Any]:
        """Análisis espectral completo."""
        return {
            "centroid": self._calculate_spectral_centroid(audio, sample_rate),
            "rolloff": self._calculate_spectral_rolloff(audio, sample_rate),
            "flatness": self._calculate_spectral_flatness(audio),
            "flux": self._calculate_spectral_flux(audio),
            "peaks": self._find_spectral_peaks(audio, sample_rate)
        }

    def _calculate_spectral_centroid(self, audio: np.ndarray, 
                                    sample_rate: int) -> float:
        """Calcular centroide espectral."""
        if len(audio) == 0:
            return 0.0
        
        spectrum = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), 1/sample_rate)
        
        if np.sum(spectrum) == 0:
            return 0.0
            
        return float(np.sum(freqs * spectrum) / np.sum(spectrum))

    def _calculate_spectral_rolloff(self, audio: np.ndarray,
                                   sample_rate: int) -> float:
        """Calcular rolloff espectral (85%)."""
        spectrum = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), 1/sample_rate)
        
        cumsum = np.cumsum(spectrum)
        total = np.sum(spectrum)
        
        if total == 0:
            return 0.0
            
        idx = np.where(cumsum >= 0.85 * total)[0]
        if len(idx) > 0:
            return float(freqs[idx[0]])
        return float(freqs[-1])

    def _calculate_spectral_flatness(self, audio: np.ndarray) -> float:
        """Calcular planeidad espectral (Wiener entropy)."""
        spectrum = np.abs(np.fft.rfft(audio)) + 1e-10
        
        geometric_mean = np.exp(np.mean(np.log(spectrum)))
        arithmetic_mean = np.mean(spectrum)
        
        if arithmetic_mean == 0:
            return 0.0
            
        return float(geometric_mean / arithmetic_mean)

    def _calculate_spectral_flux(self, audio: np.ndarray) -> float:
        """Calcular flujo espectral frame-a-frame."""
        # Dividir en frames y calcular diferencias
        frame_size = self.hop_length
        num_frames = len(audio) // frame_size
        
        if num_frames < 2:
            return 0.0
        
        flux_values = []
        for i in range(num_frames - 1):
            frame1 = np.abs(np.fft.rfft(audio[i*frame_size:(i+1)*frame_size]))
            frame2 = np.abs(np.fft.rfft(audio[(i+1)*frame_size:(i+2)*frame_size]))
            
            diff = np.sqrt(np.sum((frame2 - frame1) ** 2))
            flux_values.append(diff)

        return float(np.mean(flux_values)) if flux_values else 0.0

    def _find_spectral_peaks(self, audio: np.ndarray,
                            sample_rate: int) -> List[Dict[str, float]]:
        """Encontrar picos espectrales principales."""
        spectrum = np.abs(np.fft.rfft(audio))
        freqs = np.fft.rfftfreq(len(audio), 1/sample_rate)
        
        # Encontrar picos simples
        peaks = []
        threshold = np.mean(spectrum) + np.std(spectrum)
        
        for i in range(1, len(spectrum) - 1):
            if spectrum[i] > spectrum[i-1] and spectrum[i] > spectrum[i+1]:
                if spectrum[i] > threshold:
                    peaks.append({
                        "frequency": float(freqs[i]),
                        "magnitude": float(spectrum[i]),
                        "db": float(20 * np.log10(spectrum[i] + 1e-10))
                    })

        return sorted(peaks, key=lambda x: x["magnitude"], reverse=True)[:10]

    async def identify_resonances(self, audio: np.ndarray,
                                 sample_rate: int) -> List[Dict[str, Any]]:
        """Identificar resonancias problemáticas."""
        peaks = self._find_spectral_peaks(audio, sample_rate)
        
        resonances = []
        for peak in peaks:
            freq = peak["frequency"]
            # Resonancias problemáticas típicamente en 60-300 Hz o 3-7 kHz
            if (60 <= freq <= 300) or (3000 <= freq <= 7000):
                resonances.append({
                    "frequency": freq,
                    "severity": min(1.0, peak["magnitude"] / np.max([p["magnitude"] for p in peaks])),
                    "type": "room" if freq < 300 else "presence",
                    "correction": f"Aplicar EQ notch a {freq} Hz"
                })

        return resonances
