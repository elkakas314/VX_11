"""
VX11 Metrics Collection Module
Proporciona interfaz unificada para recolección de métricas de módulos.
"""

import psutil
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import logging
import httpx

log = logging.getLogger("vx11.metrics")


class MetricsCollector:
    """Recolecta métricas de salud del sistema y módulos."""
    
    def __init__(self, ports_config: Dict[str, int] = None):
        """
        Args:
            ports_config: dict de settings.PORTS (opcional)
        """
        from config.settings import settings
        self.ports = ports_config or getattr(settings, 'PORTS', {})
        self.metrics_history = {}
        
    async def collect_local_metrics(self) -> Dict[str, float]:
        """Recolecta métricas del sistema local."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            log.warning(f"Error collecting local metrics: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_available_mb": 0,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def collect_module_metrics(self, module: str, port: int) -> Dict[str, Any]:
        """Recolecta métricas de un módulo remoto."""
        endpoints = [
            f"/metrics/cpu",
            f"/metrics/memory",
            f"/metrics/queue",
            f"/metrics/throughput"
        ]
        
        metrics = {
            "module": module,
            "port": port,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "available": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                for endpoint in endpoints:
                    try:
                        # Use settings URL if available, fallback to hostname
                        module_url = getattr(settings, f"{module}_url", None)
                        if not module_url:
                            module_url = f"http://{module}:{port}"
                        resp = await client.get(f"{module_url}{endpoint}")
                        if resp.status_code == 200:
                            data = resp.json()
                            metric_name = endpoint.split("/")[-1]
                            metrics[metric_name] = data.get("value", 0)
                    except:
                        metrics[endpoint.split("/")[-1]] = 0
                
                metrics["available"] = True
        except Exception as e:
            log.debug(f"Could not reach {module}:{port} - {e}")
            metrics["available"] = False
        
        return metrics
    
    async def collect_all_metrics(self, ports_config: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Recolecta métricas de todos los módulos.
        
        Args:
            ports_config: Mapa opcional de puertos para módulos. Si se proporciona,
            se usa para las consultas sin modificar la firma existente.
        """
        local_metrics = await self.collect_local_metrics()
        
        ports = ports_config or self.ports or {}
        module_list = list(ports.keys()) or ["switch", "hermes", "hormiguero", "manifestator", "mcp"]
        module_metrics = await asyncio.gather(*[
            self.collect_module_metrics(m, ports.get(m, 0))
            for m in module_list
        ])
        
        return {
            "local": local_metrics,
            "modules": {m["module"]: m for m in module_metrics if m.get("available")},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def calculate_load_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calcula score de carga (0.0 = bajo, 1.0 = crítico).
        """
        local = metrics.get("local", metrics)
        
        cpu = local.get("cpu_percent", 0) / 100.0
        mem = local.get("memory_percent", 0) / 100.0
        
        # Promedio ponderado
        score = (cpu * 0.6 + mem * 0.4)
        
        return min(1.0, max(0.0, score))
    
    def get_mode(self, load_score: float) -> str:
        """Determina modo operacional basado en carga."""
        if load_score < 0.3:
            return "ECO"
        elif load_score < 0.6:
            return "BALANCED"
        elif load_score < 0.85:
            return "HIGH-PERF"
        else:
            return "CRITICAL"


class MetricsBuffer:
    """Buffer de métricas para análisis histórico."""
    
    def __init__(self, max_size: int = 100):
        self.data: List[Dict] = []
        self.max_size = max_size
    
    def add(self, metrics: Dict[str, Any]):
        """Añade métrica al buffer."""
        self.data.append(metrics)
        if len(self.data) > self.max_size:
            self.data.pop(0)
    
    def append(self, metrics: Dict[str, Any]):
        """Alias para add() - compatible con tests."""
        self.add(metrics)
    
    def average(self, field: str, window: int = None) -> float:
        """Retorna promedio de un campo en el buffer."""
        if not self.data:
            return None
        
        if window is None:
            window = len(self.data)
        
        recent = self.data[-window:]
        values = [m.get(field) for m in recent if field in m]
        
        if not values:
            return None
        
        return sum(values) / len(values)
    
    def get_average_load(self, window: int = 10) -> float:
        """Retorna carga promedio en las últimas N métricas."""
        if not self.data:
            return 0.0
        
        recent = self.data[-window:]
        avg_cpu = sum(m.get("local", {}).get("cpu_percent", 0) for m in recent) / len(recent)
        avg_mem = sum(m.get("local", {}).get("memory_percent", 0) for m in recent) / len(recent)
        
        return (avg_cpu * 0.6 + avg_mem * 0.4) / 100.0
