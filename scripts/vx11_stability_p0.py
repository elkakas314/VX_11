#!/usr/bin/env python3
"""
VX11 Stability P0 Suite Runner.

Purpose:
- Cycle start/stop per module
- Measure metrics (RAM/CPU/restarts/OOM/latencies)
- Run pytest subsets
- Generate reports (JSON + Markdown)

Usage:
  python3 scripts/vx11_stability_p0.py \
    --mode low_power \
    --cycles 1 \
    --modules switch,hermes \
    --audit-dir docs/audit/vx11_stability_<ts>/ \
    --timeout-sec 20

Environment:
  VX11_INTEGRATION: If set to "1", enable integration tests.
  DEEPSEEK_API_*: For DeepSeek API calls (optional).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# Module Dependency Map (Canonical Order)
# ============================================================================

MODULE_DEPENDENCY_MAP = {
    "baseline": {
        "description": "Madre + Tentaculo Link (core)",
        "services": ["madre", "tentaculo_link"],
        "depends_on": [],
        "health_endpoints": [
            ("http://127.0.0.1:8001", "madre"),
            ("http://127.0.0.1:8000", "tentaculo_link"),
        ],
        "flow_checks": [
            ("http://127.0.0.1:8001/health", "madre-health"),
            ("http://127.0.0.1:8000/health", "tentaculo-health"),
        ],
        "test_patterns": ["test_madre_*.py"],
    },
    "switch": {
        "description": "Provider routing",
        "services": ["switch"],
        "depends_on": ["baseline"],
        "health_endpoints": [("http://127.0.0.1:8002", "switch")],
        "flow_checks": [
            ("http://127.0.0.1:8002/health", "switch-health"),
        ],
        "test_patterns": ["test_switch_*.py"],
    },
    "hermes": {
        "description": "Registry & orchestration",
        "services": ["hermes"],
        "depends_on": ["baseline", "switch"],
        "health_endpoints": [("http://127.0.0.1:8003", "hermes")],
        "flow_checks": [
            ("http://127.0.0.1:8003/health", "hermes-health"),
        ],
        "test_patterns": ["test_hermes_*.py"],
    },
    "spawner": {
        "description": "Daughter process spawner",
        "services": ["spawner"],
        "depends_on": ["baseline", "hermes"],
        "health_endpoints": [("http://127.0.0.1:8008", "spawner")],
        "flow_checks": [
            ("http://127.0.0.1:8008/health", "spawner-health"),
        ],
        "test_patterns": ["test_spawner_*.py"],
    },
    "hormiguero": {
        "description": "Worker ant farm",
        "services": ["hormiguero"],
        "depends_on": ["baseline", "hermes", "spawner"],
        "health_endpoints": [("http://127.0.0.1:8004", "hormiguero")],
        "flow_checks": [
            ("http://127.0.0.1:8004/health", "hormiguero-health"),
        ],
        "test_patterns": ["test_hormiguero_*.py"],
    },
    "mcp": {
        "description": "Model Context Protocol",
        "services": ["mcp"],
        "depends_on": ["baseline", "hermes"],
        "health_endpoints": [("http://127.0.0.1:8006", "mcp")],
        "flow_checks": [
            ("http://127.0.0.1:8006/health", "mcp-health"),
        ],
        "test_patterns": ["test_mcp_*.py"],
    },
    "manifestator": {
        "description": "Manifest generator",
        "services": ["manifestator"],
        "depends_on": ["baseline", "hermes"],
        "health_endpoints": [("http://127.0.0.1:8005", "manifestator")],
        "flow_checks": [
            ("http://127.0.0.1:8005/health", "manifestator-health"),
        ],
        "test_patterns": ["test_manifestator_*.py"],
    },
    "shubniggurath": {
        "description": "Shubniggurath LLM orchestrator",
        "services": ["shubniggurath"],
        "depends_on": ["baseline"],
        "health_endpoints": [("http://127.0.0.1:8007", "shubniggurath")],
        "flow_checks": [
            ("http://127.0.0.1:8007/health", "shubniggurath-health"),
        ],
        "test_patterns": ["test_shub_*.py"],
    },
    "operator-backend": {
        "description": "Operator backend API (v7)",
        "services": ["operator-backend"],
        "depends_on": ["baseline", "switch"],
        "health_endpoints": [("http://127.0.0.1:8011", "operator-backend")],
        "flow_checks": [
            ("http://127.0.0.1:8011/health", "operator-backend-health"),
            ("http://127.0.0.1:8011/api/status", "operator-backend-status"),
        ],
        "test_patterns": ["test_operator_*.py"],
    },
    "operator-frontend": {
        "description": "Operator frontend (React)",
        "services": ["operator-frontend"],
        "depends_on": ["baseline", "operator-backend"],
        "health_endpoints": [("http://127.0.0.1:8020", "operator-frontend")],
        "flow_checks": [
            ("http://127.0.0.1:8020/", "operator-frontend-root"),
        ],
        "test_patterns": ["test_operator_frontend_*.py"],
    },
}

CANONICAL_MODULE_ORDER = [
    "switch",
    "hermes",
    "spawner",
    "hormiguero",
    "mcp",
    "manifestator",
    "shubniggurath",
    "operator-backend",
    "operator-frontend",
]


def topological_sort(modules: List[str]) -> List[str]:
    """
    Sort modules by their dependencies (topological sort).
    Ensures baseline is first, respects depends_on.
    """
    # Start with modules that have no unmet dependencies
    sorted_list = []
    remaining = set(modules)
    attempted = 0
    max_attempts = len(modules) + 1

    while remaining and attempted < max_attempts:
        attempted += 1
        made_progress = False

        for mod in list(remaining):
            deps = MODULE_DEPENDENCY_MAP[mod]["depends_on"]
            # Check if all deps are either in sorted_list or "baseline" (special case)
            if all(d == "baseline" or d in sorted_list for d in deps):
                sorted_list.append(mod)
                remaining.remove(mod)
                made_progress = True

        if not made_progress and remaining:
            # Circular dependency detected—log and add remaining as-is
            print(f"[WARN] Circular dependency detected; adding remaining: {remaining}")
            sorted_list.extend(sorted(remaining))
            break

    return sorted_list


# ============================================================================
# Utility Functions
# ============================================================================


def run_cmd(cmd: str, timeout: int = 10, silent: bool = False) -> Tuple[int, str, str]:
    """Run shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
        if not silent:
            print(f"[CMD] {cmd[:80]}")
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return 1, "", str(e)


