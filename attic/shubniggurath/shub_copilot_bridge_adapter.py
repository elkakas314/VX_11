"""
Shub Copilot Bridge Adapter — Compatible con VX11 v6.2 MCP
Permite Copilot → Shub sin activar operator_mode
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json
import uuid

from shubniggurath.shub_vx11_bridge import VX11FlowAdapter, get_vx11_client


class ShubCopilotMode(str, Enum):
    """Modos de interacción Copilot→Shub"""
    DIRECT = "direct"  # Comando directo a Shub
    VIA_MCP = "via_mcp"  # A través de MCP de VX11
    VIA_MADRE = "via_madre"  # A través de orquestación Madre


class CopilotEntryPayload:
    """Payload canónico de entrada desde Copilot"""
    
    def __init__(
        self,
        user_message: str,
        require_action: bool = False,
        context: Optional[Dict] = None,
        mode: ShubCopilotMode = ShubCopilotMode.VIA_MCP,
    ):
        self.user_message = user_message
        self.require_action = require_action
        self.context = context or {}
        self.mode = mode
        self.entry_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "user_message": self.user_message,
            "require_action": self.require_action,
            "context": self.context,
            "mode": self.mode.value,
            "timestamp": self.timestamp.isoformat(),
        }


class StudioCommandParser:
    """Parser de comandos tipo studio → estructurado"""
    
    STUDIO_COMMANDS = {
        "analyze": "analyze_audio",
        "mix": "start_mixing",
        "master": "start_mastering",
        "play": "preview_track",
        "eq": "adjust_equalizer",
        "compress": "apply_compression",
        "reverb": "add_reverb",
        "help": "show_help",
    }
    
    @staticmethod
    def parse(user_message: str) -> Dict[str, Any]:
        """Parsear comando de usuario"""
        msg_lower = user_message.lower().strip()
        
        # Detectar comando
        for command, action in StudioCommandParser.STUDIO_COMMANDS.items():
            if msg_lower.startswith(command):
                args_str = msg_lower[len(command):].strip()
                return {
                    "parsed": True,
                    "command": command,
                    "action": action,
                    "raw_args": args_str,
                    "args": StudioCommandParser._parse_args(args_str),
                }
        
        return {
            "parsed": False,
            "raw_message": user_message,
        }
    
    @staticmethod
    def _parse_args(args_str: str) -> Dict[str, str]:
        """Parsear argumentos simples (key=value)"""
        args = {}
        if not args_str:
            return args
        
        for pair in args_str.split():
            if "=" in pair:
                k, v = pair.split("=", 1)
                args[k] = v
        
        return args


class ShubCopilotBridgeAdapter:
    """Adaptador Copilot→Shub (vía VX11 MCP)"""
    
    def __init__(self):
        self.vx11_client = get_vx11_client()
        self.vx11_adapter = VX11FlowAdapter(self.vx11_client)
        self.parser = StudioCommandParser()
        self.sessions: Dict[str, Dict] = {}
    
    async def handle_copilot_entry(
        self,
        payload: CopilotEntryPayload,
    ) -> Dict[str, Any]:
        """
        Manejar entrada de Copilot → Shub
        NO activa operator_mode
        """
        entry_dict = payload.to_dict()
        
        # Parsear comando
        parsed = self.parser.parse(payload.user_message)
        
        if not parsed.get("parsed"):
            # Mensaje libre → enrutar a MCP
            return await self._route_to_mcp(
                payload.user_message,
                payload.context,
                entry_dict,
            )
        
        # Comando estructura → procesar localmente o vía Madre
        command = parsed["command"]
        args = parsed["args"]
        
        if payload.mode == ShubCopilotMode.VIA_MADRE:
            return await self._route_to_madre(
                command,
                args,
                entry_dict,
            )
        else:
            return await self._process_command(
                command,
                args,
                entry_dict,
            )
    
    async def _route_to_mcp(
        self,
        message: str,
        context: Dict,
        entry_dict: Dict,
    ) -> Dict[str, Any]:
        """Enrutar a MCP de VX11"""
        result = await self.vx11_adapter.copilot_message_to_shub(
            message,
            context,
        )
        
        return {
            "status": "routed_to_mcp",
            "shub_entry_id": entry_dict["entry_id"],
            "vx11_session": result.get("session_id"),
            "response": result.get("response"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _route_to_madre(
        self,
        command: str,
        args: Dict,
        entry_dict: Dict,
    ) -> Dict[str, Any]:
        """Enrutar a Madre para orquestación"""
        task_message = f"[SHUB] Execute: {command} with args {json.dumps(args)}"
        
        messages = [
            {
                "role": "user",
                "content": task_message,
            },
        ]
        
        result = await self.vx11_adapter.shub_command_to_madre(command, args)
        
        return {
            "status": "routed_to_madre",
            "shub_entry_id": entry_dict["entry_id"],
            "command": command,
            "madre_response": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _process_command(
        self,
        command: str,
        args: Dict,
        entry_dict: Dict,
    ) -> Dict[str, Any]:
        """Procesar comando localmente en Shub"""
        response = {
            "status": "command_processed",
            "shub_entry_id": entry_dict["entry_id"],
            "command": command,
            "args": args,
            "result": {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Aquí iría lógica específica por comando
        # Ejemplo:
        if command == "analyze":
            response["result"] = {"status": "analysis_queued"}
        elif command == "mix":
            response["result"] = {"status": "mixing_queued"}
        elif command == "help":
            response["result"] = {
                "commands": list(self.parser.STUDIO_COMMANDS.keys())
            }
        else:
            response["result"] = {"status": f"unknown_command: {command}"}
        
        return response
    
    async def create_session(
        self,
        copilot_session_id: str,
    ) -> str:
        """Crear sesión Shub vinculada a Copilot"""
        shub_session_id = f"shub_{uuid.uuid4()}"
        self.sessions[shub_session_id] = {
            "copilot_session": copilot_session_id,
            "created_at": datetime.utcnow(),
            "messages": [],
        }
        return shub_session_id
    
    async def log_message(
        self,
        shub_session_id: str,
        role: str,
        content: str,
    ):
        """Registrar mensaje en sesión"""
        if shub_session_id in self.sessions:
            self.sessions[shub_session_id]["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            })


# ============================================================================
# SINGLETON
# ============================================================================

_copilot_bridge_instance: Optional[ShubCopilotBridgeAdapter] = None


def get_copilot_bridge() -> ShubCopilotBridgeAdapter:
    """Obtener instancia singleton del adaptador"""
    global _copilot_bridge_instance
    if _copilot_bridge_instance is None:
        _copilot_bridge_instance = ShubCopilotBridgeAdapter()
    return _copilot_bridge_instance


__all__ = [
    "ShubCopilotMode",
    "CopilotEntryPayload",
    "StudioCommandParser",
    "ShubCopilotBridgeAdapter",
    "get_copilot_bridge",
]
