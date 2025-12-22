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
            ("http://127.0.0.1:8000", "madre"),
            ("http://127.0.0.1:8004", "tentaculo_link"),
        ],
        "test_patterns": ["test_madre_*.py"],
    },
    "switch": {
        "description": "Provider routing",
        "services": ["switch"],
        "depends_on": ["baseline"],
        "health_endpoints": [("http://127.0.0.1:8001", "switch")],
        "test_patterns": ["test_switch_*.py"],
    },
    "hermes": {
        "description": "Registry & orchestration",
        "services": ["hermes"],
        "depends_on": ["baseline", "switch"],
        "health_endpoints": [("http://127.0.0.1:8002", "hermes")],
        "test_patterns": ["test_hermes_*.py"],
    },
    "spawner": {
        "description": "Daughter process spawner",
        "services": ["spawner"],
        "depends_on": ["baseline", "hermes"],
        "health_endpoints": [("http://127.0.0.1:8005", "spawner")],
        "test_patterns": ["test_spawner_*.py"],
    },
    "hormiguero": {
        "description": "Worker ant farm",
        "services": ["hormiguero"],
        "depends_on": ["baseline", "hermes", "spawner"],
        "health_endpoints": [("http://127.0.0.1:8003", "hormiguero")],
        "test_patterns": ["test_hormiguero_*.py"],
    },
    "mcp": {
        "description": "Model Context Protocol",
        "services": ["mcp"],
        "depends_on": ["baseline", "hermes"],
        "health_endpoints": [("http://127.0.0.1:8006", "mcp")],
        "test_patterns": ["test_mcp_*.py"],
    },
    "manifestator": {
        "description": "Manifest generator",
        "services": ["manifestator"],
        "depends_on": ["baseline", "hermes"],
        "health_endpoints": [("http://127.0.0.1:8007", "manifestator")],
        "test_patterns": ["test_manifestator_*.py"],
    },
    "operator-backend": {
        "description": "Operator backend API (v7)",
        "services": ["operator-backend"],
        "depends_on": ["baseline"],
        "health_endpoints": [("http://127.0.0.1:8011", "operator-backend")],
        "test_patterns": ["test_operator_*.py"],
    },
    "operator-frontend": {
        "description": "Operator frontend (React)",
        "services": ["operator-frontend"],
        "depends_on": ["baseline", "operator-backend"],
        "health_endpoints": [("http://127.0.0.1:8020", "operator-frontend")],
        "test_patterns": ["test_operator_frontend_*.py"],
    },
    "shubniggurath": {
        "description": "Audio processing (optional)",
        "services": ["shubniggurath"],
        "depends_on": ["baseline"],
        "health_endpoints": [("http://127.0.0.1:9999", "shubniggurath")],
        "test_patterns": ["test_shub*.py"],
    },
}

CANONICAL_MODULE_ORDER = [
    "switch",
    "hermes",
    "spawner",
    "hormiguero",
    "mcp",
    "manifestator",
    "operator-backend",
    "operator-frontend",
    "shubniggurath",
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
    Get docker stats for a service (no-stream).

    Improved per DeepSeek R1: use docker inspect --format for robustness.
    """
    _, stdout, _ = run_cmd(
        f"docker inspect {service_name} --format='{{{{json .State}}}}'",
        timeout=5,
        silent=True,
    )

    if not stdout:
        return {}

    try:
        state = json.loads(stdout)
        return {
            "container_name": service_name,
            "status": state.get("Status", "unknown"),
            "running": state.get("Running", False),
            "restart_count": state.get("RestartCount", 0),
            "oom_killed": state.get("OOMKilled", False),
        }
    except:
        # Fallback: docker stats
        _, stdout, _ = run_cmd(
            f"docker stats --no-stream {service_name} 2>/dev/null",
            timeout=5,
            silent=True,
        )
        lines = stdout.strip().split("\n")
        if len(lines) < 2:
            return {}

        data = lines[1].split()
        return {
            "container_name": service_name,
            "cpu_pct": data[2] if len(data) > 2 else "N/A",
            "memory_usage": data[3] if len(data) > 3 else "N/A",
            "memory_pct": data[5] if len(data) > 5 else "N/A",
        }


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

    Improved per DeepSeek R1: exponential backoff with jitter.
    """
    latencies = []
    for attempt in range(max_retries):
        start = time.time()
        try:
            # Use curl with short timeout, parse HTTP status
            returncode, stdout, _ = run_cmd(
                f"curl -s -o /dev/null -w '%{{http_code}}' {endpoint} --max-time {timeout}",
                timeout=timeout + 2,
                silent=True,
            )
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)

            # Success if 200-299
            if returncode == "200":
                return True, latency_ms

            # Exponential backoff: 2^attempt seconds, e.g., 1s, 2s, 4s
            if attempt < max_retries - 1:
                wait_time = 2**attempt + (attempt * 0.5)  # jitter
                time.sleep(wait_time)
        except:
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


def docker_up_services(services: List[str], mode: str = "low_power") -> Tuple[int, str]:
    """Bring up docker compose services."""
    svc_str = " ".join(services)
    cmd = f"docker compose up -d {svc_str}"
    rc, stdout, stderr = run_cmd(cmd, timeout=30)
    return rc, stdout + stderr


def docker_down_services(services: List[str]) -> Tuple[int, str]:
    """Stop docker compose services."""
    svc_str = " ".join(services)
    cmd = f"docker compose down -v {svc_str} 2>/dev/null || true"
    rc, stdout, stderr = run_cmd(cmd, timeout=30)
    return rc, stdout + stderr


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

            # Determine overall status
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
            "## Module Results",
            "",
        ]

        for module_name, result in self.results["modules"].items():
            status_emoji = (
                "✅"
                if result["status"] == "PASS"
                else "❌" if result["status"] == "FAIL" else "⚠️"
            )
            lines.append(f"### {status_emoji} {module_name}")
            lines.append("")
            lines.append(f"**Status:** {result['status']}")
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
                    lines.append(
                        f"  - RAM: {metrics['stats'].get('memory_usage', 'N/A')}"
                    )
                    lines.append(f"  - CPU: {metrics['stats'].get('cpu_pct', 'N/A')}")
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
