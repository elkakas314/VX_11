"""
Agente de estudio: heurísticas simples + opcional DeepSeek.
"""
from typing import Dict, Any
from config import deepseek


def suggest_fx(metrics: Dict[str, Any]) -> Dict[str, Any]:
    suggestions = []
    if metrics.get("clipping_events", 0) > 0:
        suggestions.append("limiter")
    if metrics.get("noise_floor", -90) > -50:
        suggestions.append("noise_gate")
    if metrics.get("dynamic_range", 0) < 6:
        suggestions.append("multiband_compressor")
    return {"fx": suggestions}


async def deepseek_advise(prompt: str) -> Dict[str, Any]:
    if getattr(deepseek, "call_deepseek_reasoner_async", None):
        try:
            result, latency, conf = await deepseek.call_deepseek_reasoner_async(prompt, task_type="audio_mix")
            return {"provider": "deepseek-r1", "result": result, "latency_ms": latency, "confidence": conf}
        except Exception:
            pass
    return {"provider": "none", "result": "unavailable"}
