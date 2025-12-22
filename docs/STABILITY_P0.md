# VX11 Stability P0 Suite

## Overview

The **VX11 Stability P0 Suite** is a reproducible harness for testing module stability, reliability, and performance across the VX11 system. It automates:

- **Baseline Setup:** Start core services (Madre + Tentaculo Link)
- **Module Cycling:** For each module in dependency order:
  - Bring up dependencies
  - Run health checks
  - Collect metrics (RAM/CPU/restarts/OOM)
  - Execute pytest subsets
  - Bring down the module
- **Reporting:** Generate JSON + Markdown reports with pass/fail status

---

## Quick Start

### 1. Unit Tests (Fast, No Docker)

```bash
python3 -m pytest -q tests/test_stability_p0_runner_unit.py -v
```

### 2. Integration Tests (Real Docker, ~60s-5min per cycle)

```bash
export VX11_INTEGRATION=1
python3 -m pytest -q tests/test_stability_p0_runner_integration.py -v
```

### 3. Full Harness Run

```bash
# Single cycle, low_power mode, default modules
python3 scripts/vx11_stability_p0.py

# Custom: 2 cycles, switch+hermes only, operative_core
python3 scripts/vx11_stability_p0.py \
  --mode operative_core \
  --cycles 2 \
  --modules switch,hermes
```

---

## Command Line Options

```
--mode {low_power|operative_core}
  Madre operating mode (default: low_power)

--cycles N
  Number of test cycles (default: 1)

--modules csv
  Comma-separated list of modules
  (default: switch,hermes,spawner,hormiguero,mcp,manifestator,operator-backend,operator-frontend,shubniggurath)

--audit-dir PATH
  Output directory for reports (default: docs/audit/vx11_stability_<timestamp>/)

--keep-core
  Keep Madre + Tentaculo Link running after tests (default: True)

--timeout-sec N
  Timeout for health checks and tests (default: 20s)
```

---

## Module Dependency Map

The harness respects module dependencies. Startup order is auto-sorted via topological sort:

```
baseline (madre + tentaculo_link)
  ├─ switch
  │   └─ hermes
  │       ├─ spawner
  │       │   └─ hormiguero
  │       ├─ mcp
  │       └─ manifestator
  ├─ operator-backend
  │   └─ operator-frontend
  └─ shubniggurath (optional)
```

### Custom Module Order

The harness automatically reorders modules based on `depends_on`. If you specify `--modules hormiguero,switch`, the harness will run `switch` first (because `hormiguero` depends on it).

---

## Outputs

Each run creates a timestamped directory in `docs/audit/vx11_stability_<timestamp>/`:

```
docs/audit/vx11_stability_20251222T215059Z/
├── REPORT.json          # Machine-readable results
├── REPORT.md            # Human-readable summary
├── raw/
│   ├── switch_test_switch_*.py.txt      # pytest output
│   ├── hermes_test_hermes_*.py.txt      # pytest output
│   └── ...
└── DEEPSEEK_R1_REVIEW.md    # (if harness design was reviewed)
```

### REPORT.json Structure

```json
{
  "timestamp": "2025-12-22T21:50:59.435007",
  "mode": "low_power",
  "cycles": 1,
  "modules_tested": ["switch", "hermes"],
  "summary": {
    "total_modules": 2,
    "passed": 2,
    "failed": 0
  },
  "modules": {
    "switch": {
      "name": "switch",
      "status": "PASS",
      "metrics": {
        "vx11-switch": {
          "stats": {
            "status": "running",
            "restart_count": 0,
            "oom_killed": false
          },
          "health_latency_ms": [45.5, 48.2, 46.1]
        }
      },
      "test_results": {
        "test_switch_registry_enqueue.py": {
          "return_code": 0,
          "passed": true
        }
      },
      "errors": []
    },
    ...
  }
}
```

---

## Thresholds & Pass/Fail Criteria

A module is marked **PASS** if:

- ✅ All dependencies started successfully
- ✅ Health endpoints respond within timeout
- ✅ No container has `OOMKilled=true`
- ✅ RestartCount does not increase during test
- ✅ Health p95 latency < 500ms (if available)
- ✅ All pytest tests pass (if available)

A module is marked **FAIL** if:

- ❌ Fails to start (docker compose error)
- ❌ Health endpoints do not respond
- ❌ OOMKilled detected
- ❌ Any pytest test fails

A module is marked **WARN** if:

- ⚠️ No tests found matching pattern (but health OK)
- ⚠️ High latency (p95 > 500ms) but still responding

---

## Interpreting REPORT.md

Example:

```markdown
# VX11 Stability P0 Report

**Timestamp:** 2025-12-22T21:50:59.435007
**Mode:** low_power
**Cycles:** 1

## Summary

- Total Modules Tested: 2
- Passed: 2
- Failed: 0

## Module Results

### ✅ switch
**Status:** PASS

**Metrics:**
- vx11-switch:
  - RAM: 100MB
  - CPU: 0.5%
  - Restarts: 0
  - OOMKilled: false
  - Health p95 latency: 48.2ms

**Test Results:**
- test_switch_registry_enqueue.py: ✓ PASS
- test_switch_chat_and_breaker.py: ✓ PASS

### ✅ hermes
...
```

Interpretation:

