"""
Factory para crear endpoints de control de estado (P&P compatible)
Se integra en todos los módulos vía module_template.py
"""

from fastapi import APIRouter
from typing import Dict, Any, Literal
from datetime import datetime
from config.container_state import set_state, get_state, get_all_states


def create_state_router(module_name: str) -> APIRouter:
    """
    Crea un router con endpoints de control de estado.
    
    Args:
        module_name: Nombre del módulo (gateway, madre, switch, etc)
    
    Returns:
        APIRouter con endpoints /control/state y /control/get_state
    """
    router = APIRouter(prefix="/control", tags=[f"{module_name}-control"])
    
    @router.post("/state")
    async def control_state(request: Dict[str, Any]):
        """
        Controla el estado del módulo (off/standby/active).
        
        Body:
            {
              "state": "active" | "standby" | "off"
            }
        """
        new_state = request.get("state")
        
        if new_state not in ("off", "standby", "active"):
            return {
                "status": "error",
                "message": f"Invalid state: {new_state}. Must be: off, standby, active"
            }
        
        changed = set_state(module_name, new_state)
        
        return {
            "status": "ok",
            "module": module_name,
            "state": new_state,
            "changed": changed,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @router.get("/get_state")
    async def get_current_state():
        """
        Obtiene estado actual del módulo.
        """
        state_info = get_state(module_name)
        
        return {
            "status": "ok",
            "module": module_name,
            "state": state_info.get("state", "unknown"),
            "last_changed": state_info.get("last_changed"),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @router.get("/all_states")
    async def get_all_module_states():
        """
        Obtiene estado de TODOS los módulos (para orquestación).
        """
        all_states = get_all_states()
        
        return {
            "status": "ok",
            "states": all_states,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    return router
