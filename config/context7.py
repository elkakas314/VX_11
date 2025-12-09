"""
Context-7 Generator y Validator - Utilidad canónica para VX11 v6.2
Generación automática de context-7 desde cualquier módulo
"""

import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
import os


class Context7Generator:
    """Generador canónico de context-7 para VX11"""
    
    @staticmethod
    def generate(
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        channel: str = "http",
        task_type: str = "query",
        auth_level: str = "trusted",
        sandbox: bool = True,
        mode: str = "balanced"
    ) -> Dict[str, Any]:
        """Genera context-7 completo y válido"""
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        context7 = {
            "layer1_user": {
                "id": user_id,
                "profile": "power_user",
                "preferences": {
                    "language": "es",
                    "verbosity": "low",
                    "humor": "dry"
                }
            },
            "layer2_session": {
                "session_id": session_id,
                "channel": channel,
                "start_time": datetime.utcnow().isoformat()
            },
            "layer3_task": {
                "task_id": str(uuid.uuid4()),
                "type": task_type,
                "deadline_ms": 10000,
                "priority": "normal"
            },
            "layer4_environment": {
                "os": "ubuntu",
                "vx_version": "vx11.6.2",
                "resources": {
                    "cpu_load": 0.3,
                    "ram_free_mb": 2000,
                    "disk_free_mb": 50000
                }
            },
            "layer5_security": {
                "auth_level": auth_level,
                "sandbox": sandbox,
                "allowed_tools": ["switch.hermes.cli.safe", "switch.hermes.playwright.readonly"],
                "ip_whitelist": ["127.0.0.1"]
            },
            "layer6_history": {
                "recent_commands": [],
                "last_outcome": "success",
                "penalties": {},
                "successes_count": 0
            },
            "layer7_meta": {
                "explain_mode": False,
                "debug_trace": False,
                "telemetry": True,
                "mode": mode,
                "trace_id": str(uuid.uuid4())
            }
        }
        
        return context7
    
    @staticmethod
    def validate(context7: Dict[str, Any]) -> bool:
        """Valida que context-7 sea completo y válido"""
        required_layers = [
            "layer1_user", "layer2_session", "layer3_task",
            "layer4_environment", "layer5_security", "layer6_history", "layer7_meta"
        ]
        
        for layer in required_layers:
            if layer not in context7:
                return False
        
        return True
    
    @staticmethod
    def merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge dos context-7 (override prevalece)"""
        import copy
        merged = copy.deepcopy(base)
        
        if not isinstance(override, dict):
            return merged
        
        for layer in override:
            if layer in merged and isinstance(override[layer], dict):
                merged[layer].update(override[layer])
            else:
                merged[layer] = override[layer]
        
        return merged


# Helper global para uso rápido
def get_default_context7(session_id: str = None) -> Dict[str, Any]:
    """Retorna context-7 por defecto"""
    return Context7Generator.generate(session_id=session_id)


def validate_context7(ctx: Dict[str, Any]) -> bool:
    """Valida context-7"""
    return Context7Generator.validate(ctx)
