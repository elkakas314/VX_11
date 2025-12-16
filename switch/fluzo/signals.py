"""
FLUZO signals: raw system telemetry (CPU, RAM, power, temperature).
"""

from typing import Dict, Optional
import os
from datetime import datetime


class FLUZOSignals:
    """Raw system signals collector."""

    def __init__(self):
        """Initialize signals collector."""
        self.last_update = None
        self._try_psutil()

    def _try_psutil(self):
        """Try to import psutil for better metrics."""
        try:
            import psutil

            self.psutil = psutil
        except ImportError:
            self.psutil = None

    def collect(self) -> Dict[str, any]:
        """
        Collect current system signals.

        Returns:
            {
                "timestamp": datetime,
                "cpu_load_1m": float,
                "cpu_load_5m": float,
                "cpu_load_15m": float,
                "memory_pct": float,
                "swap_pct": float,
                "on_ac": bool,
                "battery_pct": Optional[int],
                "temperature_c": Optional[float],
                "disk_pct": float,
            }
        """
        result = {
            "timestamp": datetime.utcnow(),
            "cpu_load_1m": 0.0,
            "cpu_load_5m": 0.0,
            "cpu_load_15m": 0.0,
            "memory_pct": 0.0,
            "swap_pct": 0.0,
            "on_ac": True,
            "battery_pct": None,
            "temperature_c": None,
            "disk_pct": 0.0,
        }

        # Try psutil first
        if self.psutil:
            try:
                # CPU load
                loads = self.psutil.getloadavg()
                result["cpu_load_1m"] = loads[0]
                result["cpu_load_5m"] = loads[1]
                result["cpu_load_15m"] = loads[2]

                # Memory
                vmem = self.psutil.virtual_memory()
                result["memory_pct"] = vmem.percent

                swap = self.psutil.swap_memory()
                result["swap_pct"] = swap.percent

                # Battery (if available)
                try:
                    battery = self.psutil.sensors_battery()
                    if battery:
                        result["battery_pct"] = battery.percent
                        result["on_ac"] = battery.power_plugged
                except Exception:
                    pass

                # Temperature (if available)
                try:
                    temps = self.psutil.sensors_temperatures()
                    if temps and "coretemp" in temps:
                        result["temperature_c"] = temps["coretemp"][0].current
                except Exception:
                    pass

                # Disk
                try:
                    disk = self.psutil.disk_usage("/")
                    result["disk_pct"] = disk.percent
                except Exception:
                    pass

                self.last_update = result["timestamp"]
                return result

            except Exception:
                pass

        # Fallback: read from /proc
        return self._collect_from_proc()

    def _collect_from_proc(self) -> Dict[str, any]:
        """Fallback: collect from /proc on Linux."""
        result = {
            "timestamp": datetime.utcnow(),
            "cpu_load_1m": 0.0,
            "cpu_load_5m": 0.0,
            "cpu_load_15m": 0.0,
            "memory_pct": 0.0,
            "swap_pct": 0.0,
            "on_ac": True,
            "battery_pct": None,
            "temperature_c": None,
            "disk_pct": 0.0,
        }

        try:
            # CPU load from /proc/loadavg
            if os.path.exists("/proc/loadavg"):
                with open("/proc/loadavg") as f:
                    line = f.read().split()
                    result["cpu_load_1m"] = float(line[0])
                    result["cpu_load_5m"] = float(line[1])
                    result["cpu_load_15m"] = float(line[2])

            # Memory from /proc/meminfo
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo") as f:
                    lines = f.read().split("\n")
                    mem_total = 1
                    mem_free = 0
                    for line in lines:
                        if line.startswith("MemTotal:"):
                            mem_total = int(line.split()[1])
                        elif line.startswith("MemFree:"):
                            mem_free = int(line.split()[1])
                    result["memory_pct"] = ((mem_total - mem_free) / mem_total) * 100

            self.last_update = result["timestamp"]

        except Exception:
            pass

        return result
