# VX11 Status Report

**Timestamp**: 2025-12-15T05:08:43.329803Z

## Runtime Truth
`python3 scripts/vx11_runtime_truth.py`
```
======================================================================
VX11 Runtime Truth: Service Probe
======================================================================
  Probing tentaculo_link (port 8000)... → OK
  Probing madre (port 8001)... → OK
  Probing switch (port 8002)... → OK
  Probing hermes (port 8003)... → BROKEN
  Probing hormiguero (port 8004)... → BROKEN
  Probing manifestator (port 8005)... → OK
  Probing mcp (port 8006)... → OK
  Probing shubniggurath (port 8007)... → BROKEN
  Probing spawner (port 8008)... → OK
  Probing operator (port 8011)... → OK

[Report] Generating markdown... ✓ /home/elkakas314/vx11/docs/audit/VX11_RUNTIME_TRUTH_REPORT.md
[DB] Writing to copilot_runtime_services... [DB] Write skipped (read-only or error): table copilot_runtime_services has no column named http_code


======================================================================
✅ Runtime truth complete
======================================================================

```

## Scan & Map
`python3 scripts/vx11_scan_and_map.py --write`
```
======================================================================
VX11 Agent Bootstrap: Repo Scan + BD Map + Report
======================================================================

Database: /home/elkakas314/vx11/data/runtime/vx11.db

1. Initializing copilot_* tables...
   ✓ Tables ready

2. Scanning canonical paths...
   ✓ Canonical paths scanned

3. Checking runtime services (ports 8000-8020)...
   ✓ 7/10 services up

4. Generating bootstrap report...
   ✓ Report: docs/audit/VX11_AGENT_BOOTSTRAP_REPORT.md

======================================================================
✅ Bootstrap complete. Agent ready.
======================================================================

```

