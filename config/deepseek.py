"""Wrapper ligero para llamadas a DeepSeek con fallback local.

Este módulo no realiza llamadas externas cuando la clave no está presente.
Si `settings.deepseek_api_key` existe, `call_deepseek` intentará usar `httpx`.
En todos los casos devuelve un dict con `ok` y `result`.

FASE 5: Extendido con soporte para DeepSeek R1 meta-reasoning.
"""
from typing import Dict, Any, Optional, Tuple
import os
import time
import logging
import json

import httpx

from config.settings import settings

logger = logging.getLogger("deepseek")

# DeepSeek R1 API endpoint
DEEPSEEK_R1_ENDPOINT = "https://api.deepseek.com/beta/chat/completions"
DEEPSEEK_API_VERSION = "2024-11"


def call_deepseek(prompt: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Dict[str, Any]:
    """Call DeepSeek API if key present; otherwise return a deterministic local fallback.

    Nota: este wrapper respeta la configuración local y no realiza llamadas
    peligrosas durante tests si no hay clave.
    """
    params = params or {}
    key = getattr(settings, "deepseek_api_key", None)
    if not key:
        # Local deterministic fallback: summarize prompt length and echo
        logger.debug("DeepSeek key missing — usando fallback local")
        return {"ok": True, "provider": "local", "result": {"summary": prompt[:512], "meta": {"len": len(prompt)}}}

    url = "https://api.deepseek.example/v1/reason"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "params": params}
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return {"ok": True, "provider": "deepseek", "result": data}
    except Exception as e:
        logger.exception("DeepSeek call failed, returning fallback")
        return {"ok": False, "provider": "deepseek", "error": str(e)}


# ============ PHASE 5: R1 REASONING ==============

