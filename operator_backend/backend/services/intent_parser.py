from typing import Dict, Any


class AudioIntentParser:
    """Minimal intent parser for operator text/audio commands."""

    def parse(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        msg = (message or "").lower()
        intent = "chat"
        if "manifest" in msg:
            intent = "manifest"
        elif "task" in msg or "queue" in msg:
            intent = "task"
        elif "shub" in msg or "audio" in msg:
            intent = "audio_analysis"
        return {"intent": intent, "message": message, "context": context}

    # VX11 v6.7 – mixing intent parser (non-breaking)
    def parse_mixing_intent(self, message: str) -> Dict[str, Any]:
        msg = (message or "").lower()
        ops = []
        if "reson" in msg:
            ops.append({"action": "remove_resonances"})
        if "paneo" in msg or "pan" in msg:
            ops.append({"action": "natural_panning"})
        if "voz" in msg or "voice" in msg:
            ops.append({"action": "raise_voice", "gain_db": 1})
        if "mezcla" in msg or "mix" in msg:
            ops.append({"action": "mix_realistic"})
        if "compara" in msg:
            ops.append({"action": "compare_takes"})
        return {
            "intent": "mixing",
            "ops": ops or [{"action": "analyze_mix"}],
            "raw": message,
        }
