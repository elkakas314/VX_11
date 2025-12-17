import os
import wave
import math
from shubniggurath.pro.audio_io import load_audio, save_wav
from shubniggurath.pro.dsp import analyze_basic
from shubniggurath.pro.mixing import auto_mix


def make_tone(path: str, sr: int = 44100, seconds: float = 1.0, freq: float = 440.0):
    samples = [0.2 * math.sin(2 * math.pi * freq * n / sr) for n in range(int(sr * seconds))]
    save_wav(path, samples, sample_rate=sr)
    return path


def test_audio_io_and_dsp(tmp_path):
    wav = tmp_path / "tone.wav"
    make_tone(str(wav))
    samples, sr = load_audio(str(wav))
    metrics = analyze_basic(samples)
    assert sr > 0
    assert metrics["peak"] > 0
    assert "lufs" in metrics
    mix = auto_mix(samples)
    assert "mono" in mix and "stereo" in mix
    assert len(mix["stereo"]) == 2
