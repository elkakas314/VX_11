"""
FASE 7: Orchestration Bridge v6.2
Orquestación integrada entre Hermes, Switch, Madre
"""

import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime
from config.forensics import write_log
from config.context7 import get_default_context7
from config.tokens import get_token
from config.settings import settings


class OrchestrationBridge:
    """Puente de orquestación entre módulos"""
    
    def __init__(self, endpoints: Dict[str, str]):
        """
        endpoints: {
            "hermes": "http://hermes:8003",
            "switch": "http://switch:8002",
            "madre": "http://madre:8001",
        }
        Normalmente construido por get_bridge() usando config/settings.py
        """
        self.endpoints = {k: v.rstrip("/") for k, v in endpoints.items()}
        self.headers = {
            settings.token_header: get_token("VX11_TENTACULO_LINK_TOKEN")
            or get_token("VX11_GATEWAY_TOKEN")
            or settings.api_token
        }
        self.http = httpx.AsyncClient(timeout=30.0, headers=self.headers)
    
    async def execute_full_pipeline(self, query: str, context7: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Pipeline completo:
        1. Switch: escoger mejor engine (scoring)
        2. Hermes: ejecutar comando/browse si es necesario
        3. Madre: persistir resultado en task
        """
        ctx7 = context7 or get_default_context7()
        
        try:
            # PASO 1: Switch - scoring
            write_log("bridge", "pipeline:step1:switch_scoring")
            
            switch_payload = {
                "query": query,
                "context7": ctx7,
            }
            
            async with self.http.post(
                f"{self.endpoints['switch']}/switch/query",
                json=switch_payload
            ) as resp:
                if resp.status_code != 200:
                    return {
                        "status": "error",
                        "step": "switch_scoring",
                        "error": f"Switch failed: {resp.status_code}",
                    }
                switch_result = resp.json()
            
            engine_selected = switch_result.get("engine_selected")
            score = switch_result.get("score")
            
            # PASO 2: Hermes - ejecutar si es comando/browser
            write_log("bridge", f"pipeline:step2:hermes_execute:engine={engine_selected}")
            
            hermes_payload = {
                "command": query,
                "context7": ctx7,
            }
            
            hermes_result = None
            if "hermes" in engine_selected or "cli" in engine_selected:
                try:
                    async with self.http.post(
                        f"{self.endpoints['hermes']}/hermes/execute",
                        json=hermes_payload,
                        timeout=10.0
                    ) as resp:
                        if resp.status_code == 200:
                            hermes_result = resp.json()
                except:
                    hermes_result = None
            
            # PASO 3: Madre - persistir
            write_log("bridge", "pipeline:step3:madre_persist")
            
            madre_payload = {
                "messages": [{"role": "user", "content": query}],
                "context7": ctx7,
                "metadata": {
                    "switch_engine": engine_selected,
                    "switch_score": score,
                    "hermes_executed": hermes_result is not None,
                }
            }
            
            madre_result = None
            try:
                async with self.http.post(
                    f"{self.endpoints['madre']}/chat",
                    json=madre_payload,
                    timeout=15.0
                ) as resp:
                    if resp.status_code == 200:
                        madre_result = resp.json()
            except:
                madre_result = None
            
            # Resultado final
            return {
                "status": "ok",
                "pipeline": {
                    "switch": {
                        "engine": engine_selected,
                        "score": score,
                    },
                    "hermes": {
                        "executed": hermes_result is not None,
                        "result": hermes_result,
                    },
                    "madre": {
                        "persisted": madre_result is not None,
                        "result": madre_result,
                    }
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            write_log("bridge", f"pipeline_error:{e}", level="ERROR")
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def scoring_and_execute(self, query: str, context7: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Versión rápida: solo Switch scoring + ejecución directa
        """
        ctx7 = context7 or get_default_context7()
        
        try:
            # Switch scoring
            switch_payload = {
                "query": query,
                "context7": ctx7,
            }
            
            async with self.http.post(
                f"{self.endpoints['switch']}/switch/query",
                json=switch_payload
            ) as resp:
                if resp.status_code != 200:
                    return {"status": "error", "error": "Switch scoring failed"}
                switch_result = resp.json()
            
            return {
                "status": "ok",
                "engine": switch_result.get("engine_selected"),
                "score": switch_result.get("score"),
                "scores_detail": switch_result.get("scores_per_engine"),
            }
        
        except Exception as e:
            write_log("bridge", f"scoring_error:{e}", level="ERROR")
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Cierra cliente HTTP"""
        await self.http.aclose()


# Instancia global
_bridge = None


def get_bridge(endpoints: Dict[str, str] = None) -> OrchestrationBridge:
    """Retorna instancia singleton del bridge"""
    global _bridge
    if _bridge is None or endpoints:
        _bridge = OrchestrationBridge(endpoints or {
            "hermes": (settings.hermes_url or f"http://hermes:{settings.hermes_port}").rstrip("/"),
            "switch": (settings.switch_url or f"http://switch:{settings.switch_port}").rstrip("/"),
            "madre": (settings.madre_url or f"http://madre:{settings.madre_port}").rstrip("/"),
        })
    return _bridge


# ========== COPILOT OPERATOR BRIDGE (v6.2) ==========

async def build_operator_payload(message: str, context7: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Construye payload canónico para operador Copilot.
    
    Estructura interna, NO se envía a VX11 aún.
    """
    ctx7 = context7 or get_default_context7()
    
    return {
        "source": "copilot_operator",
        "message": message,
        "context7": ctx7,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": ctx7.get("layer7_meta", {}).get("trace_id"),
        }
    }


