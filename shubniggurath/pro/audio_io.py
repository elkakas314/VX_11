"""
Lectura/escritura de audio (WAV/FLAC/MP3) con dependencias estándar.
"""
from pathlib import Path
import wave
import array

try:  # opcional
    import soundfile as sf  # type: ignore
except Exception:  # pragma: no cover
    sf = None


def load_audio(path: str):
    """
    Retorna (samples mono list[float], sample_rate).
    Usa soundfile si está disponible; fallback a wave.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    if sf:
        data, sr = sf.read(str(p))
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        return data.astype("float32").tolist(), sr

    with wave.open(str(p), "rb") as wf:
        sr = wf.getframerate()
        sampwidth = wf.getsampwidth()
        nframes = wf.getnframes()
        frames = wf.readframes(nframes)
        arr = array.array("h" if sampwidth == 2 else "b")
        arr.frombytes(frames)
        data = list(arr)
        if wf.getnchannels() > 1:
            data = [sum(data[i:i + wf.getnchannels()]) / wf.getnchannels() for i in range(0, len(data), wf.getnchannels())]
        norm = float(2 ** (8 * sampwidth - 1))
        samples = [float(x) / norm for x in data]
        return samples, sr


def save_wav(path: str, samples, sample_rate: int = 48000):
    """Guarda WAV mono 16-bit."""
    clamped = [max(-1.0, min(1.0, float(s))) for s in samples]
    ints = array.array("h", [int(s * 32767) for s in clamped])
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(ints.tobytes())
    return str(path)
