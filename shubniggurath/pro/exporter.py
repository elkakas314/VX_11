"""
Exportador simple: guarda WAV mono/stereo y genera previews.
"""
from pathlib import Path
from .audio_io import save_wav


def export_mix(output_dir: str, name: str, mono, stereo, sample_rate: int = 48000):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    master_path = Path(output_dir) / f"{name}_master.wav"
    preview_path = Path(output_dir) / f"{name}_preview.wav"
    save_wav(master_path, mono, sample_rate=sample_rate)
    # preview = downsample stereo to mono short clip
    preview_samples = mono[: sample_rate * 5]  # 5s
    save_wav(preview_path, preview_samples, sample_rate=sample_rate)
    return {"master": str(master_path), "preview": str(preview_path)}
