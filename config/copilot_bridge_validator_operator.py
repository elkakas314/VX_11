"""
COPILOT OPERATOR MODE: Bridge Validators (FASE 4)
Validadores estrictos para el puente Copilot-VX11 Operator Mode

Propósito: Implementar 5 funciones de validación que aseguran que NINGÚN
mensaje de Copilot llegue a VX11 sin pasar validaciones STRICT.

Restricción crítica: Si validate_operator_request() FALLA en cualquier punto,
el mensaje se rechaza INMEDIATAMENTE.
"""

import re
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime


# ============================================================================
# VALIDATORS (5 funciones principales)
# ============================================================================

def validate_message_length(message: str, max_length: int = 16384) -> Tuple[bool, str]:
    """
    VALIDATOR 1: Valida que el mensaje NO exceda longitud máxima
    
    Args:
        message: Contenido del mensaje
        max_length: Máximo permitido (default 16KB)
    
    Returns:
        (valid, error_msg)
    
    Rechaza si:
        - Message es None o vacío
        - Mensaje > 16 KB
        - Contiene null bytes
    """
    if not message:
        return False, "Message cannot be empty or None"
    
    if isinstance(message, str) and len(message.encode('utf-8')) > max_length:
        return False, f"Message too long: {len(message.encode('utf-8'))} > {max_length} bytes"
    
    if '\x00' in message:
        return False, "Message contains null bytes"
    
    return True, ""


