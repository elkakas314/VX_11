"""
VX11 Prometheus Metrics Layer (Phase 3.3)
==========================================
Export metrics for monitoring, alerting, and capacity planning.

Metrics:
- shub_proxy_requests_total: Total proxy requests by status/path/method
- shub_proxy_latency_ms: Proxy latency histogram (p50/p95/p99)
- cache_hit_rate: Cache hit percentage for /shub/health
- rate_limit_rejections: Total rate-limit violations
"""

import logging
import os
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Collect and export Prometheus metrics for Phase 3.3"""

    def __init__(self):
        self.enabled = os.getenv("VX11_METRICS_ENABLED", "true").lower() == "true"
        self.metrics: Dict[str, dict] = {
            "shub_proxy_requests_total": {},
            "shub_proxy_latency_ms": [],
            "cache_hit_total": 0,
            "cache_miss_total": 0,
            "rate_limit_rejections": 0,
        }
        self.start_time = time.time()

    def record_proxy_request(
        self,
        status_code: int,
        path: str,
        method: str,
        latency_ms: float,
    ):
        """Record proxy request metric"""
        if not self.enabled:
            return

        # Aggregate by status/path/method
        key = f"{status_code}:{path}:{method}"
        if key not in self.metrics["shub_proxy_requests_total"]:
            self.metrics["shub_proxy_requests_total"][key] = 0
        self.metrics["shub_proxy_requests_total"][key] += 1

        # Record latency
        self.metrics["shub_proxy_latency_ms"].append(latency_ms)

        # Keep only last 1000 samples for p50/p95/p99
        if len(self.metrics["shub_proxy_latency_ms"]) > 1000:
            self.metrics["shub_proxy_latency_ms"] = self.metrics[
                "shub_proxy_latency_ms"
            ][-1000:]

    def record_cache_hit(self):
        """Record cache hit"""
        if self.enabled:
            self.metrics["cache_hit_total"] += 1

    def record_cache_miss(self):
        """Record cache miss"""
        if self.enabled:
            self.metrics["cache_miss_total"] += 1

    def record_rate_limit_rejection(self):
        """Record rate limit rejection"""
        if self.enabled:
            self.metrics["rate_limit_rejections"] += 1

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage"""
        total = self.metrics["cache_hit_total"] + self.metrics["cache_miss_total"]
        if total == 0:
            return 0.0
        return (self.metrics["cache_hit_total"] / total) * 100

    def get_latency_percentiles(self) -> dict:
        """Get latency p50/p95/p99"""
        if not self.metrics["shub_proxy_latency_ms"]:
            return {"p50": 0, "p95": 0, "p99": 0}

        sorted_latencies = sorted(self.metrics["shub_proxy_latency_ms"])
        length = len(sorted_latencies)

        p50_idx = max(0, (length * 50) // 100)
        p95_idx = max(0, (length * 95) // 100)
        p99_idx = max(0, (length * 99) // 100)

        return {
            "p50": sorted_latencies[p50_idx],
            "p95": sorted_latencies[p95_idx],
            "p99": sorted_latencies[p99_idx],
        }

    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format"""
        if not self.enabled:
            return "# Metrics disabled\n"

        lines = []
        lines.append("# HELP shub_proxy_requests_total Total proxy requests")
        lines.append("# TYPE shub_proxy_requests_total counter")

        # Requests by status/path/method
        for key, count in self.metrics["shub_proxy_requests_total"].items():
            status, path, method = key.split(":")
            lines.append(
                f'shub_proxy_requests_total{{status="{status}",path="{path}",method="{method}"}} {count}'
            )

        # Cache metrics
        lines.append("# HELP cache_hit_total Total cache hits")
        lines.append("# TYPE cache_hit_total counter")
        lines.append(f"cache_hit_total {self.metrics['cache_hit_total']}")

        lines.append("# HELP cache_miss_total Total cache misses")
        lines.append("# TYPE cache_miss_total counter")
        lines.append(f"cache_miss_total {self.metrics['cache_miss_total']}")

        lines.append("# HELP cache_hit_rate Cache hit rate percentage")
        lines.append("# TYPE cache_hit_rate gauge")
        lines.append(f"cache_hit_rate {self.get_cache_hit_rate():.2f}")

        # Latency percentiles
        percentiles = self.get_latency_percentiles()
        lines.append("# HELP shub_proxy_latency_p50 Proxy latency p50")
        lines.append("# TYPE shub_proxy_latency_p50 gauge")
        lines.append(f"shub_proxy_latency_p50 {percentiles['p50']:.2f}")

        lines.append("# HELP shub_proxy_latency_p95 Proxy latency p95")
        lines.append("# TYPE shub_proxy_latency_p95 gauge")
        lines.append(f"shub_proxy_latency_p95 {percentiles['p95']:.2f}")

        lines.append("# HELP shub_proxy_latency_p99 Proxy latency p99")
        lines.append("# TYPE shub_proxy_latency_p99 gauge")
        lines.append(f"shub_proxy_latency_p99 {percentiles['p99']:.2f}")

        # Rate limit rejections
        lines.append("# HELP rate_limit_rejections Total rate limit rejections")
        lines.append("# TYPE rate_limit_rejections counter")
        lines.append(f"rate_limit_rejections {self.metrics['rate_limit_rejections']}")

        # Uptime
        uptime = time.time() - self.start_time
        lines.append("# HELP vx11_uptime_seconds Service uptime")
        lines.append("# TYPE vx11_uptime_seconds gauge")
        lines.append(f"vx11_uptime_seconds {uptime:.0f}")

        return "\n".join(lines) + "\n"

    def get_summary(self) -> dict:
        """Get metrics summary for monitoring"""
        percentiles = self.get_latency_percentiles()
        return {
            "uptime_seconds": time.time() - self.start_time,
            "cache_hit_rate": self.get_cache_hit_rate(),
            "total_requests": sum(self.metrics["shub_proxy_requests_total"].values()),
            "total_cache_hits": self.metrics["cache_hit_total"],
            "total_cache_misses": self.metrics["cache_miss_total"],
            "rate_limit_rejections": self.metrics["rate_limit_rejections"],
            "latency_percentiles": percentiles,
        }


# Global metrics instance
_prom_metrics: Optional[PrometheusMetrics] = None


def get_prometheus_metrics() -> PrometheusMetrics:
    """Get or create Prometheus metrics instance"""
    global _prom_metrics
    if _prom_metrics is None:
        _prom_metrics = PrometheusMetrics()
    return _prom_metrics
