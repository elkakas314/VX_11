"""
REINA IA: Queen with AI integration for intelligent task routing via SWITCH.
Used in production mode to delegate complex reasoning to remote/local LLMs.
"""

import logging
import json
import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

log = logging.getLogger("vx11.hormiguero.reina_ia")


class ReinaIA:
    """
    Intelligent Queen that uses SWITCH to delegate reasoning tasks.
    
    Features:
    - Task classification via SmartRouter
    - Adaptive decision-making based on engine capabilities
    - Quota-aware task prioritization
    - Fallback to local heuristics if SWITCH unavailable
    """
    
    def __init__(self, switch_endpoint: str = None):
        # Use settings if no endpoint provided
        if switch_endpoint is None:
            from config.settings import settings
            switch_port = settings.PORTS.get("switch", 8002)
            switch_endpoint = (settings.switch_url or f"http://switch:{switch_port}").rstrip("/")
        self.switch_endpoint = switch_endpoint
        self.client = None
        self.decisions: Dict[str, Dict[str, Any]] = {}
    
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
    
    async def classify_task(self, task_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use SWITCH to classify task and determine optimal handling strategy.
        
        Args:
            task_type: Task category (e.g., "inference", "classification", "pattern_detect")
            payload: Task payload dict
        
        Returns:
            {
                "task_id": str,
                "classification": str,
                "strategy": "local_ant" | "local_ants_parallel" | "remote_reasoning" | "hybrid",
                "confidence": float,
                "reasoning": str,
                "engine_name": str,
                "estimated_tokens": int,
            }
        """
        task_id = f"classify-{datetime.utcnow().timestamp():.0f}"
        
        # Build classification query
        query = f"Classify task: type={task_type}, payload_keys={list(payload.keys()) if payload else []}. Return: classification, strategy (local_ant|local_ants_parallel|remote_reasoning|hybrid), confidence."
        
        try:
            client = await self._get_client()
            
            # Call SWITCH /switch/route-v5
            resp = await client.post(
                f"{self.switch_endpoint}/switch/route-v5",
                json={
                    "query": query,
                    "context": {
                        "domain": "reasoning",
                        "allow_remote": True,
                        "max_latency_ms": 5000,
                    },
                },
                timeout=10.0,
            )
            
            if resp.status_code != 200:
                log.warning(f"classify_task_failed:status={resp.status_code}")
                return await self._fallback_classify(task_type, payload, task_id)
            
            router_response = resp.json()
            answer = router_response.get("answer", "")
            engine_name = router_response.get("engine_name", "unknown")
            tokens_used = router_response.get("tokens_used", 0)
            
            # Parse answer (simple heuristic)
            strategy = "local_ant"
            if "parallel" in answer.lower():
                strategy = "local_ants_parallel"
            elif "remote" in answer.lower() or "reasoning" in answer.lower():
                strategy = "remote_reasoning"
            elif "hybrid" in answer.lower():
                strategy = "hybrid"
            
            result = {
                "task_id": task_id,
                "classification": task_type,
                "strategy": strategy,
                "confidence": min(0.9, 0.5 + len(answer) / 1000),  # Rough confidence
                "reasoning": answer[:200],
                "engine_name": engine_name,
                "estimated_tokens": tokens_used,
                "success": True,
            }
            
            self.decisions[task_id] = result
            log.info(f"classify_task:ok:strategy={strategy}:engine={engine_name}")
            return result
        
        except Exception as e:
            log.error(f"classify_task_error:{e}")
            return await self._fallback_classify(task_type, payload, task_id)
    
    async def _fallback_classify(self, task_type: str, payload: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """Fallback classification using local heuristics."""
        # Simple heuristics when SWITCH unavailable
        if "urgent" in task_type.lower():
            strategy = "local_ants_parallel"
            confidence = 0.7
        elif "inference" in task_type.lower():
            strategy = "remote_reasoning"
            confidence = 0.6
        elif len(payload or {}) > 5:
            strategy = "hybrid"
            confidence = 0.5
        else:
            strategy = "local_ant"
            confidence = 0.8
        
        result = {
            "task_id": task_id,
            "classification": task_type,
            "strategy": strategy,
            "confidence": confidence,
            "reasoning": "fallback_classification",
            "engine_name": "local_heuristics",
            "estimated_tokens": 0,
            "success": False,
        }
        
        self.decisions[task_id] = result
        log.info(f"classify_task:fallback:strategy={strategy}")
        return result
    
    async def optimize_priority(
        self,
        task_type: str,
        payload: Dict[str, Any],
        current_queue_size: int,
        system_load: float,
    ) -> Dict[str, Any]:
        """
        Use SWITCH to optimize task priority based on context.
        
        Args:
            task_type: Task category
            payload: Task payload
            current_queue_size: Number of tasks in queue
            system_load: System load percentage (0-1)
        
        Returns:
            {
                "priority": int (1-10),
                "reasoning": str,
                "expedited": bool,
                "defer_until": Optional[float],  # Unix timestamp
            }
        """
        query = f"Prioritize task: type={task_type}, queue_size={current_queue_size}, load={system_load:.2f}. Return: priority(1-10), expedited(bool), reasoning."
        
        try:
            client = await self._get_client()
            
            resp = await client.post(
                f"{self.switch_endpoint}/switch/route-v5",
                json={
                    "query": query,
                    "context": {
                        "domain": "reasoning",
                        "allow_remote": False,  # Use local model for speed
                        "max_latency_ms": 1000,
                    },
                },
                timeout=5.0,
            )
            
            if resp.status_code != 200:
                # Fallback
                priority = max(1, min(10, 5 - int(system_load * 3)))
                return {
                    "priority": priority,
                    "reasoning": "fallback_priority",
                    "expedited": False,
                    "defer_until": None,
                }
            
            router_response = resp.json()
            answer = router_response.get("answer", "")
            
            # Parse priority from answer (heuristic)
            priority = 5
            try:
                import re
                match = re.search(r"priority[:\s]+(\d+)", answer)
                if match:
                    priority = int(match.group(1))
            except Exception:
                pass
            
            priority = max(1, min(10, priority))
            expedited = "expedited" in answer.lower() or "urgent" in answer.lower()
            
            return {
                "priority": priority,
                "reasoning": answer[:200],
                "expedited": expedited,
                "defer_until": None,
            }
        
        except Exception as e:
            log.error(f"optimize_priority_error:{e}")
            # Fallback
            priority = max(1, min(10, 5 - int(system_load * 3)))
            return {
                "priority": priority,
                "reasoning": "fallback_priority",
                "expedited": False,
                "defer_until": None,
            }
    
    async def suggest_ant_count(
        self,
        task_type: str,
        payload: Dict[str, Any],
        available_ants: int,
    ) -> Dict[str, Any]:
        """
        Use SWITCH to suggest number of ants for parallel task execution.
        """
        query = f"For task type={task_type} with payload_size={len(payload or {})}, how many parallel ants? Available: {available_ants}. Return: ant_count, reasoning."
        
        try:
            client = await self._get_client()
            
            resp = await client.post(
                f"{self.switch_endpoint}/switch/route-v5",
                json={
                    "query": query,
                    "context": {
                        "domain": "reasoning",
                        "allow_remote": False,
                        "max_latency_ms": 1000,
                    },
                },
                timeout=5.0,
            )
            
            if resp.status_code == 200:
                router_response = resp.json()
                answer = router_response.get("answer", "")
                
                # Parse ant count
                ant_count = 1
                try:
                    import re
                    match = re.search(r"(\d+)\s*ant", answer)
                    if match:
                        ant_count = int(match.group(1))
                except Exception:
                    pass
                
                ant_count = max(1, min(available_ants, ant_count))
                
                return {
                    "ant_count": ant_count,
                    "reasoning": answer[:200],
                    "parallelizable": ant_count > 1,
                }
        
        except Exception as e:
            log.error(f"suggest_ant_count_error:{e}")
        
        # Fallback: suggest 2-4 ants for parallel tasks
        if "parallel" in task_type.lower() or len(payload or {}) > 3:
            return {
                "ant_count": min(4, available_ants),
                "reasoning": "fallback_suggestion",
                "parallelizable": True,
            }
        else:
            return {
                "ant_count": 1,
                "reasoning": "fallback_suggestion",
                "parallelizable": False,
            }
    
    def get_decision(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored decision."""
        return self.decisions.get(task_id)