def validate_metadata_format(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    VALIDATOR 2: Valida que metadata tenga estructura correcta
    
    Args:
        metadata: Dict con metadata del request
    
    Returns:
        (valid, error_list)
    
    Rechaza si:
        - Metadata no es dict
        - Faltan campos requeridos: source, timestamp, context7_version
        - source != "copilot_operator"
        - Timestamp no es ISO format
        - context7_version != "7.0"
    """
    errors = []
    
    if not isinstance(metadata, dict):
        errors.append("Metadata must be a dictionary")
        return False, errors
    
    # Check required fields
    required = ["source", "timestamp", "context7_version"]
    for field in required:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate source
    if metadata.get("source") != "copilot_operator":
        errors.append(f"Invalid source: {metadata.get('source')} (must be 'copilot_operator')")
    
    # Validate timestamp (ISO format)
    try:
        datetime.fromisoformat(metadata.get("timestamp", "").replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"Invalid timestamp format: {metadata.get('timestamp')}")
    
    # Validate context7_version
    if metadata.get("context7_version") != "7.0":
        errors.append(f"Invalid context7_version: {metadata.get('context7_version')} (must be '7.0')")
    
    return len(errors) == 0, errors


def validate_mode_flag(message_payload: Dict[str, Any]) -> Tuple[bool, str]:
    """
    VALIDATOR 3: Valida que operator mode esté correctamente indicado
    
    Args:
        message_payload: Payload completo del mensaje
    
    Returns:
        (valid, error_msg)
    
    Rechaza si:
        - No tiene campo 'mode' o 'operator_mode'
        - mode es "disabled" (debe estar habilitado para procesar)
        - mode no está en lista blanca: ["vx11_operator", "disabled"]
    """
    mode = message_payload.get("operator_mode") or message_payload.get("mode")
    
    if not mode:
        return False, "Missing operator_mode or mode flag"
    
    if mode not in ["vx11_operator", "disabled"]:
        return False, f"Invalid mode: {mode}"
    
    if mode == "disabled":
        return False, "Operator mode is disabled - cannot process requests"
    
    return True, ""


def validate_security_constraints(
    message: str, 
    blocked_actions: List[str] = None
) -> Tuple[bool, List[str]]:
    """
    VALIDATOR 4: Valida restricciones de seguridad
    
    Args:
        message: Contenido del mensaje
        blocked_actions: Lista de acciones bloqueadas
    
    Returns:
        (valid, error_list)
    
    Rechaza si:
        - Contiene indicadores shell: bash, exec, system, popen
        - Contiene rutas absolutas peligrosas: /etc/, /root/, /sys/, C:\\
        - Contiene acciones bloqueadas del parámetro blocked_actions
        - Contiene palabras clave de peligro: DROP, TRUNCATE, DELETE (si parece SQL)
        - Contiene patrones de borrado masivo (rm -rf, sudo rm)
    """
    if blocked_actions is None:
        blocked_actions = [
            "spawn_daughters", "spawn", "delete", "rm", "mv", "rmdir",
            "root", "sudo", "docker", "shell", "bash", "exec", "system", "popen",
            "drop", "truncate", "curl", "ssh", "scp", "telnet",
            "kernel", "panic", "reboot", "shutdown", "halt",
            "chmod", "chown", "chroot", "umount", "mount",
            "dd", "fdisk", "parted", "mkfs", "fsck",
            "kill", "killall", "pkill", "signal", "trap",
            "fork", "clone", "exec", "pipe", "ptrace",
            "selinux", "apparmor", "capabilities", "seccomp"
        ]
    
    errors = []
    message_lower = message.lower()
    
    # Shell indicators
    shell_patterns = [
        r'\bos\.system\(',
        r'\bsubprocess\.Popen\(',
        r'\bsubprocess\.call\(',
        r'\bshell\s*=\s*True',
        r'bash\s+-c',
        r'/bin/sh',
        r'/bin/bash',
        r'eval\s*\(',
        r'exec\s*\(',
    ]
    
    for pattern in shell_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            errors.append(f"Detected shell execution pattern: {pattern}")

    # Explicit rm -rf / or sudo rm patterns
    if "rm -rf" in message_lower or "sudo rm" in message_lower:
        errors.append("Blocked destructive command: rm -rf")
    
    # Dangerous paths
    dangerous_paths = ["/etc/", "/root/", "/sys/", "/proc/", "C:\\Windows", "C:\\"]
    for path in dangerous_paths:
        if path.lower() in message_lower:
            errors.append(f"Detected dangerous path: {path}")
    
    # Blocked actions
    for action in blocked_actions:
        if action.lower() in message_lower:
            errors.append(f"Blocked action detected: {action}")
    
    # SQL danger keywords (if looks like SQL)
    if "select" in message_lower or "from" in message_lower:
        sql_danger = ["drop table", "truncate table", "delete from"]
        for keyword in sql_danger:
            if keyword in message_lower:
                errors.append(f"Blocked SQL keyword: {keyword}")
    
    return len(errors) == 0, errors


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    VALIDATOR 5: Sanitiza payload para envío seguro
    
    Args:
        payload: Payload completo
    
    Returns:
        Payload sanitizado (copy del original con campos sensibles limpios)
    
    Operaciones:
        - Copia profunda del payload
        - Remueve tokens/secrets si existen en metadata
        - Remueve path absolutos del mensaje
        - Normaliza campos de control
        - Asegura que solo existan campos esperados
    """
    import copy
    
    sanitized = copy.deepcopy(payload)
    
    # Remove sensitive metadata fields that shouldn't go through
    sensitive_meta_fields = ["api_key", "token", "secret", "password", "auth"]
    if "metadata" in sanitized:
        for field in sensitive_meta_fields:
            if field in sanitized["metadata"]:
                del sanitized["metadata"][field]
    
    # Remove/mask absolute paths from message
    message = sanitized.get("message", "")
    
    # Mask absolute paths
    message = re.sub(r'/[a-zA-Z0-9/_\-\.]+', '/***masked_path***', message)
    message = re.sub(r'C:\\[a-zA-Z0-9\\_\-\.]+', 'C:\\***masked_path***', message)
    
    sanitized["message"] = message
    
    # Ensure only expected root-level keys exist
    allowed_keys = {
        "source", "message", "metadata", "context7", 
        "operator_mode", "mode", "role", "action"
    }
    
    payload_keys = set(sanitized.keys())
    extra_keys = payload_keys - allowed_keys
    
    for key in extra_keys:
        del sanitized[key]
    
    # Normalize control fields
    if "mode" in sanitized and "operator_mode" not in sanitized:
        sanitized["operator_mode"] = sanitized["mode"]
        del sanitized["mode"]
    
    return sanitized


# ============================================================================
# ORCHESTRATION VALIDATOR CLASS (Orquesta los 5 validadores)
# ============================================================================

class CopilotOperatorBridgeValidator:
    """
    Orquestador de validación para Copilot Operator Bridge
    
    Diseño: FAIL-FAST - si CUALQUIER validador falla, se rechaza el request
    
    Flujo:
        1. Validar longitud de mensaje
        2. Validar formato de metadata
        3. Validar modo operator
        4. Validar restricciones de seguridad
        5. Sanitizar payload
    
    Si ALGUNO falla → response con error y lista de problemas
    Si TODOS pasan → payload sanitizado listo para envío
    """
    
    def __init__(self, blocked_actions: List[str] = None):
        self.blocked_actions = blocked_actions or []
        self.validation_log = []
    
    async def validate_complete_request(
        self, 
        message: str,
        metadata: Dict[str, Any],
        payload: Dict[str, Any],
        blocked_actions: List[str] = None
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Ejecuta todas las validaciones en secuencia STRICT
        
        Args:
            message: Mensaje de usuario
            metadata: Metadata del request
            payload: Payload completo
            blocked_actions: Acciones bloqueadas (override)
        
        Returns:
            (is_valid, sanitized_payload_or_error_dict, errors_list)
        
        Ejemplo de error response:
            False, {
                "valid": False,
                "status": "validation_failed",
                "timestamp": "2024-01-15T10:30:00Z",
                "errors": ["Message too long", "Missing timestamp"]
            }, ["Message too long", "Missing timestamp"]
        """
        errors = []
        blocked = blocked_actions or self.blocked_actions
        
        # VALIDATOR 1: Message length
        valid, error = validate_message_length(message)
        if not valid:
            errors.append(error)
            self.validation_log.append(f"FAILED: Message length - {error}")
        
        # VALIDATOR 2: Metadata format
        valid, meta_errors = validate_metadata_format(metadata)
        if not valid:
            errors.extend(meta_errors)
            self.validation_log.extend([f"FAILED: Metadata format - {e}" for e in meta_errors])
        
        # VALIDATOR 3: Mode flag
        valid, error = validate_mode_flag(payload)
        if not valid:
            errors.append(error)
            self.validation_log.append(f"FAILED: Mode flag - {error}")
        
        # VALIDATOR 4: Security constraints
        valid, sec_errors = validate_security_constraints(message, blocked)
        if not valid:
            errors.extend(sec_errors)
            self.validation_log.extend([f"FAILED: Security - {e}" for e in sec_errors])
        
        # If ANY validator failed, return error response
        if errors:
            error_response = {
                "valid": False,
                "status": "validation_failed",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error_count": len(errors),
                "errors": errors
            }
            return False, error_response, errors
        
        # VALIDATOR 5: Sanitize (only if all previous passed)
        sanitized = sanitize_payload(payload)
        self.validation_log.append(f"PASSED: All validators passed. Payload sanitized.")
        
        success_response = {
            "valid": True,
            "status": "validation_passed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sanitized": True,
            "payload_size_bytes": len(json.dumps(sanitized).encode('utf-8'))
        }
        
        return True, success_response, []
    
    def get_validation_log(self) -> List[str]:
        """Retorna log de validaciones realizadas"""
        return self.validation_log.copy()
    
    def clear_log(self):
        """Limpia el log de validaciones"""
        self.validation_log.clear()


# ============================================================================
# HELPER FUNCTIONS (para testing y debugging)
# ============================================================================

def get_validator_stats() -> Dict[str, Any]:
    """Retorna estadísticas del validador"""
    return {
        "validators_count": 5,
        "validators": [
            "validate_message_length",
            "validate_metadata_format",
            "validate_mode_flag",
            "validate_security_constraints",
            "sanitize_payload"
        ],
        "strategy": "FAIL-FAST",
        "max_message_length_bytes": 16384,
        "operator_mode_required": "vx11_operator",
        "context7_version_required": "7.0"
    }


def build_test_payload(
    message: str = "Test message",
    mode: str = "vx11_operator"
) -> Dict[str, Any]:
    """Construye un payload de prueba para testing del validador"""
    return {
        "source": "copilot_operator",
        "operator_mode": mode,
        "message": message,
        "metadata": {
            "source": "copilot_operator",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "context7_version": "7.0",
            "request_id": "test-req-001"
        },
        "context7": {
            "layer1_user": {"user_id": "copilot-test"},
            "layer2_session": {"session_id": "test-session"},
            "layer3_task": {"task_id": "test-task"},
            "layer4_environment": {"os": "linux"},
            "layer5_security": {"auth_level": "operator"},
            "layer6_history": {"recent_commands": []},
            "layer7_meta": {"mode": "test"}
        }
    }