def docker_stats(service_name: str) -> Dict[str, Any]:
    """
    Get docker stats for a container (RAM/CPU).
    Uses docker stats --no-stream --format json for robustness.
    Returns dict with mem_mib, mem_limit_mib, mem_pct, cpu_pct.
    """
    try:
        returncode, stdout, _ = run_cmd(
            f"docker stats --no-stream --format '{{{{json .}}}}' {service_name} 2>/dev/null",
            timeout=5,
            silent=True,
        )
        if returncode != 0 or not stdout:
            return {}

        # Parse JSON line
        data = json.loads(stdout.strip())

        # Extract memory usage (format: "123.4MiB")
        mem_str = data.get("MemUsage", "0B").split("/")[0].strip()
        mem_mib = _parse_memory_to_mib(mem_str)

        mem_limit_str = (
            data.get("MemUsage", "0B").split("/")[-1].strip()
            if "/" in data.get("MemUsage", "")
            else "0B"
        )
        mem_limit_mib = _parse_memory_to_mib(mem_limit_str)

        # Extract CPU (format: "1.23%")
        cpu_str = data.get("CPUPerc", "0%").replace("%", "").strip()
        cpu_pct = float(cpu_str) if cpu_str else 0.0

        mem_pct_str = data.get("MemPerc", "0%").replace("%", "").strip()
        mem_pct = float(mem_pct_str) if mem_pct_str else 0.0

        return {
            "mem_mib": mem_mib,
            "mem_limit_mib": mem_limit_mib,
            "mem_pct": mem_pct,
            "cpu_pct": cpu_pct,
        }
    except Exception:
        # Fallback to empty if JSON parsing fails
        return {"error": "Failed to parse docker stats"}


def _parse_memory_to_mib(mem_str: str) -> float:
    """Parse memory string (e.g., '123.4MiB') to MiB float."""
    try:
        mem_str = mem_str.strip()
        if mem_str.endswith("MiB"):
            return float(mem_str.replace("MiB", "").strip())
        elif mem_str.endswith("GiB"):
            return float(mem_str.replace("GiB", "").strip()) * 1024
        elif mem_str.endswith("KiB"):
            return float(mem_str.replace("KiB", "").strip()) / 1024
        elif mem_str.endswith("B"):
            return float(mem_str.replace("B", "").strip()) / (1024 * 1024)
        else:
            return 0.0
    except Exception:
        return 0.0


