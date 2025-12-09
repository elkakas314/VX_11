"""
Switch-Hermes Integration Module
Proporciona control adaptativo de motores IA con feedback loops y circuit breaker.
"""

from typing import Dict, List, Literal, Any
from datetime import datetime, timedelta
import logging

log = logging.getLogger("vx11.switch_hermes")

# Tipos
Mode = Literal["ECO", "BALANCED", "HIGH-PERF", "CRITICAL"]
EngineStatus = Literal["available", "error", "throttled", "offline"]

# Perfiles de motores por modo
ENGINE_PROFILES: Dict[Mode, Dict[str, Any]] = {
    "ECO": {
        "preferred_engines": ["hermes_local", "cli_bash"],
        "timeout_ms": 5000,
        "max_concurrent": 2,
        "fallback_chain": ["cli_bash"],
        "description": "Local and CLI engines only"
    },
    "BALANCED": {
        "preferred_engines": ["hermes_local", "hermes_cli", "openrouter_text"],
        "timeout_ms": 8000,
        "max_concurrent": 4,
        "fallback_chain": ["hermes_local", "cli_bash"],
        "description": "Mix of local and light cloud engines"
    },
    "HIGH-PERF": {
        "preferred_engines": ["openrouter_text", "deepseek", "hermes_cli"],
        "timeout_ms": 15000,
        "max_concurrent": 8,
        "fallback_chain": ["openrouter_text", "hermes_local"],
        "description": "Cloud engines with high capacity"
    },
    "CRITICAL": {
        "preferred_engines": ["deepseek", "openrouter_text"],
        "timeout_ms": 30000,
        "max_concurrent": 16,
        "fallback_chain": ["deepseek"],
        "description": "Only most reliable engines"
    }
}


