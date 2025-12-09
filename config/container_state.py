"""
Container State Management for VX11
Proporciona lógica de estados: off, standby, active para todos los módulos.
"""

from typing import Dict, Literal
from datetime import datetime
import logging

log = logging.getLogger("vx11.container_state")

# Estados válidos
State = Literal["off", "standby", "active"]

# Registro global de estados (por módulo)
_MODULE_STATES: Dict[str, Dict] = {
    "tentaculo_link": {"state": "active", "last_changed": datetime.utcnow().isoformat()},
    "madre": {"state": "active", "last_changed": datetime.utcnow().isoformat()},
    "switch": {"state": "active", "last_changed": datetime.utcnow().isoformat()},
    "hermes": {"state": "active", "last_changed": datetime.utcnow().isoformat()},
    "hormiguero": {"state": "active", "last_changed": datetime.utcnow().isoformat()},
    "manifestator": {"state": "standby", "last_changed": datetime.utcnow().isoformat()},
    "mcp": {"state": "active", "last_changed": datetime.utcnow().isoformat()},
    "shubniggurath": {"state": "standby", "last_changed": datetime.utcnow().isoformat()},
    "spawner": {"state": "standby", "last_changed": datetime.utcnow().isoformat()},
}


def set_state(module: str, state: State) -> bool:
    """
    Cambia estado de un módulo.
    
    Args:
        module: Nombre del módulo
        state: off, standby, o active
    
    Returns:
        True si cambió, False si ya estaba en ese estado
    """
    if module not in _MODULE_STATES:
        log.warning(f"Unknown module: {module}")
        return False
    
    if state not in ("off", "standby", "active"):
        log.warning(f"Invalid state: {state}")
        return False
    
    old_state = _MODULE_STATES[module]["state"]
    _MODULE_STATES[module] = {
        "state": state,
        "last_changed": datetime.utcnow().isoformat()
    }
    log.info(f"Module {module}: {old_state} → {state}")
    return True


def get_state(module: str) -> Dict:
    """Obtiene estado actual de un módulo."""
    return _MODULE_STATES.get(module, {})


def get_all_states() -> Dict[str, Dict]:
    """Obtiene todos los estados."""
    return dict(_MODULE_STATES)


def is_active(module: str) -> bool:
    """Retorna True si módulo está active."""
    return _MODULE_STATES.get(module, {}).get("state") == "active"


def is_standby(module: str) -> bool:
    """Retorna True si módulo está standby."""
    return _MODULE_STATES.get(module, {}).get("state") == "standby"


def is_off(module: str) -> bool:
    """Retorna True si módulo está off."""
    return _MODULE_STATES.get(module, {}).get("state") == "off"


def should_process(module: str) -> bool:
    """
    Retorna True si módulo debe procesar comandos.
    Retorna False si está off o standby.
    """
    state = _MODULE_STATES.get(module, {}).get("state")
    return state == "active"


def get_active_modules() -> list:
    """Retorna lista de módulos activos."""
    return [m for m, info in _MODULE_STATES.items() if info["state"] == "active"]


def get_standby_modules() -> list:
    """Retorna lista de módulos en standby."""
    return [m for m, info in _MODULE_STATES.items() if info["state"] == "standby"]


def get_off_modules() -> list:
    """Retorna lista de módulos apagados."""
    return [m for m, info in _MODULE_STATES.items() if info["state"] == "off"]


def reset_all_states(default_state: State = "active"):
    """Resetea todos los módulos a estado default (para testing)."""
    for module in _MODULE_STATES:
        _MODULE_STATES[module] = {
            "state": default_state,
            "last_changed": datetime.utcnow().isoformat()
        }
    log.info(f"All modules reset to {default_state}")