def docker_inspect(service_name: str) -> Dict[str, Any]:
    """Get docker inspect info for a service."""
    _, stdout, _ = run_cmd(
        f"docker inspect {service_name} 2>/dev/null",
        timeout=5,
        silent=True,
    )
    if not stdout:
        return {}

    try:
        data = json.loads(stdout)
        if data:
            d = data[0]
            return {
                "container_id": d.get("Id", "")[:12],
                "state": d.get("State", {}).get("Status"),
                "running": d.get("State", {}).get("Running"),
                "restart_count": d.get("RestartCount", 0),
                "oom_killed": d.get("State", {}).get("OOMKilled", False),
                "memory_limit": d.get("HostConfig", {}).get("Memory"),
            }
    except:
        pass

    return {}


def health_check(
    endpoint: str, timeout: int = 5, max_retries: int = 3
) -> Tuple[bool, float]:
    """
    Check health endpoint with exponential backoff retry.
    Returns (success, latency_ms).

    Uses curl with %{http_code} to parse HTTP status code.
    """
    latencies = []
    for attempt in range(max_retries):
        start = time.time()
        try:
            # Use curl to get HTTP status code in stdout
            returncode, stdout, _ = run_cmd(
                f"curl -s -o /dev/null -w '%{{http_code}}' {endpoint} --max-time {timeout}",
                timeout=timeout + 2,
                silent=True,
            )
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

            # Parse HTTP code (stdout should be like "200", "404", etc.)
            http_code_str = stdout.strip()
            if http_code_str and http_code_str[0] == "2":  # 200-299
                return True, latency_ms

            # Exponential backoff: 2^attempt seconds, e.g., 2s, 4s, 8s + jitter
            if attempt < max_retries - 1:
                wait_time = 2**attempt + (attempt * 0.5)  # jitter
                time.sleep(wait_time)
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

    # All retries exhausted; return with avg latency
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    return False, avg_latency


def run_pytest(pattern: str, timeout: int = 30) -> Tuple[int, str]:
    """Run pytest with pattern. Returns (returncode, output)."""
    cmd = f"python3 -m pytest -q -x tests/{pattern} 2>&1"
    rc, stdout, stderr = run_cmd(cmd, timeout=timeout, silent=True)
    return rc, stdout + stderr


