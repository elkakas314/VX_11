"""
MCP v2: Capa Conversacional Integrada

Características:
- Interfaz conversacional para Copilot + Actions
- Enrutamiento inteligente a Madre/Switch
- Respuestas enriquecidas con contexto
- Sesiones persistentes
- Integración completa con VX11 v4
"""

from fastapi import FastAPI, Depends, HTTPException, WebSocket, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import asyncio
import logging
import json
from datetime import datetime
import httpx
import requests

from config.settings import settings
from config.db_schema import get_session, Context
from config.deepseek import call_deepseek_reasoner_async

log = logging.getLogger("vx11.mcp_v2")
app = FastAPI(title="VX11 MCP v2 Conversational")

# =========== MODELS ===========

class ConversationTurn(BaseModel):
    """Un turno de conversación."""
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPChatRequest(BaseModel):
    """Request para chat MCP."""
    session_id: Optional[str] = None
    user_message: str
    context: Optional[Dict[str, Any]] = None
    require_action: bool = False  # Si True, MCP busca realizar acciones (switch, spawn, etc)


class MCPChatResponse(BaseModel):
    """Response de chat MCP."""
    session_id: str
    response: str
    actions_taken: List[Dict[str, Any]]
    reasoning: Optional[str] = None
    confidence: float
    timestamp: datetime


class ConversationSession(BaseModel):
    """Session de conversación."""
    session_id: str
    created_at: datetime
    last_interaction: datetime
    turns_count: int
    history: List[ConversationTurn]


# =========== MCP V2 CORE ===========