async def validate_operator_request(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida request del operador antes de procesamiento.
    Retorna {"valid": bool, "errors": [...], "sanitized": {...}}
    """
    from config.copilot_operator import validate_operator_action, blocked_actions
    
    errors = []
    
    # 1. Tamaño máximo (16 KB)
    req_json = json.dumps(req)
    if len(req_json) > 16384:
        errors.append("Request exceeds 16KB limit")
    
    # 2. Validar estructura mínima
    if "message" not in req or not isinstance(req["message"], str):
        errors.append("Missing or invalid 'message' field")
    
    message = req.get("message", "").lower()
    
    # 3. Buscar comandos shell
    shell_indicators = ["shell", "bash", "sh ", "exec", "system", "popen"]
    if any(indicator in message for indicator in shell_indicators):
        errors.append("Shell commands detected and blocked")
    
    # 4. Buscar rutas absolutas (potencial inyección)
    if any(char in message for char in ["/etc/", "/root/", "/sys/", "C:\\"]):
        errors.append("Absolute paths detected")
    
    # 5. Buscar acciones bloqueadas
    for blocked in blocked_actions:
        if blocked in message:
            errors.append(f"Blocked action detected: {blocked}")
            break
    
    # 6. Context-7 debe estar presente
    if "context7" not in req:
        errors.append("Missing context-7 in request")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "sanitized": {
            "message": req.get("message", ""),
            "context7": req.get("context7", {}),
        }
    }


async def safe_route_to_vx11(
    message: str,
    context7: Optional[Dict] = None,
    gateway_endpoint: str = "http://tentaculo_link:8000"
) -> Dict[str, Any]:
    """
    Ruta SEGURA a VX11 (NOT ACTIVE IN v6.2).
    
    Cuando operator_mode="vx11_operator" en copilot_operator.py:
    1. Construye payload
    2. Valida request
    3. Envía a gateway (si pasa validación)
    
    Por ahora: SOLO PREPARADO, NO EJECUTA.
    """
    from config.copilot_operator import is_operator_active, validate_operator_action
    
    write_log("operator_bridge", f"route_attempt:mode={'active' if is_operator_active() else 'inactive'}")
    
    if not is_operator_active():
        write_log("operator_bridge", "operator_inactive:request_rejected")
        return {
            "status": "error",
            "reason": "Copilot operator mode is disabled",
            "message": "To enable: set operator_mode='vx11_operator' in config/copilot_operator.py"
        }
    
    # Construir payload
    payload = await build_operator_payload(message, context7)
    
    # Validar
    validation = await validate_operator_request(payload)
    if not validation["valid"]:
        write_log("operator_bridge", f"validation_failed:errors={len(validation['errors'])}")
        return {
            "status": "error",
            "reason": "Request validation failed",
            "errors": validation["errors"]
        }
    
    # Verificar acción
    if not validate_operator_action(message):
        write_log("operator_bridge", f"action_not_allowed:{message[:50]}")
        return {
            "status": "error",
            "reason": "Action not allowed for Copilot operator",
            "message": message[:100]
        }
    
    # AQUÍ iría el envío a VX11 si estuviera activo
    # Por ahora: solo log y retorno simulado
    write_log("operator_bridge", f"safe_route_prepared:message_len={len(message)}")
    
    return {
        "status": "prepared",
        "note": "Copilot operator mode is disabled. Request prepared but not sent to VX11.",
        "message": "Enable in config/copilot_operator.py to activate routing",
        "payload_ready": True,
    }