def call_deepseek_reasoner(
    prompt: str,
    task_type: str = "reasoning",
    max_reasoning_tokens: int = 8000,
    temperature: float = 0.5,
    timeout: float = 60.0,
) -> Tuple[Dict[str, Any], float, float]:
    """
    Llamar a DeepSeek R1 con capacidades de meta-reasoning.
    
    Devuelve: (result_dict, latency_ms, confidence_score)
    """
    start_time = time.time()
    key = getattr(settings, "deepseek_api_key", None)
    
    if not key or not getattr(settings, "deepseek_r1_enabled", True):
        logger.debug("DeepSeek R1 disabled o sin key — fallback local")
        latency_ms = (time.time() - start_time) * 1000
        return _local_reasoning_fallback(prompt, task_type), latency_ms, 0.4
    
    try:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": getattr(settings, "deepseek_r1_model", "deepseek-reasoner"),
            "messages": [
                {"role": "system", "content": f"You are a helpful AI assistant specialized in {task_type}"},
                {"role": "user", "content": prompt},
            ],
            "max_reasoning_tokens": max_reasoning_tokens,
            "temperature": temperature,
        }
        
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(DEEPSEEK_R1_ENDPOINT, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
            result = {
                "text": "",
                "reasoning": "",
                "usage": data.get("usage", {}),
                "provider": "deepseek-r1",
            }
            
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "reasoning_content" in choice:
                    result["reasoning"] = choice["reasoning_content"]
                if "message" in choice:
                    result["text"] = choice["message"].get("content", "")
                elif "content" in choice:
                    result["text"] = choice["content"]
            
            has_reasoning = bool(result.get("reasoning"))
            confidence = 0.85 if has_reasoning else 0.60
            latency_ms = (time.time() - start_time) * 1000
            
            logger.debug(f"DeepSeek R1: {latency_ms:.1f}ms, reasoning: {has_reasoning}")
            return result, latency_ms, confidence
    
    except Exception as e:
        logger.exception(f"DeepSeek R1 failed: {str(e)}")
        latency_ms = (time.time() - start_time) * 1000
        return _local_reasoning_fallback(prompt, task_type), latency_ms, 0.3


async def call_deepseek_reasoner_async(
    prompt: str,
    task_type: str = "reasoning",
    max_reasoning_tokens: int = 8000,
    temperature: float = 0.5,
    timeout: float = 60.0,
) -> Tuple[Dict[str, Any], float, float]:
    """Async version de call_deepseek_reasoner."""
    start_time = time.time()
    key = getattr(settings, "deepseek_api_key", None)
    
    if not key or not getattr(settings, "deepseek_r1_enabled", True):
        logger.debug("DeepSeek R1 async disabled o sin key — fallback")
        latency_ms = (time.time() - start_time) * 1000
        return _local_reasoning_fallback(prompt, task_type), latency_ms, 0.4
    
    try:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": getattr(settings, "deepseek_r1_model", "deepseek-reasoner"),
            "messages": [
                {"role": "system", "content": f"You are a helpful AI assistant specialized in {task_type}"},
                {"role": "user", "content": prompt},
            ],
            "max_reasoning_tokens": max_reasoning_tokens,
            "temperature": temperature,
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(DEEPSEEK_R1_ENDPOINT, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
            result = {
                "text": "",
                "reasoning": "",
                "usage": data.get("usage", {}),
                "provider": "deepseek-r1",
            }
            
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "reasoning_content" in choice:
                    result["reasoning"] = choice["reasoning_content"]
                if "message" in choice:
                    result["text"] = choice["message"].get("content", "")
                elif "content" in choice:
                    result["text"] = choice["content"]
            
            has_reasoning = bool(result.get("reasoning"))
            confidence = 0.85 if has_reasoning else 0.60
            latency_ms = (time.time() - start_time) * 1000
            return result, latency_ms, confidence
    
    except Exception as e:
        logger.exception(f"Async DeepSeek R1 failed: {str(e)}")
        latency_ms = (time.time() - start_time) * 1000
        return _local_reasoning_fallback(prompt, task_type), latency_ms, 0.3


def _local_reasoning_fallback(prompt: str, task_type: str = "reasoning") -> Dict[str, Any]:
    """Fallback local para razonamiento."""
    reasoning = f"Analyzing {task_type} prompt:\n"
    reasoning += f"- Input length: {len(prompt)} chars\n"
    reasoning += f"- Task type: {task_type}\n"
    
    if "?" in prompt:
        reasoning += "- Detected: Question pattern\n"
    if len(prompt) > 1000:
        reasoning += "- Detected: Long-form content\n"
    
    reasoning += "\nConclusion: Generated response based on analysis.\n"
    
    response = f"[Local reasoning] {prompt[:200]}..."
    
    return {
        "text": response,
        "reasoning": reasoning,
        "usage": {"prompt_tokens": len(prompt) // 4, "completion_tokens": len(response) // 4},
        "provider": "local-reasoning-fallback",
    }


def get_reasoning_strategy(
    prompt: str,
    available_providers: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Determinar estrategia de razonamiento óptima."""
    available_providers = available_providers or {}
    prompt_length = len(prompt)
    
    strategy = {
        "provider": "local",
        "model": "echo",
        "params": {},
        "expected_latency_ms": 100,
    }
    
    if prompt_length > 2000:
        if getattr(settings, "deepseek_r1_enabled", False):
            strategy = {
                "provider": "deepseek-r1",
                "model": getattr(settings, "deepseek_r1_model", "deepseek-reasoner"),
                "params": {
                    "max_reasoning_tokens": 8000,
                    "temperature": 0.5,
                },
                "expected_latency_ms": 3000,
            }
    elif prompt_length > 500:
        if "deepseek" in available_providers.get("remote", {}):
            strategy = {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "params": {"temperature": 0.7},
                "expected_latency_ms": 1500,
            }
    else:
        if "local_llm" in available_providers.get("local", {}):
            strategy = {
                "provider": "local_llm",
                "model": "auto",
                "params": {},
                "expected_latency_ms": 200,
            }
    
    logger.debug(f"Reasoning strategy ({prompt_length} chars): {strategy['provider']}")
    return strategy