class MCPEngine:
    """Motor conversacional MCP v2."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Mapeos de intención
        self.action_keywords = {
            "spawn": ["execute", "run", "launch", "crear proceso"],
            "route": ["ask", "query", "send", "route", "enviar"],
            "scan": ["scan", "find", "discover", "buscar"],
            "repair": ["fix", "repair", "error", "bug"],
        }
    
    async def process_message(self, req: MCPChatRequest) -> MCPChatResponse:
        """Procesar mensaje del usuario."""
        
        # 1. Obtener o crear sesión
        session_id = req.session_id or str(uuid.uuid4())
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.utcnow(),
                "turns": [],
            }
        
        session = self.sessions[session_id]
        
        # 2. Detectar intención
        intent = await self._detect_intent(req.user_message, req.context or {})
        
        # 3. Generar respuesta base con R1 si es necesario
        base_response = await self._generate_response(
            req.user_message,
            intent,
            session["turns"],
        )
        
        # 4. Si require_action, ejecutar acciones
        actions_taken = []
        if req.require_action and intent["action"] != "none":
            actions_taken = await self._execute_action(intent, req.user_message, req.context or {})
        
        # 5. Enriquecer respuesta con resultados de acciones
        final_response = await self._enrich_response(base_response, actions_taken)
        
        # 6. Guardar turno
        session["turns"].append({
            "role": "user",
            "content": req.user_message,
            "timestamp": datetime.utcnow(),
        })
        session["turns"].append({
            "role": "assistant",
            "content": final_response,
            "timestamp": datetime.utcnow(),
        })
        
        # 7. Guardar en BD
        await self._save_context(session_id, req.user_message, final_response)
        
        return MCPChatResponse(
            session_id=session_id,
            response=final_response,
            actions_taken=actions_taken,
            reasoning=base_response,
            confidence=intent.get("confidence", 0.5),
            timestamp=datetime.utcnow(),
        )
    
    async def _detect_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detectar intención del usuario."""
        message_lower = message.lower()
        
        # Buscar palabras clave
        detected_action = "none"
        confidence = 0.5
        
        for action, keywords in self.action_keywords.items():
            for kw in keywords:
                if kw in message_lower:
                    detected_action = action
                    confidence = min(0.9, 0.5 + len([k for k in keywords if k in message_lower]) * 0.1)
                    break
        
        return {
            "action": detected_action,
            "confidence": confidence,
            "message": message,
            "context": context,
        }
    
    async def _generate_response(self, message: str, intent: Dict[str, Any], history: List[Dict[str, Any]]) -> str:
        """Generar respuesta con contexto."""
        
        # Construir prompt con historial
        history_text = ""
        if history:
            history_text = "\n".join([
                f"{t['role'].upper()}: {t['content'][:100]}"
                for t in history[-4:]  # Últimos 4 turnos
            ])
        
        reasoning = await call_deepseek_reasoner_async(
            prompt=f"""
Eres un asistente IA conversacional (MCP) que forma parte de VX11, un orquestador autónomo.

HISTORIAL:
{history_text}

USUARIO: {message}
INTENCIÓN DETECTADA: {intent['action']} (confianza: {intent['confidence']:.1%})

Genera una respuesta conversacional que:
1. Responda al usuario de forma natural
2. Reconozca la intención detectada
3. Si es apropiado, explica qué acciones se van a tomar
4. Ofrece opciones o aclaraciones si es necesario

Responde en una frase o dos, de forma concisa y amigable.
""",
            max_tokens=300,
        )
        
        return reasoning.get("reasoning", "Entendido.")
    
    async def _execute_action(self, intent: Dict[str, Any], message: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ejecutar acción según intención."""
        action = intent["action"]
        results = []
        
        try:
            if action == "spawn":
                # Delegar a spawner
                result = await self._action_spawn(message, context)
                results.append(result)
            
            elif action == "route":
                # Delegar a switch (routing IA)
                result = await self._action_route(message, context)
                results.append(result)
            
            elif action == "scan":
                # Delegar a hermes
                result = await self._action_scan(message, context)
                results.append(result)
            
            elif action == "repair":
                # Delegar a manifestator
                result = await self._action_repair(message, context)
                results.append(result)
        
        except Exception as e:
            log.error(f"Action execution error: {e}")
            results.append({
                "action": action,
                "status": "error",
                "error": str(e),
            })
        
        return results
    
    async def _action_spawn(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Acción: Spawn."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"http://127.0.0.1:{settings.PORTS.get('spawner', 52114)}/spawn",
                    json={
                        "name": "mcp-spawned",
                        "command": "echo",
                        "args": ["Executed from MCP"],
                        "timeout_seconds": 30,
                        "max_memory_mb": 256,
                    },
                    timeout=10.0,
                )
                data = resp.json() if resp.status_code == 200 else {"error": resp.text}
                return {
                    "action": "spawn",
                    "status": "executed",
                    "result": data.get("spawn_id", "unknown"),
                }
        except Exception as e:
            return {
                "action": "spawn",
                "status": "failed",
                "error": str(e),
            }
    
    async def _action_route(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Acción: Route (switch)."""
        try:
            # Delegar al switch mediante payload simple y función sync de compatibilidad
            action_payload = {
                "source": "mcp",
                "type": "spawn",
                "command": message,
            }
            result = _delegate_to_switch(action_payload)

            # Si el mensaje sugiere audio o hermes, intentar llamar a Hermes /route
            hermes_out = None
            ant_out = None
            try:
                lower = (message or "").lower()
                if "audio" in lower or "hermes" in lower:
                    try:
                        async with httpx.AsyncClient() as client:
                            hermes_url = f"http://127.0.0.1:{settings.PORTS.get('hermes', settings.hermes_port)}/route"
                            resp = await client.post(
                                hermes_url,
                                json={"prompt": message, "task_type": "chat"},
                                timeout=10.0,
                            )
                            hermes_out = resp.json() if resp.status_code == 200 else {"error": resp.text}
                    except Exception as e:
                        hermes_out = {"error": str(e)}

                    # Intentar notificar a una hormiga 'ant-test' si existe (no crítico)
                    try:
                        async with httpx.AsyncClient() as client:
                            ant_check = await client.get(
                                f"http://127.0.0.1:{settings.PORTS.get('hormiguero', settings.hormiguero_port)}/ant/ant-test",
                                timeout=3.0,
                            )
                            if ant_check.status_code == 200:
                                run_resp = await client.post(
                                    f"http://127.0.0.1:{settings.PORTS.get('hormiguero', settings.hormiguero_port)}/ant/ant-test/run",
                                    json={"task": message},
                                    timeout=5.0,
                                )
                                ant_out = run_resp.json() if run_resp.status_code == 200 else {"error": "ant_run_failed"}
                    except Exception:
                        ant_out = None

            except Exception:
                # No bloquear la ruta principal por fallos en integraciones
                hermes_out = hermes_out or {"error": "hermes_integration_failed"}

            combined = {
                "switch": result,
                "hermes": hermes_out,
                "ant": ant_out,
            }

            # Prefer devolver la estructura enriquecida
            return {
                "action": "route",
                "status": "executed",
                "result": combined,
            }
        except Exception as e:
            return {
                "action": "route",
                "status": "failed",
                "error": str(e),
            }
    
    async def _action_scan(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Acción: Scan (hermes)."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"http://127.0.0.1:{settings.PORTS.get('hermes', 52114)}/hermes/full-scan",
                    json={"context": context},
                    timeout=30.0,
                )
                data = resp.json() if resp.status_code == 200 else {"error": resp.text}
                return {
                    "action": "scan",
                    "status": "executed",
                    "result": data,
                }
        except Exception as e:
            return {
                "action": "scan",
                "status": "failed",
                "error": str(e),
            }
    
    async def _action_repair(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Acción: Repair (manifestator)."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"http://127.0.0.1:{settings.PORTS.get('manifestator', 52115)}/manifestator/drift/audit",
                    json={"include_tests": True},
                    timeout=30.0,
                )
                data = resp.json() if resp.status_code == 200 else {"error": resp.text}
                return {
                    "action": "repair",
                    "status": "executed",
                    "drift_items": data.get("drift_items", 0),
                }
        except Exception as e:
            return {
                "action": "repair",
                "status": "failed",
                "error": str(e),
            }
    
    async def _enrich_response(self, base_response: str, actions: List[Dict[str, Any]]) -> str:
        """Enriquecer respuesta con resultados de acciones."""
        if not actions:
            return base_response
        
        actions_summary = "\n".join([
            f"- {a['action']}: {a['status']}"
            for a in actions
        ])
        
        return f"{base_response}\n\nAcciones ejecutadas:\n{actions_summary}"
    
    async def _save_context(self, session_id: str, user_msg: str, assistant_msg: str):
        """Guardar contexto en BD."""
        try:
            ctx = Context(
                session_id=session_id,
                user_input=user_msg,
                madre_response=assistant_msg,
                timestamp=datetime.utcnow(),
            )
            self.db_session.add(ctx)
            self.db_session.commit()
        except Exception as e:
            log.error(f"Context save error: {e}")
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Obtener sesión."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return ConversationSession(
            session_id=session_id,
            created_at=session["created_at"],
            last_interaction=session.get("last_interaction", session["created_at"]),
            turns_count=len(session["turns"]),
            history=[ConversationTurn(**t) for t in session["turns"]],
        )