- **✅ Green checkmarks** = All criteria passed
- **⚠️ Yellow warnings** = High latency but operational
- **❌ Red X** = Module failed stability test

---

## Extending the Harness

### Add a New Module

1. Edit `MODULE_DEPENDENCY_MAP` in `scripts/vx11_stability_p0.py`:

```python
MODULE_DEPENDENCY_MAP = {
    "my-module": {
        "description": "My new module",
        "services": ["vx11-my-module"],
        "depends_on": ["baseline"],  # or ["baseline", "switch", ...]
        "health_endpoints": [("http://127.0.0.1:8099", "my-module")],
        "test_patterns": ["test_my_module_*.py"],
    },
    ...
}
```

2. Add to `CANONICAL_MODULE_ORDER`:

```python
CANONICAL_MODULE_ORDER = [
    ...,
    "my-module",
]
```

3. Create corresponding tests in `tests/test_my_module_*.py`.

### Customize Thresholds

Modify `_test_module()` method in `StabilityP0Runner`:

```python
# Health p95 latency threshold
if p95_latency > 1000:  # ms (default: 500)
    module_result["errors"].append(f"High latency: {p95_latency}ms")
```

### Add Memory Leak Detection

Modify `_test_module()` to track delta across cycles:

```python
if cycle > 1:
    prev_mem = self.memory_baseline.get(module_name, 0)
    curr_mem = parse_memory(stats)
    delta = curr_mem - prev_mem
    if delta > 50:  # MB threshold
        module_result["errors"].append(f"Possible memory leak: +{delta}MB")
```

---

## Known Limitations

1. **Parsing**: Docker stats parsing is pragmatic (not production-grade). Complex multi-container scenarios may need refinement.

2. **Health Endpoints**: Assumes HTTP-based health checks. Non-HTTP services require custom checks.

3. **Test Patterns**: Relies on pytest test file naming (`test_<module>_*.py`). If tests are reorganized, update patterns in `MODULE_DEPENDENCY_MAP`.

4. **No Parallel Execution**: Modules are tested sequentially for clarity. Future: implement parallel execution for independent modules.

5. **Hardcoded Ports**: Health endpoints are hardcoded by module (e.g., `http://127.0.0.1:8001` for switch). Changes to docker-compose ports must be reflected here.

---

## Troubleshooting

### Issue: "Failed to start baseline"

**Cause:** Docker compose error or images not built.

**Solution:**

```bash
# Rebuild images
docker compose build

# Check logs
docker compose logs madre tentaculo_link

# Ensure low_power environment
export VX11_MODE=low_power
docker compose up -d madre tentaculo_link
```

### Issue: "Health endpoints do not respond"

**Cause:** Service not fully initialized within timeout, or wrong port.

**Solution:**

```bash
# Check service status
docker compose ps

# Manual health check with more retries
curl -v http://127.0.0.1:8001/health

# Increase timeout in CLI
python3 scripts/vx11_stability_p0.py --timeout-sec 30
```

### Issue: "OOMKilled detected"

**Cause:** Service ran out of memory.

**Solution:**

```bash
# Check memory limits in docker-compose.yml
grep -A 5 "mem_limit:" docker-compose.yml

# Check actual memory usage
docker stats vx11-switch

# Increase limit or reduce module workload
```

### Issue: "No tests matching pattern"

**Cause:** Test files don't match pattern, or tests don't exist.

**Solution:**

1. Verify test file naming: `tests/test_<module>_*.py`
2. Update `test_patterns` in `MODULE_DEPENDENCY_MAP`
3. Create a smoke test if no unit tests exist

---

## DeepSeek R1 Review

This harness was designed with input from **DeepSeek R1** reasoning. Key recommendations accepted:

1. ✅ **Topological Sort**: Auto-order modules based on dependencies
2. ✅ **Exponential Backoff**: Retry health checks with jitter
3. ✅ **Docker Inspect JSON**: Robust metrics collection
4. ✅ **Test Validation**: Warn if patterns don't match

See `docs/audit/vx11_stability_<timestamp>/DEEPSEEK_R1_REVIEW.md` for full review.

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: VX11 Stability P0

on: push

jobs:
  stability-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Unit Tests
        run: python3 -m pytest tests/test_stability_p0_runner_unit.py -v

  stability-integration:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Integration Tests
        env:
          VX11_INTEGRATION: '1'
        run: python3 -m pytest tests/test_stability_p0_runner_integration.py -v

  stability-full:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'  # nightly
    steps:
      - uses: actions/checkout@v3
      - name: Full Harness
        run: python3 scripts/vx11_stability_p0.py --cycles 3 --timeout-sec 30
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: stability-report
          path: docs/audit/vx11_stability_*/
```

---

## Related Docs

- [VX11 Architecture](../docs/ARCHITECTURE.md)
- [Canonical Flows](../docs/CANONICAL_FLOWS_VX11.json)
- [Database Map](../docs/audit/DB_MAP_v7_FINAL.md)
- [pytest Configuration](../pytest.ini)

---

## Support

For issues, questions, or improvements:

1. Check troubleshooting section above
2. Review DeepSeek R1 recommendations in audit dir
3. Check stdout/stderr from `docker-compose logs`
4. Inspect raw pytest output in `docs/audit/vx11_stability_<ts>/raw/`
