"""
VX11 DSL Parser — Convertir lenguaje natural a comandos VX11.

EJEMPLO:
  Input:  "crear tarea audio con archivo.mp3"
  Output: VX11::TASK create type="audio" file="archivo.mp3"

STATUS: Stub para FASE 3 - Features Autónomas
"""

import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class VX11DSLParser:
    """Parseador de DSL natural a comandos VX11."""
    
    def __init__(self):
        self.patterns = {
            "crear_tarea": r"crear\s+(?:tarea|task)\s+(\w+)",
            "con_archivo": r"con\s+(?:archivo|file)\s+(.+)",
            "parametros": r"(?:con|with)\s+([\w=,\s]+)",
        }
    
    def parse(self, input_text: str) -> Optional[Dict[str, Any]]:
        """Parse DSL natural a estructura de comando.
        
        Args:
            input_text: Comando natural en DSL VX11
            
        Returns:
            Dict con estructura de comando o None si falla parsing
        """
        logger.info(f"Parsing DSL: {input_text}")
        
        # Detectar tipo de tarea
        task_match = re.search(self.patterns["crear_tarea"], input_text)
        if not task_match:
            logger.warning(f"No VX11 task detected in: {input_text}")
            return None
        
        task_type = task_match.group(1)  # e.g., "audio"
        
        # Construir comando base
        command = {
            "vx11_command": "TASK.create",
            "type": task_type,
            "parameters": {},
        }
        
        # Extraer archivo si existe
        file_match = re.search(self.patterns["con_archivo"], input_text)
        if file_match:
            command["parameters"]["file"] = file_match.group(1)
        
        # Extraer otros parámetros
        param_match = re.search(self.patterns["parametros"], input_text)
        if param_match:
            params_str = param_match.group(1)
            # Parse key=value pairs
            for param in params_str.split(","):
                if "=" in param:
                    key, val = param.strip().split("=", 1)
                    command["parameters"][key.strip()] = val.strip()
        
        logger.info(f"Parsed command: {command}")
        return command
    
    def format_command(self, cmd: Dict[str, Any]) -> str:
        """Convierte estructura de comando a string VX11.
        
        Example output:
            VX11::TASK create type="audio" file="song.mp3" normalize="true"
        """
        if not cmd:
            return ""
        
        vx11_cmd = cmd.get("vx11_command", "UNKNOWN")
        type_val = cmd.get("type", "")
        params = cmd.get("parameters", {})
        
        param_str = " ".join([f'{k}="{v}"' for k, v in params.items()])
        
        if param_str:
            return f'VX11::{vx11_cmd} type="{type_val}" {param_str}'
        else:
            return f'VX11::{vx11_cmd} type="{type_val}"'