def flow_check(endpoint: str, label: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Execute a flow check: GET endpoint, capture HTTP code, latency, and payload hash.
    Returns dict with: success, latency_ms, http_code, payload_hash, error.
    """
    start = time.time()
    try:
        returncode, stdout, _ = run_cmd(
            f"curl -s -w '\\n%{{http_code}}' {endpoint} --max-time {timeout}",
            timeout=timeout + 2,
            silent=True,
        )
        latency_ms = (time.time() - start) * 1000

        # Split response body and HTTP code
        lines = stdout.strip().rsplit("\n", 1)
        if len(lines) == 2:
            body, http_code_str = lines
        else:
            body = stdout.strip()
            http_code_str = "0"

        http_code = int(http_code_str) if http_code_str.isdigit() else 0
        success = 200 <= http_code < 300

        # Hash payload (if not empty)
        payload_hash = hashlib.md5(body.encode()).hexdigest()[:8] if body else "empty"

        return {
            "label": label,
            "success": success,
            "http_code": http_code,
            "latency_ms": latency_ms,
            "payload_hash": payload_hash,
            "error": None,
        }
    except Exception as e:
        return {
            "label": label,
            "success": False,
            "http_code": 0,
            "latency_ms": (time.time() - start) * 1000,
            "payload_hash": None,
            "error": str(e),
        }


def docker_up_services(services: List[str], mode: str = "low_power") -> Tuple[int, str]:
    """Bring up docker compose services."""
    svc_str = " ".join(services)
    cmd = f"docker compose up -d {svc_str}"
    rc, stdout, stderr = run_cmd(cmd, timeout=30)
    return rc, stdout + stderr


def docker_down_services(services: List[str]) -> Tuple[int, str]:
    """
    Stop and remove docker compose services with verification.

    Per DeepSeek R1: Add timeout handling and termination verification.
    """
    errors = []
    for svc in services:
        # Stop with timeout
        stop_rc, _, _ = run_cmd(
            f"docker compose stop -t 10 {svc} 2>/dev/null || true", timeout=15
        )

        # Force kill if needed
        run_cmd(f"docker compose kill {svc} 2>/dev/null || true", timeout=5)

        # Remove
        rm_rc, _, _ = run_cmd(
            f"docker compose rm -f {svc} 2>/dev/null || true", timeout=15
        )

        # Verify removal
        verify_rc, stdout, _ = run_cmd(
            f"docker ps -q --filter 'label=com.docker.compose.service={svc}' 2>/dev/null | wc -l",
            timeout=5,
            silent=True,
        )

        # If container still exists, force remove
        if verify_rc == 0 and stdout.strip() != "0":
            run_cmd(
                f"docker rm -f $(docker ps -aq --filter 'label=com.docker.compose.service={svc}') 2>/dev/null || true",
                timeout=15,
            )

    return 0, "Services stopped, killed, and removed"


def find_test_files(pattern: str, test_dir: str = "tests") -> List[str]:
    """
    Find test files matching pattern.

    Improved per DeepSeek R1: validate that tests are found; log if not.
    """
    test_path = Path(test_dir)
    if not test_path.exists():
        print(f"    [WARN] Test directory not found: {test_path}")
        return []

    matches = list(test_path.glob(pattern))
    if not matches:
        print(f"    [WARN] No tests matching pattern: {pattern}")
        return []

    return [str(m.relative_to(test_dir)) for m in matches if m.is_file()]


def calculate_stability_p0_pct(
    tests_pass: bool,
    health_ok: bool,
    restarts_increased: bool,
    oom_killed: bool,
    mem_peak_mib: float,
    mem_limit_mib: float,
    mem_threshold_mib: float = 400.0,
) -> float:
    """
    Calculate Stability_P0_pct score (0-100).

    Weights:
    - 40%: Tests (100% pass => full; any fail => 0)
    - 20%: Health (all OK => full; any fail => 0)
    - 15%: Restarts (no increase => full; any increase => 0)
    - 15%: OOM (not killed => full; killed => 0)
    - 10%: Memory (mem_peak <= threshold => full; linear degrade)
    """
    score = 0.0

    # 40% Tests
    if tests_pass:
        score += 40.0

    # 20% Health
    if health_ok:
        score += 20.0

    # 15% Restarts
    if not restarts_increased:
        score += 15.0

    # 15% OOM
    if not oom_killed:
        score += 15.0

    # 10% Memory (linear: 100% at threshold, 0% at 2*threshold)
    if mem_peak_mib <= mem_threshold_mib:
        score += 10.0
    elif mem_peak_mib <= (mem_threshold_mib * 2):
        # Linear degrade
        usage_ratio = (mem_peak_mib - mem_threshold_mib) / mem_threshold_mib
        mem_score = 10.0 * (1.0 - usage_ratio)
        score += max(0.0, mem_score)
    # else: mem_peak > 2*threshold => 0 for memory

    return min(100.0, max(0.0, score))


# ============================================================================
# Main Harness
# ============================================================================


class StabilityP0Runner:
    """Main stability harness."""

    def __init__(
        self,
        mode: str = "low_power",
        cycles: int = 1,
        modules: Optional[str] = None,
        audit_dir: Optional[str] = None,
        keep_core: bool = True,
        timeout_sec: int = 20,
    ):
        self.mode = mode
        self.cycles = cycles
        self.timeout_sec = timeout_sec
        self.keep_core = keep_core

        # Determine modules to test
        if modules:
            self.modules = modules.split(",")
        else:
            self.modules = CANONICAL_MODULE_ORDER

        # Setup audit directory
        if audit_dir:
            self.audit_dir = Path(audit_dir)
        else:
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            self.audit_dir = Path("docs/audit") / f"vx11_stability_{ts}"

        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Ensure raw/ subdir
        (self.audit_dir / "raw").mkdir(exist_ok=True)

        # Result tracking
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": mode,
            "cycles": cycles,
            "modules_tested": [],
            "summary": {
                "total_modules": 0,
                "passed": 0,
                "failed": 0,
            },
            "modules": {},
        }

    def run(self) -> int:
        """Execute stability P0 suite."""
        print(f"[HARNESS] Starting VX11 Stability P0 Suite")
        print(f"[HARNESS] Audit dir: {self.audit_dir}")

        # Apply topological sort (improved per DeepSeek R1)
        sorted_modules = topological_sort(self.modules)
        print(f"[HARNESS] Modules (sorted): {', '.join(sorted_modules)}")
        print(f"[HARNESS] Mode: {self.mode}, Cycles: {self.cycles}")

        # Baseline: start madre + tentaculo_link
        print("\n[PHASE 0] Starting baseline (madre + tentaculo_link)...")
        rc, out = docker_up_services(
            MODULE_DEPENDENCY_MAP["baseline"]["services"],
            mode=self.mode,
        )
        if rc != 0:
            print(f"[ERROR] Failed to start baseline: {out[:200]}")
            return 1

        time.sleep(3)  # Wait for baseline to stabilize

        # Main cycle
        for cycle in range(1, self.cycles + 1):
            print(f"\n[CYCLE {cycle}]")

            for module_name in sorted_modules:
                if module_name not in MODULE_DEPENDENCY_MAP:
                    print(f"[WARN] Unknown module: {module_name}")
                    continue

                self._test_module(module_name)

        # Cleanup
        if not self.keep_core:
            print("\n[CLEANUP] Stopping all services...")
            docker_down_services(
                [
                    s
                    for m_info in MODULE_DEPENDENCY_MAP.values()
                    for s in m_info["services"]
                ]
            )

        # Generate reports
        self._generate_reports()

        print(f"\n[COMPLETE] Results saved to {self.audit_dir}")
        return 0

    def _test_module(self, module_name: str) -> None:
        """Test single module."""
        module_info = MODULE_DEPENDENCY_MAP[module_name]
        print(f"\n  [MODULE] {module_name} ({module_info['description']})")

        module_result = {
            "name": module_name,
            "status": "UNKNOWN",
            "metrics": {},
            "test_results": {},
            "errors": [],
        }

        try:
            # Bring up module
            print(f"    [UP] Starting {module_name}...")
            rc, out = docker_up_services(module_info["services"], mode=self.mode)
            if rc != 0:
                module_result["errors"].append(f"Failed to start: {out[:100]}")
                module_result["status"] = "FAIL"
                self.results["modules"][module_name] = module_result
                return

            time.sleep(2)

            # Health check
            print(f"    [HEALTH] Checking {module_name}...")
            health_latencies = []
            for endpoint, label in module_info["health_endpoints"]:
                success, latency_ms = health_check(endpoint, timeout=self.timeout_sec)
                health_latencies.append(latency_ms)
                status_str = "✓" if success else "✗"
                print(f"      {status_str} {label}: {latency_ms:.1f}ms")

            if not any(health_latencies):
                module_result["errors"].append("No health endpoints responded")
                module_result["status"] = "FAIL"
                self.results["modules"][module_name] = module_result
                return

            # Flow checks (real endpoint functionality)
            print(f"    [FLOW] Testing module flows...")
            flow_results = []
            for endpoint, label in module_info.get("flow_checks", []):
                result = flow_check(endpoint, label, timeout=self.timeout_sec)
                flow_results.append(result)
                status_str = "✓" if result["success"] else "✗"
                print(
                    f"      {status_str} {label}: {result['latency_ms']:.1f}ms (code: {result['http_code']}, hash: {result['payload_hash']})"
                )

            module_result["flow_results"] = flow_results

            # Collect metrics
            print(f"    [METRICS] Collecting docker stats...")
            for svc in module_info["services"]:
                stats = docker_stats(svc)
                inspect = docker_inspect(svc)

                if inspect.get("oom_killed"):
                    module_result["errors"].append(f"{svc} was OOMKilled")

                module_result["metrics"][svc] = {
                    "stats": stats,
                    "inspect": inspect,
                    "health_latency_ms": health_latencies,
                }

            # Run tests
            print(f"    [TESTS] Running pytest patterns...")
            for pattern in module_info["test_patterns"]:
                test_files = find_test_files(pattern)
                if test_files:
                    print(f"      Testing {pattern}...")
                    for test_file in test_files[:2]:  # Limit to 2 test files
                        rc, output = run_pytest(test_file)
                        module_result["test_results"][test_file] = {
                            "return_code": rc,
                            "passed": rc == 0,
                        }
                        # Save output
                        test_out_file = (
                            self.audit_dir / "raw" / f"{module_name}_{test_file}.txt"
                        )
                        test_out_file.write_text(output)

            # Determine overall status and calculate stability score
            tests_pass = (
                all(tr.get("passed") for tr in module_result["test_results"].values())
                if module_result["test_results"]
                else False
            )

            health_ok = len(health_latencies) > 0 and not module_result["errors"]

            # Check if any restart counts increased (start with 0 baseline assumption)
            restarts_increased = False
            for svc, metrics in module_result["metrics"].items():
                if metrics.get("inspect", {}).get("restart_count", 0) > 0:
                    restarts_increased = True
                    break

            oom_killed = any(
                metrics.get("inspect", {}).get("oom_killed", False)
                for metrics in module_result["metrics"].values()
            )

            # Get max memory usage
            mem_peak_mib = max(
                (
                    metrics.get("stats", {}).get("mem_mib", 0)
                    for metrics in module_result["metrics"].values()
                ),
                default=0.0,
            )
            mem_limit_mib = max(
                (
                    metrics.get("stats", {}).get("mem_limit_mib", 512)
                    for metrics in module_result["metrics"].values()
                ),
                default=512.0,
            )

            # Calculate stability score
            stability_p0_pct = calculate_stability_p0_pct(
                tests_pass=tests_pass,
                health_ok=health_ok,
                restarts_increased=restarts_increased,
                oom_killed=oom_killed,
                mem_peak_mib=mem_peak_mib,
                mem_limit_mib=mem_limit_mib,
                mem_threshold_mib=min(400.0, mem_limit_mib * 0.8),
            )

            module_result["stability_p0_pct"] = stability_p0_pct

            if module_result["errors"]:
                module_result["status"] = "FAIL"
            elif any(
                not tr.get("passed") for tr in module_result["test_results"].values()
            ):
                module_result["status"] = "WARN"
            else:
                module_result["status"] = "PASS"

        except Exception as e:
            module_result["errors"].append(str(e))
            module_result["status"] = "FAIL"

        finally:
            # Bring down module (but keep baseline)
            print(f"    [DOWN] Stopping {module_name}...")
            docker_down_services(module_info["services"])

            # Track result
            self.results["modules"][module_name] = module_result
            self.results["modules_tested"].append(module_name)

            if module_result["status"] == "PASS":
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1

        self.results["summary"]["total_modules"] = len(self.results["modules_tested"])

    def _generate_reports(self) -> None:
        """Generate JSON and Markdown reports."""
        # JSON report
        json_file = self.audit_dir / "REPORT.json"
        json_file.write_text(json.dumps(self.results, indent=2))
        print(f"[REPORT] JSON: {json_file}")

        # Markdown report
        md_file = self.audit_dir / "REPORT.md"
        md_content = self._generate_markdown()
        md_file.write_text(md_content)
        print(f"[REPORT] Markdown: {md_file}")

    def _generate_markdown(self) -> str:
        """Generate Markdown report from results."""
        lines = [
            "# VX11 Stability P0 Report",
            "",
            f"**Timestamp:** {self.results['timestamp']}",
            f"**Mode:** {self.results['mode']}",
            f"**Cycles:** {self.results['cycles']}",
            "",
            "## Summary",
            "",
            f"- Total Modules Tested: {self.results['summary']['total_modules']}",
            f"- Passed: {self.results['summary']['passed']}",
            f"- Failed: {self.results['summary']['failed']}",
            "",
            "## Cost & Stability Table",
            "",
            "| Module | Status | Mem Peak (MiB) | CPU % | Restarts | OOM | Health p95 (ms) | Tests | Stability % |",
            "|--------|--------|----------------|-------|----------|-----|-----------------|-------|-------------|",
        ]

        # Add cost table rows
        for module_name, result in sorted(self.results["modules"].items()):
            status = result["status"]
            stability = result.get("stability_p0_pct", 0.0)

            # Extract metrics
            mem_peak = 0.0
            cpu_max = 0.0
            restarts = 0
            oom = "No"
            health_p95 = 0.0

            if result["metrics"]:
                for svc, metrics in result["metrics"].items():
                    stats = metrics.get("stats", {})
                    inspect = metrics.get("inspect", {})
                    mem_peak = max(mem_peak, stats.get("mem_mib", 0.0))
                    cpu_max = max(cpu_max, stats.get("cpu_pct", 0.0))
                    restarts = max(restarts, inspect.get("restart_count", 0))
                    if inspect.get("oom_killed"):
                        oom = "Yes"

                    latencies = metrics.get("health_latency_ms", [])
                    if latencies:
                        health_p95 = sorted(latencies)[int(len(latencies) * 0.95)]

            tests_pass = (
                all(tr.get("passed") for tr in result["test_results"].values())
                if result["test_results"]
                else "N/A"
            )
            tests_str = (
                "✓" if tests_pass else "✗" if isinstance(tests_pass, bool) else "—"
            )

            lines.append(
                f"| {module_name} | {status} | {mem_peak:.1f} | {cpu_max:.1f} | {restarts} | {oom} | {health_p95:.1f} | {tests_str} | {stability:.1f}% |"
            )

        lines.extend(
            [
                "",
                "## Module Results (Detailed)",
                "",
            ]
        )

        for module_name, result in self.results["modules"].items():
            status_emoji = (
                "✅"
                if result["status"] == "PASS"
                else "❌" if result["status"] == "FAIL" else "⚠️"
            )
            lines.append(f"### {status_emoji} {module_name}")
            lines.append("")
            lines.append(f"**Status:** {result['status']}")
            lines.append(
                f"**Stability Score:** {result.get('stability_p0_pct', 0.0):.1f}%"
            )
            lines.append("")

            if result["errors"]:
                lines.append("**Errors:**")
                for err in result["errors"]:
                    lines.append(f"- {err}")
                lines.append("")

            if result["metrics"]:
                lines.append("**Metrics:**")
                for svc, metrics in result["metrics"].items():
                    lines.append(f"- {svc}:")
                    stats = metrics.get("stats", {})
                    lines.append(
                        f"  - RAM: {stats.get('mem_mib', 'N/A'):.1f} MiB (limit: {stats.get('mem_limit_mib', 'N/A')})"
                    )
                    lines.append(f"  - CPU: {stats.get('cpu_pct', 'N/A'):.1f}%")
                    lines.append(
                        f"  - Restarts: {metrics['inspect'].get('restart_count', 0)}"
                    )
                    lines.append(
                        f"  - OOMKilled: {metrics['inspect'].get('oom_killed', False)}"
                    )
                    latencies = metrics.get("health_latency_ms", [])
                    if latencies:
                        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
                        lines.append(f"  - Health p95 latency: {p95_latency:.1f}ms")
                lines.append("")

            if result["test_results"]:
                lines.append("**Test Results:**")
                for test_file, tr in result["test_results"].items():
                    status = "✓ PASS" if tr["passed"] else "✗ FAIL"
                    lines.append(f"- {test_file}: {status}")
                lines.append("")

        # Add cost ranking
        lines.extend(
            [
                "",
                "## Cost Ranking (by Memory Peak)",
                "",
            ]
        )

        sorted_by_mem = sorted(
            self.results["modules"].items(),
            key=lambda x: max(
                (
                    m.get("stats", {}).get("mem_mib", 0.0)
                    for m in x[1].get("metrics", {}).values()
                ),
                default=0.0,
            ),
            reverse=True,
        )

        for rank, (module_name, result) in enumerate(sorted_by_mem, 1):
            mem_peak = max(
                (
                    m.get("stats", {}).get("mem_mib", 0.0)
                    for m in result.get("metrics", {}).values()
                ),
                default=0.0,
            )
            stability = result.get("stability_p0_pct", 0.0)
            lines.append(
                f"{rank}. **{module_name}**: {mem_peak:.1f} MiB (Stability: {stability:.1f}%)"
            )

        return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="VX11 Stability P0 Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["low_power", "operative_core"],
        default="low_power",
        help="Madre operating mode (default: low_power)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of test cycles (default: 1)",
    )
    parser.add_argument(
        "--modules",
        type=str,
        default=None,
        help=f"Comma-separated list of modules (default: {','.join(CANONICAL_MODULE_ORDER)})",
    )
    parser.add_argument(
        "--audit-dir",
        type=str,
        default=None,
        help="Audit output directory (default: docs/audit/vx11_stability_<ts>/)",
    )
    parser.add_argument(
        "--keep-core",
        action="store_true",
        default=True,
        help="Keep core services (madre, tentaculo_link) running (default: True)",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=20,
        help="Timeout for health checks and tests (default: 20s)",
    )

    args = parser.parse_args()

    runner = StabilityP0Runner(
        mode=args.mode,
        cycles=args.cycles,
        modules=args.modules,
        audit_dir=args.audit_dir,
        keep_core=args.keep_core,
        timeout_sec=args.timeout_sec,
    )

    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