# =========== ENDPOINTS ===========

_MCP_ENGINE: Optional[MCPEngine] = None


def get_mcp_engine(db_session = Depends(lambda: get_session("madre"))):
    """Dependency para MCP engine."""
    global _MCP_ENGINE
    if _MCP_ENGINE is None:
        _MCP_ENGINE = MCPEngine(db_session)
    return _MCP_ENGINE


@app.post("/mcp/chat")
async def mcp_chat(
    request: Request,
    engine: MCPEngine = Depends(get_mcp_engine),
) -> MCPChatResponse:
    """Chat endpoint principal de MCP.

    Compatibilidad: acepta `user_message` o `message` como alias.
    """
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="invalid_json")

    msg = data.get("user_message") or data.get("message")
    if not msg:
        raise HTTPException(status_code=400, detail="missing_message")

    req_obj = MCPChatRequest(
        session_id=data.get("session_id"),
        user_message=msg,
        context=data.get("context"),
        require_action=data.get("require_action", False),
    )

    # Si el mensaje menciona 'tarea' o 'task', crear una task automática en Madre (no crítico)
    try:
        lower_msg = (msg or "").lower()
        if "tarea" in lower_msg or "task" in lower_msg:
            try:
                from uuid import uuid4
                from config.settings import settings
                auto_name = "auto-" + uuid4().hex[:8]
                madre_port = settings.PORTS.get("madre", 8001)
                # Llamada no crítica; si falla, se registra y se continúa
                requests.post(
                    f"http://127.0.0.1:{madre_port}/task",
                    json={
                        "name": auto_name,
                        "module": "madre",
                        "action": "chat",
                        "payload": {"message": msg},
                    },
                    timeout=3,
                )
                write_log("mcp", f"auto_task_created:{auto_name}")
            except Exception as _e:
                log.error(f"auto_task_failed:{_e}")
    except Exception:
        # No bloquear por errores en esta detección
        pass
    try:
        return await engine.process_message(req_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _delegate_to_switch(payload: dict) -> dict:
    """Compat shim synchronous hacia switch desde MCP."""
    try:
        from config.settings import settings
        switch_port = settings.PORTS.get("switch", 8002)
        r = requests.post(f"http://127.0.0.1:{switch_port}/from_mcp", json=payload, timeout=3)
        try:
            return r.json()
        except Exception:
            return {"error": "invalid_response", "text": r.text}
    except Exception:
        return {"error": "switch_unreachable"}


@app.get("/mcp/session/{session_id}")
async def get_mcp_session(
    session_id: str,
    engine: MCPEngine = Depends(get_mcp_engine),
) -> ConversationSession:
    """Obtener sesión de conversación."""
    session = await engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check."""
    return {"status": "ok", "module": "mcp_v2"}


@app.post("/control")
async def control(action: str = "status") -> Dict[str, Any]:
    """Control actions."""
    return {
        "action": action,
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=52116, reload=True)
