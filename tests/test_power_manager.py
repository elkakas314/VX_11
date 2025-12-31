"""
P0 Tests: Power Manager & Docker Compose

Tests for container-level control via docker compose.
Markers: @pytest.mark.p0, @pytest.mark.docker, @pytest.mark.power_manager
"""

import pytest
import subprocess
import json


@pytest.mark.p0
@pytest.mark.docker
def test_p0_1_docker_compose_default_state(docker_state, docker_available):
    """
    P0.1: Verify default docker compose state
    Expected: 2 containers (madre, redis)
    """
    if not docker_available:
        pytest.skip("Docker not available")
    assert docker_state is not None, "Docker state not available"
    assert (
        len(docker_state) >= 2
    ), f"Expected at least 2 containers, got {len(docker_state)}: {docker_state}"

    # Check that madre and redis are in the list
    container_names = [c.lower() for c in docker_state]
    assert any(
        "madre" in c for c in container_names
    ), f"madre not found in {docker_state}"
    assert any(
        "redis" in c for c in container_names
    ), f"redis not found in {docker_state}"


@pytest.mark.p0
@pytest.mark.docker
@pytest.mark.power_manager
def test_p0_2_solo_madre_policy_state(docker_state, docker_available):
    """
    P0.2: Verify solo_madre policy has been applied
    Expected: Only madre + redis running, no other services
    """
    if not docker_available:
        pytest.skip("Docker not available")
    containers = [c for c in docker_state if c.strip()]

    # Should have exactly 2: madre, redis
    assert (
        len(containers) == 2
    ), f"Expected 2 containers, got {len(containers)}: {containers}"

    # Should have madre and redis
    container_names_lower = [c.lower() for c in containers]
    assert any(
        "madre" in c for c in container_names_lower
    ), f"madre not found in {containers}"
    assert any(
        "redis" in c for c in container_names_lower
    ), f"redis not found in {containers}"


@pytest.mark.p0
@pytest.mark.docker
@pytest.mark.power_manager
def test_p0_3_poder_ports_listening(docker_project_name, docker_available):
    """
    P0.3: Verify correct ports are listening
    Expected: 8001 (madre), 6379 (redis)
    """
    if not docker_available:
        pytest.skip("Docker not available")
    import socket

    ports = [(8001, "madre"), (6379, "redis")]

    for port, service in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", port))
        sock.close()

        assert result == 0, f"Port {port} ({service}) not listening"
