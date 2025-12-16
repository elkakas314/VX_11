# FLUZO: Low-Power Adaptive Signals (Phase 3)

## Overview

FLUZO is a low-consumption telemetry module that collects system signals (CPU, RAM, power, temperature) and derives an operational mode (low_power, balanced, performance). It does **NOT** make decisions — only provides signals that influence Switch CLI scoring.

## Components

- **signals.py**: Collects raw metrics from psutil or /proc
- **profile.py**: Derives FLUZO mode based on thresholds
- **client.py**: Simple API: `get_signals()`, `get_profile()`, `get_mode()`

## Environment Variables

```bash
VX11_FLUZO_PERSIST=0                # Persist signals to DB (default: 0)
# Thresholds (in profile.py):
# - cpu_threshold_low: 30% (when CPU < this, performance mode possible)
# - cpu_threshold_high: 70% (when CPU > this, low_power mode possible)
# - memory_threshold_low: 40%
# - memory_threshold_high: 75%
# - battery_threshold_low: 20% (when battery < this AND on battery, low_power mode)
```

## Usage

```python
from switch.fluzo import FLUZOClient

fluzo = FLUZOClient()

# Get raw signals
signals = fluzo.get_signals()
# {"cpu_load_1m": 0.5, "memory_pct": 45, "on_ac": True, ...}

# Get profile with mode
profile = fluzo.get_profile()
# {"mode": "balanced", "signals": {...}, "reasoning": "..."}

# Get mode directly
mode = fluzo.get_mode()  # "balanced"
```

## Integration with CLI Concentrator

In `/switch/cli_concentrator/scoring.py`, FLUZO mode influences provider scoring:

```python
def _apply_fluzo_multiplier(self, fluzo_data, provider, request):
    mode = fluzo_data.get("profile", "balanced")
    
    if mode == "low_power":
        # Prefer cheaper, faster CLIs
        return 85.0 * 0.7  # Penalize heavy providers
    elif mode == "performance":
        # Allow heavier workloads
        return 100.0
    else:
        return 90.0
```

## Signals Collected

- **cpu_load_1m, cpu_load_5m, cpu_load_15m**: Load average
- **memory_pct**: RAM usage percentage
- **swap_pct**: Swap usage percentage
- **on_ac**: Boolean (True if plugged in)
- **battery_pct**: Battery percentage (if available)
- **temperature_c**: CPU temperature (if available)
- **disk_pct**: Disk usage percentage

## Modes Derived

- **low_power**: Battery critical OR high CPU+memory load
- **balanced**: Normal operation (default)
- **performance**: AC power AND low system load

## No Decision-Making

FLUZO is **purely informational**. It does not:
- Start/stop modules
- Change Madre behavior
- Modify routing policy (only influences scoring)
- Make resource allocation decisions

Switch and CLI Concentrator consume FLUZO data and apply it as one factor in their scoring algorithms.
