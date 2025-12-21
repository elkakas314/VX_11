import sys
from pathlib import Path

# Ensure local operator package shadows stdlib operator module
sys.modules.pop("operator", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from operator_backend.backend.services.intent_parser import AudioIntentParser  # type: ignore  # noqa: E402


def test_intent_parser_mix():
    parser = AudioIntentParser()
    res = parser.parse("Necesito mezcla rock a -12 LUFS", {})
    assert res["intent"] in ("audio_analysis", "chat")


def test_intent_parser_master_default():
    parser = AudioIntentParser()
    res = parser.parse("master streaming", {})
    assert res["intent"] in ("audio_analysis", "chat")
