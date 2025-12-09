"""
SmartRouter v5: Engine selection and routing via HERMES registry.
Maps user queries to optimal engine (local_model, cli, remote_llm) with quota management.
"""

import logging
import asyncio
import httpx
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from config.settings import settings

log = logging.getLogger("vx11.switch.router_v5")

# VX11 v6.7 – hybrid slots definition (non-breaking defaults)
SLOT_PRIORITIES = [
    "task_local",
    "tech_local",
    "music_local",
    "cli_remote",
]
QUEUE_PRIORITY = ["shub", "operator", "madre", "hijas", "default"]


class SmartRouter:
    """
    Routes queries to best engine using HERMES registry.
    - Queries HERMES /hermes/select-engine to pick best engine
    - Routes to appropriate executor (local_model stub, CLI stub, remote_llm)
    - Updates quota via HERMES /hermes/use-quota
    - Returns structured result with cost estimation and reasoning
    """
    
    def __init__(self, hermes_endpoint: str = None):
        # Use settings if no endpoint provided
        if hermes_endpoint is None:
            hermes_port = settings.PORTS.get("hermes", 8003)
            hermes_endpoint = f"http://127.0.0.1:{hermes_port}"
        self.hermes_endpoint = hermes_endpoint
        self.client = None
    
    async def _get_client(self):
        """Lazy-init httpx AsyncClient."""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def close(self):
        """Cleanup HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def _map_domain(self, query: str) -> str:
        """
        Map query intent to domain:
        - Contains "reason" or "think" → "reasoning"
        - Contains "code" → "code_generation"
        - Contains "docker|kubectl|git|curl" → "infrastructure"
        - Default → "general"
        """
        query_lower = query.lower()
        
        if any(w in query_lower for w in ["reason", "think", "analyze", "explain"]):
            return "reasoning"
        elif any(w in query_lower for w in ["code", "write", "implement", "function"]):
            return "code_generation"
        elif any(w in query_lower for w in ["docker", "kubectl", "git", "curl", "bash", "script"]):
            return "infrastructure"
        else:
            return "general"

    # VX11 v6.7 – hybrid slot selector (lightweight, non-blocking)
    def _select_slot(self, intent_type: str, context: Dict[str, Any]) -> str:
        intent_type = (intent_type or "").lower()
        if intent_type in ("task", "deploy", "ops"):
            return "task_local"
        if intent_type in ("audio", "mix", "music", "shub"):
            return "music_local"
        if intent_type in ("chat", "code", "tech"):
            return "tech_local"
        if context.get("force_cli"):
            return "cli_remote"
        return SLOT_PRIORITIES[0]

    def _queue_priority_score(self, source: str) -> int:
        source = (source or "default").lower()
        if source in QUEUE_PRIORITY:
            return QUEUE_PRIORITY.index(source)
        return len(QUEUE_PRIORITY)
    
    async def _call_hermes_select(self, domain: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call HERMES /hermes/select-engine to pick best engine."""
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.hermes_endpoint}/hermes/select-engine",
                json={
                    "domain": domain,
                    "context": context,
                },
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                log.warning(f"hermes_select_failed:status={resp.status_code}")
                return None
        except Exception as e:
            log.error(f"hermes_select_error:{e}")
            return None
    
    async def _call_hermes_quota(self, engine_id: int, tokens: int = 1) -> bool:
        """Call HERMES /hermes/use-quota to decrement quota."""
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{self.hermes_endpoint}/hermes/use-quota",
                json={
                    "engine_id": engine_id,
                    "tokens": tokens,
                },
            )
            return resp.status_code == 200
        except Exception as e:
            log.error(f"hermes_quota_error:{e}")
            return False
    
    async def _execute_local_model(self, engine_name: str, endpoint: str, query: str) -> str:
        """Execute query on local model (ollama stub)."""
        # Stub: in production, would call endpoint (e.g., http://localhost:11434/api/generate)
        log.info(f"execute_local_model:engine={engine_name}:endpoint={endpoint}")
        # For now, return mock reasoning response
        return f"[{engine_name}] Analyzed query: {query[:50]}..."
    
    async def _execute_cli(self, engine_name: str, endpoint: str, query: str) -> str:
        """Execute CLI command (docker/kubectl/git/curl stub)."""
        # Stub: in production, would parse query and execute CLI
        log.info(f"execute_cli:engine={engine_name}:endpoint={endpoint}")
        return f"[{engine_name}] CLI stub: {query[:50]}... (not executed)"
    
    async def _execute_remote_llm(self, engine_name: str, endpoint: str, query: str) -> str:
        """Execute query on remote LLM (DeepSeek stub)."""
        # Stub: in production, would call DeepSeek or OpenRouter with API key
        log.info(f"execute_remote_llm:engine={engine_name}:endpoint={endpoint}")
        return f"[{engine_name}] Remote LLM stub: {query[:50]}... (not called)"
    
    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Route query to best engine.
        
        Args:
            query: User query/prompt
            context: Optional context dict with cpu_budget_mb, allow_remote, max_latency_ms, token_budget
        
        Returns:
            {
                "engine_id": int,
                "engine_name": str,
                "engine_type": str,  # "local_model" | "cli" | "remote_llm"
                "domain": str,
                "answer": str,
                "cost_estimate": float,
                "reasoning": str,
                "timestamp": str,
            }
        """
        context = context or {}
        domain = await self._map_domain(query)
        intent_type = context.get("intent_type") or context.get("type") or ""
        slot_selected = self._select_slot(intent_type, context)
        queue_score = self._queue_priority_score(context.get("source"))
        # VX11 v6.7: prewarm hint only (non-blocking)
        prewarm_hint = SLOT_PRIORITIES[(SLOT_PRIORITIES.index(slot_selected) + 1) % len(SLOT_PRIORITIES)] if SLOT_PRIORITIES else None

        # Step 1: Select best engine from HERMES
        engine_info = await self._call_hermes_select(domain, context)
        if not engine_info:
            return {
                "engine_id": -1,
                "engine_name": "fallback_local",
                "engine_type": "unknown",
                "domain": domain,
                "answer": f"No engine available for domain: {domain}",
                "cost_estimate": 0.0,
                "reasoning": "fallback_no_engines",
                "timestamp": datetime.utcnow().isoformat(),
                "slot": slot_selected,
                "queue_priority": queue_score,
            }
        
        engine_id = engine_info.get("engine_id")
        engine_name = engine_info.get("engine_name")
        engine_type = engine_info.get("engine_type")
        endpoint = engine_info.get("endpoint", "")
        cost_per_call = engine_info.get("cost_per_call", 0.0)
        
        # Step 2: Execute on chosen engine
        try:
            if engine_type == "local_model":
                answer = await self._execute_local_model(engine_name, endpoint, query)
            elif engine_type == "cli":
                answer = await self._execute_cli(engine_name, endpoint, query)
            elif engine_type == "remote_llm":
                answer = await self._execute_remote_llm(engine_name, endpoint, query)
            else:
                answer = f"Unknown engine type: {engine_type}"
        except Exception as e:
            log.error(f"execution_error:engine={engine_name}:{e}")
            answer = f"Execution error: {str(e)}"
        
        # Step 3: Update quota in HERMES
        # Estimate tokens (rough heuristic: query length / 4 + answer length / 4)
        estimated_tokens = (len(query) + len(answer)) // 4 or 1
        quota_ok = await self._call_hermes_quota(engine_id, estimated_tokens)
        
        return {
            "engine_id": engine_id,
            "engine_name": engine_name,
            "engine_type": engine_type,
            "domain": domain,
            "answer": answer,
            "cost_estimate": cost_per_call,
            "tokens_used": estimated_tokens,
            "quota_ok": quota_ok,
            "reasoning": f"selected_best_engine:domain={domain}:type={engine_type}",
            "timestamp": datetime.utcnow().isoformat(),
            "slot": slot_selected,
            "queue_priority": queue_score,
            "prewarm_next": prewarm_hint,
        }
