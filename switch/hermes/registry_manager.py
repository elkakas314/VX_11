"""
Engine Registry Manager: Centraliza modelos locales, CLI, y motores remotos.
Proporciona selección inteligente de motores basada en contexto.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
import os

from config.db_schema import Engine, get_session

log = logging.getLogger("switch.hermes.registry")


class EngineRegistry:
    """Manager para registro CRUD de motores + selección inteligente."""
    
    def __init__(self, db_session=None):
        """
        Inicializa registry.
        Si db_session es None, obtiene una sesión de BD por defecto.
        """
        self.db = db_session or get_session("hermes")
        self.log = logging.getLogger("switch.hermes.registry")
    
    def register(
        self,
        name: str,
        engine_type: str,
        domain: str,
        endpoint: str,
        version: str = "latest",
        quota_tokens_per_day: int = -1,
        latency_ms: float = 0.0,
        cost_per_call: float = 0.0,
    ) -> Engine:
        """
        Registra un nuevo motor.
        
        Args:
            name: nombre único del motor (ej. "ollama-llama2", "deepseek-api", "docker")
            engine_type: "local_model" | "cli" | "remote_llm"
            domain: "reasoning" | "code" | "infrastructure" | etc.
            endpoint: URL (para remote) ó comando/path (para local/cli)
            version: versión del motor
            quota_tokens_per_day: cuota de tokens/día (-1 = ilimitado)
            latency_ms: latencia promedio en ms
            cost_per_call: costo por llamada (para remote)
        
        Returns:
            Engine: objeto registrado
        """
        # Verificar si ya existe
        existing = self.db.query(Engine).filter(Engine.name == name).first()
        if existing:
            self.log.warning(f"Engine {name} already registered")
            return existing
        
        eng = Engine(
            name=name,
            engine_type=engine_type,
            domain=domain,
            endpoint=endpoint,
            version=version,
            quota_tokens_per_day=quota_tokens_per_day,
            latency_ms=latency_ms,
            cost_per_call=cost_per_call,
            enabled=True,
            created_at=datetime.utcnow(),
        )
        self.db.add(eng)
        self.db.commit()
        self.log.info(f"registered_engine:{name}:{engine_type}:{domain}")
        return eng
    
    def list_available(
        self,
        engine_type: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> List[Engine]:
        """
        Lista motores disponibles (filtrados).
        Un motor está "disponible" si está enabled y no ha excedido cuota.
        """
        q = self.db.query(Engine).filter(Engine.enabled == True)
        
        if engine_type:
            q = q.filter(Engine.engine_type == engine_type)
        if domain:
            q = q.filter(Engine.domain == domain)
        
        engines = q.all()
        
        # Filtrar por cuota y reset si es necesario
        available = []
        for eng in engines:
            # Resetear cuota si pasó la fecha
            if eng.quota_reset_at and datetime.utcnow() > eng.quota_reset_at:
                eng.quota_used_today = 0
                eng.quota_reset_at = datetime.utcnow() + timedelta(days=1)
                self.db.commit()
            
            # Verificar si tiene cuota disponible
            if eng.quota_tokens_per_day == -1:  # Ilimitado
                available.append(eng)
            elif eng.quota_used_today < eng.quota_tokens_per_day:
                available.append(eng)
        
        return available
    
    def select_best(self, domain: str, context: Dict[str, Any]) -> Optional[Engine]:
        """
        Selecciona el mejor motor para un dominio basado en contexto.
        
        Args:
            domain: dominio de la tarea ("reasoning", "code", "infrastructure", etc.)
            context: {
                cpu_budget_mb: int,
                allow_remote: bool,
                max_latency_ms: float,
                token_budget: int,
            }
        
        Returns:
            Engine: motor seleccionado, o None si no hay candidatos.
        """
        candidates = self.list_available(domain=domain)
        
        if not candidates:
            self.log.warning(f"No available engines for domain {domain}")
            return None
        
        # Filtrar por restricciones de contexto
        if not context.get("allow_remote", False):
            # Si no se permite remote, filtrar solo locales
            candidates = [
                e for e in candidates
                if e.engine_type in ("local_model", "cli")
            ]
        
        if context.get("cpu_budget_mb") and context["cpu_budget_mb"] < 256:
            # Budget muy bajo: preferir modelos locales
            local = [e for e in candidates if e.engine_type == "local_model"]
            if local:
                candidates = local
        
        if context.get("max_latency_ms"):
            candidates = [
                e for e in candidates
                if e.latency_ms <= context["max_latency_ms"]
            ]
        
        if not candidates:
            self.log.warning(f"No engines match context constraints for {domain}")
            return None
        
        # Ordenar por latencia (preferir rápidos)
        candidates.sort(key=lambda e: e.latency_ms)
        
        return candidates[0]
    
    def use_quota(self, engine_id: int, tokens: int = 1) -> bool:
        """
        Decrementa la cuota disponible de un motor.
        
        Args:
            engine_id: ID del motor
            tokens: cantidad de tokens a consumir (default 1)
        
        Returns:
            bool: True si se pudo decrementar, False si ya no hay cuota.
        """
        eng = self.db.query(Engine).filter(Engine.id == engine_id).first()
        if not eng:
            self.log.error(f"Engine ID {engine_id} not found")
            return False
        
        # Reset si pasó la fecha
        if eng.quota_reset_at and datetime.utcnow() > eng.quota_reset_at:
            eng.quota_used_today = 0
            eng.quota_reset_at = datetime.utcnow() + timedelta(days=1)
        
        # Verificar cuota
        if eng.quota_tokens_per_day != -1:
            if eng.quota_used_today + tokens > eng.quota_tokens_per_day:
                self.log.warning(f"Engine {eng.name} quota exceeded")
                return False
        
        eng.quota_used_today += tokens
        eng.last_used = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def get_engine(self, engine_id: int) -> Optional[Engine]:
        """Obtiene un motor por ID."""
        return self.db.query(Engine).filter(Engine.id == engine_id).first()
    
    def get_engine_by_name(self, name: str) -> Optional[Engine]:
        """Obtiene un motor por nombre."""
        return self.db.query(Engine).filter(Engine.name == name).first()
    
    def disable_engine(self, engine_id: int):
        """Deshabilita un motor (por problemas, mantenimiento, etc.)."""
        eng = self.db.query(Engine).filter(Engine.id == engine_id).first()
        if eng:
            eng.enabled = False
            self.db.commit()
            self.log.info(f"disabled_engine:{eng.name}")