class EngineMetrics:
    """Tracks metrics per engine for adaptive selection."""
    
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_latency_ms = 0
        self.last_error = None
        self.last_error_time = None
        self.status: EngineStatus = "available"
        self.consecutive_errors = 0
        self.circuit_breaker_open = False
        self.circuit_breaker_open_time = None
    
    def record_success(self, latency_ms: int):
        """Record successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency_ms += latency_ms
        self.consecutive_errors = 0
        if self.consecutive_errors < 3:  # Reset after 3 consecutive successes
            self.status = "available"
    
    def record_error(self, error: str):
        """Record failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_error = error
        self.last_error_time = datetime.utcnow()
        self.consecutive_errors += 1
        self.status = "error"
        
        # Circuit breaker: open after 5 consecutive errors
        if self.consecutive_errors >= 5:
            self.circuit_breaker_open = True
            self.circuit_breaker_open_time = datetime.utcnow()
            log.warning(f"Circuit breaker OPEN for {self.engine_name}")
    
    def try_reset_circuit_breaker(self, timeout_seconds: int = 60):
        """Try to reset circuit breaker after timeout."""
        if self.circuit_breaker_open and self.circuit_breaker_open_time:
            elapsed = (datetime.utcnow() - self.circuit_breaker_open_time).total_seconds()
            if elapsed > timeout_seconds:
                self.circuit_breaker_open = False
                self.consecutive_errors = 0
                self.status = "available"
                log.info(f"Circuit breaker RESET for {self.engine_name}")
    
    def get_avg_latency_ms(self) -> float:
        """Get average latency."""
        if self.successful_requests == 0:
            return 0
        return self.total_latency_ms / self.successful_requests
    
    def get_error_rate(self) -> float:
        """Get error rate as percentage."""
        if self.total_requests == 0:
            return 0
        return (self.failed_requests / self.total_requests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize metrics."""
        return {
            "engine": self.engine_name,
            "status": self.status,
            "total_requests": self.total_requests,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "error_rate_percent": self.get_error_rate(),
            "avg_latency_ms": self.get_avg_latency_ms(),
            "circuit_breaker_open": self.circuit_breaker_open,
            "consecutive_errors": self.consecutive_errors,
            "last_error": self.last_error
        }


class AdaptiveEngineSelector:
    """Selects best engine based on mode, metrics, and availability."""
    
    def __init__(self):
        self.metrics: Dict[str, EngineMetrics] = {}
        self.current_mode: Mode = "BALANCED"
        self.available_engines: List[str] = []
    
    def register_engine(self, engine_name: str):
        """Register an engine for tracking."""
        if engine_name not in self.metrics:
            self.metrics[engine_name] = EngineMetrics(engine_name)
    
    def set_mode(self, mode: Mode):
        """Set current operational mode."""
        if mode in ENGINE_PROFILES:
            self.current_mode = mode
            log.info(f"Mode changed to {mode}")
        else:
            log.warning(f"Invalid mode: {mode}")
    
    def set_available_engines(self, engines: List[str]):
        """Set list of currently available engines."""
        self.available_engines = engines
    
    def select_engine(self, query: str = "") -> Dict[str, Any]:
        """
        Select best engine for current mode.
        
        Returns:
            {
              "engine": "engine_name",
              "profile": {mode specific profile},
              "fallbacks": [list of fallback engines],
              "reason": "selection reason"
            }
        """
        profile = ENGINE_PROFILES.get(self.current_mode)
        if not profile:
            return {"error": f"Unknown mode: {self.current_mode}"}
        
        # Get preferred engines for this mode
        preferred = profile["preferred_engines"]
        # Ensure metrics for all available engines
        for engine in list(self.available_engines):
            if engine not in self.metrics:
                self.register_engine(engine)
        
        # Filter by availability and circuit breaker status
        candidates = []
        for engine in preferred:
            if engine not in self.available_engines:
                continue
            
            # Register engine if not already tracked
            if engine not in self.metrics:
                self.register_engine(engine)
            
            self.metrics[engine].try_reset_circuit_breaker()
            
            if self.metrics[engine].circuit_breaker_open:
                continue
            
            if self.metrics[engine].status == "available":
                candidates.append(engine)
        
        # If no candidates, use fallbacks
        if not candidates:
            candidates = [e for e in profile["fallback_chain"] if e in self.available_engines]
        
        if not candidates:
            return {
                "error": f"No engines available for mode {self.current_mode}",
                "profile": profile
            }
        
        # Select best candidate (lowest error rate, best latency)
        best_engine = min(
            candidates,
            key=lambda e: (
                self.metrics[e].get_error_rate(),
                self.metrics[e].get_avg_latency_ms()
            )
        )
        
        return {
            "status": "ok",
            "engine": best_engine,
            "mode": self.current_mode,
            "profile": {
                "timeout_ms": profile["timeout_ms"],
                "max_concurrent": profile["max_concurrent"]
            },
            "fallbacks": profile["fallback_chain"],
            "reason": f"Selected for {self.current_mode} mode"
        }
    
    def record_engine_result(self, engine: str, success: bool, latency_ms: int = 0, error: str = None):
        """Record result from engine execution."""
        if engine not in self.metrics:
            self.register_engine(engine)
        
        if success:
            self.metrics[engine].record_success(latency_ms)
        else:
            self.metrics[engine].record_error(error or "Unknown error")
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all engines."""
        return {
            engine: metrics.to_dict()
            for engine, metrics in self.metrics.items()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current selector status."""
        active_engines = [e for e in self.available_engines if e in self.metrics]
        healthy = [e for e in active_engines if self.metrics[e].status == "available"]
        
        return {
            "status": "ok",
            "mode": self.current_mode,
            "available_engines": self.available_engines,
            "healthy_engines": healthy,
            "unhealthy_engines": [e for e in active_engines if e not in healthy],
            "metrics": self.get_all_metrics()
        }


# Global singleton
_selector = AdaptiveEngineSelector()


def get_selector() -> AdaptiveEngineSelector:
    """Get global selector instance."""
    return _selector
