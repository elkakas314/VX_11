import wave
import audioop
import math
from typing import Dict, Any, Tuple, List
from pathlib import Path


def _read_pcm_mono(path: str) -> Tuple[bytes, int, int]:
    """
    Lee archivo WAV y retorna frames mono, sample_rate, sampwidth.
    Si es estéreo, mezcla a mono.
    """
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        sample_rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
        if n_channels > 1:
            frames = audioop.tomono(frames, sampwidth, 0.5, 0.5)
        return frames, sample_rate, sampwidth


def _peak_rms(frames: bytes, sampwidth: int) -> Tuple[float, float]:
    peak = audioop.max(frames, sampwidth)
    rms = audioop.rms(frames, sampwidth)
    return peak, rms


def _estimate_lufs(rms: float, sampwidth: int) -> float:
    # Aproximación: referencia full-scale según bits
    max_amp = float(2 ** (sampwidth * 8 - 1))
    if rms <= 0 or max_amp <= 0:
        return -999.0
    dbfs = 20 * math.log10(rms / max_amp)
    # LUFS aproximado asumiendo weighting simple
    return dbfs


def _detect_clipping(frames: bytes, sampwidth: int, threshold_db: float = -1.0) -> int:
    max_amp = float(2 ** (sampwidth * 8 - 1))
    thresh = max_amp * (10 ** (threshold_db / 20))
    clip_count = 0
    for i in range(0, len(frames), sampwidth):
        sample = audioop.getsample(frames, sampwidth, i // sampwidth)
        if abs(sample) >= thresh:
            clip_count += 1
    return clip_count


def _dynamic_range(peak: float, rms: float, sampwidth: int) -> float:
    max_amp = float(2 ** (sampwidth * 8 - 1))
    if peak <= 0 or rms <= 0:
        return 0.0
    peak_db = 20 * math.log10(peak / max_amp)
    rms_db = 20 * math.log10(rms / max_amp)
    return peak_db - rms_db


def _noise_floor(frames: bytes, sampwidth: int, window: int = 2048) -> float:
    """
    Estimación sencilla: promedio de RMS en ventanas y tomar percentil bajo.
    """
    if len(frames) < window:
        return -90.0
    rms_values: List[float] = []
    step = window
    for i in range(0, len(frames), step):
        chunk = frames[i : i + window]
        if not chunk:
            continue
        rms_values.append(audioop.rms(chunk, sampwidth))
    if not rms_values:
        return -90.0
    rms_values.sort()
    low = rms_values[max(0, len(rms_values) // 10 - 1)]
    max_amp = float(2 ** (sampwidth * 8 - 1))
    if low <= 0 or max_amp <= 0:
        return -90.0
    return 20 * math.log10(low / max_amp)


def analyze_audio(path: str) -> Dict[str, Any]:
    """
    Pipeline DSP básico: peak, rms, lufs aproximado, clipping, ruido y DR.
    """
    p = Path(path)
    if not p.exists():
        return {"status": "error", "error": "file_not_found"}

    frames, sample_rate, sampwidth = _read_pcm_mono(str(p))
    peak, rms = _peak_rms(frames, sampwidth)
    lufs = _estimate_lufs(rms, sampwidth)
    clipping = _detect_clipping(frames, sampwidth)
    dr = _dynamic_range(peak, rms, sampwidth)
    noise_floor = _noise_floor(frames, sampwidth)

    issues = []
    if clipping > 0:
        issues.append("clipping_detected")
    if noise_floor > -40:
        issues.append("high_noise_floor")
    if dr < 6:
        issues.append("low_dynamic_range")

    fx_suggestions = []
    if clipping > 0:
        fx_suggestions.append("limiter")
    if noise_floor > -40:
        fx_suggestions.append("noise_gate")
    if dr < 6:
        fx_suggestions.append("multiband_compressor")

    return {
        "status": "ok",
        "sample_rate": sample_rate,
        "peak": peak,
        "rms": rms,
        "lufs": lufs,
        "dynamic_range": dr,
        "noise_floor": noise_floor,
        "clipping_events": clipping,
        "issues": issues,
        "fx_suggestions": fx_suggestions,
    }
