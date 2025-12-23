"""
CPU pressure detector for Hormiguero.

Portable CPU monitoring: cgroup v2, /proc/loadavg, /proc/stat fallback.
Detects sustained high CPU and returns normalized metrics.
"""

import os
import time
from typing import Dict, Optional, Tuple


class CPUPressureScanner:
    """Detects sustained high CPU usage in container."""

    def __init__(self, window_sec: int = 30, threshold_pct: float = 80.0):
        """
        Args:
            window_sec: Time window to detect sustained high CPU (seconds)
            threshold_pct: CPU threshold percentage (0-100)
        """
        self.window_sec = window_sec
        self.threshold_pct = threshold_pct
        self._samples = []  # (timestamp, cpu_usage) tuples

    def _read_cgroup_v2_cpu(self) -> Optional[Tuple[float, float]]:
        """
        Read CPU stats from cgroup v2 (if available).
        Returns (cpu_usage_pct, limit_pct) or None if not available.
        """
        try:
            # Try cgroup v2 path
            with open("/sys/fs/cgroup/cpu.stat", "r") as f:
                lines = f.readlines()
                usage_usec = 0
                for line in lines:
                    if line.startswith("usage_usec"):
                        usage_usec = int(line.split()[-1])
                        break

            # Read CPU max (soft limit)
            max_usec = 100000  # 100ms default
            try:
                with open("/sys/fs/cgroup/cpu.max", "r") as f:
                    parts = f.read().strip().split()
                    if parts[0] != "max":
                        max_usec = int(parts[0])
            except (FileNotFoundError, ValueError):
                pass

            # Calculate usage percentage (relative to limit period)
            # Rough estimate: usage_usec / (100ms * #cores) * 100
            num_cores = os.cpu_count() or 1
            period_usec = 100000
            cpu_pct = (usage_usec / (period_usec * num_cores)) * 100
            cpu_pct = min(100, max(0, cpu_pct))

            return cpu_pct, 100.0
        except Exception:
            return None

    def _read_proc_loadavg(self) -> Optional[Tuple[float, float, float]]:
        """
        Read load averages from /proc/loadavg.
        Returns (load1, load5, load15) or None if not available.
        """
        try:
            with open("/proc/loadavg", "r") as f:
                parts = f.read().split()
                return float(parts[0]), float(parts[1]), float(parts[2])
        except Exception:
            return None

    def _read_proc_stat(self) -> Optional[Dict[str, float]]:
        """
        Read CPU stats from /proc/stat.
        Returns dict with cpu_pct or None if not available.
        """
        try:
            with open("/proc/stat", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("cpu "):
                        parts = [int(x) for x in line.split()[1:]]
                        if len(parts) >= 4:
                            user, nice, system, idle = (
                                parts[0],
                                parts[1],
                                parts[2],
                                parts[3],
                            )
                            total = user + nice + system + idle
                            if total == 0:
                                return {"cpu_pct": 0.0}
                            used = user + nice + system
                            cpu_pct = (used / total) * 100
                            return {"cpu_pct": min(100, cpu_pct)}
        except Exception:
            pass
        return None

    def _get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage (0-100).
        Tries cgroup v2, then /proc/stat.
        """
        # Try cgroup v2 first
        result = self._read_cgroup_v2_cpu()
        if result:
            return result[0]

        # Fallback to /proc/stat
        result = self._read_proc_stat()
        if result:
            return result["cpu_pct"]

        # If all fails, return 0 (safe)
        return 0.0

    def detect_sustained_high(self) -> bool:
        """
        Detect if CPU has been sustained high over window_sec.
        Returns True if average CPU > threshold over window.
        """
        now = time.time()
        cutoff = now - self.window_sec

        # Remove old samples
        self._samples = [(ts, cpu) for ts, cpu in self._samples if ts > cutoff]

        # Get current CPU
        cpu_now = self._get_cpu_usage()
        self._samples.append((now, cpu_now))

        # Need at least 2 samples to detect trend
        if len(self._samples) < 2:
            return False

        # Average over window
        avg_cpu = sum(cpu for _, cpu in self._samples) / len(self._samples)
        return avg_cpu > self.threshold_pct

    def scan_cpu_pressure(self) -> Dict[str, object]:
        """
        Scan CPU pressure and return normalized metrics.
        """
        try:
            cpu_usage = self._get_cpu_usage()
            load_result = self._read_proc_loadavg()
            load_avg = load_result if load_result else (0.0, 0.0, 0.0)
            sustained_high = self.detect_sustained_high()

            return {
                "status": "ok",
                "cpu_usage_pct": round(cpu_usage, 2),
                "load_avg_1m": round(load_avg[0], 2),
                "load_avg_5m": round(load_avg[1], 2),
                "load_avg_15m": round(load_avg[2], 2),
                "sustained_high": sustained_high,
                "threshold_pct": self.threshold_pct,
                "window_sec": self.window_sec,
            }
        except Exception as exc:
            return {
                "status": "error",
                "error": str(exc),
                "cpu_usage_pct": 0.0,
                "sustained_high": False,
            }


# Global instance (lazy init)
_scanner_instance: Optional[CPUPressureScanner] = None


def get_scanner(
    window_sec: int = 30, threshold_pct: float = 80.0
) -> CPUPressureScanner:
    """Get or create global CPU pressure scanner."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = CPUPressureScanner(window_sec, threshold_pct)
    return _scanner_instance


def scan_cpu_pressure() -> Dict[str, object]:
    """
    Scan CPU pressure (convenience function for Ant).
    Uses default scanner.
    """
    scanner = get_scanner()
    return scanner.scan_cpu_pressure()
