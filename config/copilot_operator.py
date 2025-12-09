"""
Copilot Operator Mode v6.2
Estructura de control para operador Copilot en VX11
ESTADO: DESACTIVADO (disabled) - preparado pero inactivo
"""

# ========== OPERATOR MODE STATUS ==========
# Cambiar a "vx11_operator" para activar en el futuro
operator_mode = "disabled"

# Estados válidos
OPERATOR_MODES = {
    "disabled": {
        "description": "Modo desactivado - Copilot NO interactúa con VX11",
        "routing": "skip_bridge",
        "allowed_actions": 0,
    },
    "vx11_operator": {
        "description": "Modo operador activo - Copilot puede consultar VX11 de forma limitada",
        "routing": "validate_and_route",
        "allowed_actions": 50,
    },
}


# ========== ALLOWED ACTIONS (cuando se active) ==========
allowed_actions = [
    # Query operations (read-only)
    "vx11/status",
    "vx11/chat",
    "switch/query",
    "hermes/list-engines",
    "madre/get-task",
    "hormiguero/ga/summary",
    
    # Safe state changes
    "switch/pheromone/update",
    "hormiguero/ga/optimize",
    
    # Validation
    "vx11/validate/copilot-bridge",
]


# ========== BLOCKED ACTIONS (siempre bloqueado) ==========
blocked_actions = [
    # Dangerous process operations
    "spawn_daughters",
    "spawn",
    "exec",
    "system",
    "shell",
    "bash",
    "sh",
    "cmd",
    "powershell",
    
    # File operations
    "delete",
    "rm",
    "mv",
    "cp",
    "rename",
    "chmod",
    "chown",
    
    # System operations
    "root",
    "sudo",
    "reboot",
    "shutdown",
    "systemctl",
    "docker",
    "kubectl",
    
    # Database operations
    "drop",
    "truncate",
    "alter",
    "grant",
    "revoke",
    
    # Network operations
    "curl",
    "wget",
    "nc",
    "nmap",
    "ssh",
    "telnet",
]


# ========== ROLE-BASED ACCESS ==========
class OperatorRoles:
    """Definición de roles para operator mode"""
    
    ROLES = {
        "viewer": {
            "description": "Solo lectura",
            "can_read": True,
            "can_write": False,
            "max_concurrent_ops": 1,
            "rate_limit_per_min": 30,
        },
        "operator": {
            "description": "Lectura + acciones limitadas",
            "can_read": True,
            "can_write": True,
            "max_concurrent_ops": 5,
            "rate_limit_per_min": 100,
        },
        "admin": {
            "description": "Acceso completo (no recomendado para Copilot)",
            "can_read": True,
            "can_write": True,
            "max_concurrent_ops": 20,
            "rate_limit_per_min": 300,
        },
    }
    
    @staticmethod
    def validate_role(role: str) -> bool:
        """Valida que el role sea válido"""
        return role in OperatorRoles.ROLES
    
    @staticmethod
    def get_role_config(role: str) -> dict:
        """Retorna configuración del role"""
        return OperatorRoles.ROLES.get(role, {})


# ========== MODE SWITCH MANAGEMENT ==========
class ModeSwitch:
    """Gestor del flag de activación/desactivación"""
    
    def __init__(self, mode: str = "disabled"):
        self.current_mode = mode
        self.history = []
        self._validate_mode()
    
    def _validate_mode(self):
        """Valida que el modo sea válido"""
        if self.current_mode not in OPERATOR_MODES:
            raise ValueError(f"Invalid mode: {self.current_mode}. Valid: {list(OPERATOR_MODES.keys())}")
    
    def switch_to(self, new_mode: str) -> bool:
        """Cambia a nuevo modo (solo estructura, no implementa)"""
        if new_mode not in OPERATOR_MODES:
            return False
        
        self.history.append({
            "from": self.current_mode,
            "to": new_mode,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        })
        
        self.current_mode = new_mode
        return True
    
    def get_current_mode(self) -> str:
        """Retorna modo actual"""
        return self.current_mode
    
    def is_active(self) -> bool:
        """Retorna True si operator mode está activo"""
        return self.current_mode == "vx11_operator"
    
    def get_status(self) -> dict:
        """Retorna estado actual"""
        return {
            "current_mode": self.current_mode,
            "is_active": self.is_active(),
            "mode_config": OPERATOR_MODES.get(self.current_mode, {}),
            "history_count": len(self.history),
        }


# ========== TOKEN MANAGEMENT ==========
class OperatorTokenReader:
    """Lectura segura de tokens para operator mode"""
    
    def __init__(self, env_file: str = "tokens.env"):
        # File-based tokens deprecated; kept for signature compatibility
        self.env_file = env_file
        self._tokens = {}
        self._load_tokens()
    
    def _load_tokens(self):
        """Carga tokens desde entorno (fallback a archivos solo si está permitido)"""
        try:
            from config.tokens import load_tokens, get_token
            load_tokens()
            
            # Solo cargar tokens necesarios para validación
            self._tokens = {
                "vx11_gateway": get_token("VX11_GATEWAY_TOKEN") or "",
                "copilot_session": get_token("COPILOT_SESSION_TOKEN") or "",
            }
        except:
            # En caso de fallo, continuar con tokens vacíos
            self._tokens = {}
    
    def validate_token(self, token: str, token_type: str = "copilot_session") -> bool:
        """Valida token (no expone valor real)"""
        if not token or not isinstance(token, str):
            return False
        
        # Nunca comparar directamente, solo validar formato
        return len(token) > 8 and all(c.isalnum() or c in "-_" for c in token)
    
    def get_token_safe(self, token_type: str) -> str:
        """Retorna token solo si existe (no en modo disabled)"""
        if operator_mode == "disabled":
            return ""
        
        return self._tokens.get(token_type, "")


# ========== GLOBAL STATE ==========
_mode_switch = ModeSwitch(operator_mode)
_token_reader = OperatorTokenReader()


# ========== PUBLIC API ==========
def get_operator_status() -> dict:
    """Retorna estado del operador"""
    return {
        "mode": _mode_switch.get_current_mode(),
        "is_active": _mode_switch.is_active(),
        "allowed_actions": len(allowed_actions) if _mode_switch.is_active() else 0,
        "blocked_actions": len(blocked_actions),
    }


def is_operator_active() -> bool:
    """Quick check si operador está activo"""
    return _mode_switch.is_active()


def validate_operator_action(action: str) -> bool:
    """Valida si una acción está permitida"""
    # Si está desactivado, rechazar todo
    if not _mode_switch.is_active():
        return False
    
    # Verificar acciones bloqueadas primero
    if any(blocked in action.lower() for blocked in blocked_actions):
        return False
    
    # Verificar acciones permitidas
    return any(allowed in action for allowed in allowed_actions)


def get_allowed_actions() -> list:
    """Retorna lista de acciones permitidas"""
    if not _mode_switch.is_active():
        return []
    return allowed_actions.copy()


def get_blocked_actions() -> list:
    """Retorna lista de acciones bloqueadas"""
    return blocked_actions.copy()
