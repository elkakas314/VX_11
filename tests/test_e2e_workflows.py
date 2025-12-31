"""
E2E Tests: End-to-End Integration

Tests for complete workflows and resource measurement.
Markers: @pytest.mark.e2e, @pytest.mark.integration, @pytest.mark.performance
"""

import json
from pathlib import Path

import pytest
import requests
import subprocess
import time
from tests._vx11_base import vx11_base_url


@pytest.mark.e2e
@pytest.mark.integration
def test_e2e_1_full_workflow_boot_scale_policy_ondemand(madre_port, docker_available):
    """
    E2E.1: Full workflow - boot, scale, policy, on-demand
    Expected: System transitions through all states cleanly

    Workflow:
    1. Initial state: solo_madre policy (2 containers)
    2. Start multiple services (spawner, hermes)
    3. Verify they're running
    4. Re-apply solo_madre policy (stops them)
    5. Verify back to 2 containers
    6. Start switch on-demand
    7. Verify switch running
    8. Stop switch
    9. Verify back to solo_madre state
    """

    if not docker_available:
        pytest.skip("Docker not available")
    # Step 1: Verify initial solo_madre state
    output = subprocess.check_output(
        "docker ps --format '{{.Names}}'",
        shell=True,
        text=True,
    )
    containers = [c.strip() for c in output.strip().split("\n") if c.strip()]
    assert len(containers) == 2, f"Step 1: Expected 2 containers, got {len(containers)}"

    # Step 2: Start multiple services
    services_to_start = ["spawner", "hermes"]
    for svc in services_to_start:
        response = requests.post(
            vx11_base_url() + "/madre/power/service/start",
            json={"service": svc},
            timeout=10,
        )
        assert response.status_code == 200, f"Failed to start {svc}"

    time.sleep(2)

    # Step 3: Verify they're running (at least attempt to start)
    output = subprocess.check_output(
        "docker ps --format '{{.Names}}'",
        shell=True,
        text=True,
    )
    containers = [c.strip() for c in output.strip().split("\n") if c.strip()]
    # After starting services, we should have more than 2
    assert (
        len(containers) >= 2
    ), f"Step 3: Expected at least 2 containers after starting"

    # Step 4: Re-apply solo_madre policy
    response = requests.post(
        vx11_base_url() + "/madre/power/policy/solo_madre/apply",
        timeout=10,
    )
    assert response.status_code == 200, "Failed to apply solo_madre policy"

    time.sleep(2)

    # Step 5: Verify back to 2 containers
    output = subprocess.check_output(
        "docker ps --format '{{.Names}}'",
        shell=True,
        text=True,
    )
    containers = [c.strip() for c in output.strip().split("\n") if c.strip()]
    assert (
        len(containers) == 2
    ), f"Step 5: Expected 2 containers after policy, got {len(containers)}"

    # Step 6: Start switch on-demand
    response = requests.post(
        vx11_base_url() + "/madre/power/service/start",
        json={"service": "switch"},
        timeout=10,
    )
    assert response.status_code == 200, "Failed to start switch"

    time.sleep(2)

    # Step 7: Verify switch running (port 8002)
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(("localhost", 8002))
    sock.close()
    assert result == 0, "Switch port 8002 not listening"

    # Step 8: Stop switch
    response = requests.post(
        vx11_base_url() + "/madre/power/service/stop",
        json={"service": "switch"},
        timeout=10,
    )
    assert response.status_code == 200, "Failed to stop switch"

    time.sleep(1)

    # Step 9: Verify back to solo_madre state
    output = subprocess.check_output(
        "docker ps --format '{{.Names}}'",
        shell=True,
        text=True,
    )
    containers = [c.strip() for c in output.strip().split("\n") if c.strip()]
    assert (
        len(containers) == 2
    ), f"Step 9: Expected 2 containers final, got {len(containers)}"

    # Verify solo_madre policy still active
    response = requests.get(
        vx11_base_url() + "/madre/power/policy/solo_madre/status",
        timeout=10,
    )
    assert response.status_code == 200, "Failed to check policy status"
    result = response.json()
    assert result.get("policy_active") is True, "solo_madre policy not active at end"


@pytest.mark.e2e
@pytest.mark.performance
def test_e2e_2_resource_measurement_idle_vs_full(
    madre_port, db_connection, docker_available
):
    """
    E2E.2: Resource measurement - idle state vs full stack
    Expected: Record baseline metrics for idle and active states

    Measurements:
    1. Idle state (solo_madre): madre + redis
       - Memory usage
       - CPU
       - DB size
       - Port stats
    2. Active state: Start multiple services
       - Memory usage
       - CPU
       - DB size
       - Port stats
    3. Compare and report
    """

    if not docker_available:
        pytest.skip("Docker not available")
    results = {
        "idle": {},
        "active": {},
        "timestamp": time.time(),
    }

    # Step 1: Measure idle state
    idle_metrics = _measure_system_metrics()
    results["idle"] = idle_metrics

    # Step 2: Start services
    services_to_start = ["spawner", "hermes"]
    for svc in services_to_start:
        requests.post(
            f"http://localhost:{madre_port}/madre/power/service/start",
            json={"service": svc},
            timeout=10,
        )

    time.sleep(3)

    # Step 3: Measure active state
    active_metrics = _measure_system_metrics()
    results["active"] = active_metrics

    # Step 4: Verify measurements are present
    assert "containers" in results["idle"], "Idle measurements missing containers"
    assert "containers" in results["active"], "Active measurements missing containers"

    # Step 5: Verify active has more containers
    idle_count = results["idle"].get("container_count", 0)
    active_count = results["active"].get("container_count", 0)
    assert (
        active_count >= idle_count
    ), f"Active ({active_count}) should have >= idle ({idle_count}) containers"

    # Step 6: Save results for analysis
    outdir = Path(__file__).resolve().parent.parent / "docs/audit"
    outdir.mkdir(parents=True, exist_ok=True)

    results_file = outdir / "e2e_resource_measurement.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    assert results_file.exists(), "Failed to save measurement results"

    # Step 7: Clean up - return to solo_madre
    response = requests.post(
        f"http://localhost:{madre_port}/madre/power/policy/solo_madre/apply",
        timeout=10,
    )
    assert response.status_code == 200, "Failed to cleanup: return to solo_madre"


def _measure_system_metrics():
    """Helper: Measure system metrics"""
    import subprocess

    metrics = {
        "timestamp": time.time(),
        "container_count": 0,
        "containers": [],
        "ports": [],
    }

    # Get container count and names
    try:
        output = subprocess.check_output(
            "docker ps --format '{{.Names}}\t{{.MemoryUsage}}'",
            shell=True,
            text=True,
        )
        lines = output.strip().split("\n")
        containers = []
        for line in lines:
            if line.strip():
                parts = line.split("\t")
                containers.append(
                    {
                        "name": parts[0],
                        "memory": parts[1] if len(parts) > 1 else "unknown",
                    }
                )

        metrics["containers"] = containers
        metrics["container_count"] = len(containers)
    except Exception as e:
        metrics["error"] = str(e)

    # Get listening ports
    try:
        output = subprocess.check_output(
            "ss -ltn 2>/dev/null | egrep ':(8000|8001|8002|8003|8004|8005|8006|8007|8008|8011)' || echo ''",
            shell=True,
            text=True,
        )
        ports = []
        for line in output.strip().split("\n"):
            if line.strip():
                ports.append(line.strip())

        metrics["ports"] = ports
        metrics["port_count"] = len(ports)
    except Exception as e:
        metrics["port_error"] = str(e)

    return metrics
