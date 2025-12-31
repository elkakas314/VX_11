import os
import pytest
import subprocess
import shutil
import sqlite3
import time
import requests
from pathlib import Path


# Default: integration tests OFF unless explicitly enabled.
INTEGRATION_ENABLED = os.getenv("VX11_INTEGRATION", "0") == "1"

# Ensure deterministic testing defaults.
os.environ.setdefault("VX11_TESTING_MODE", "1")
os.environ.setdefault("VX11_TENTACULO_LINK_TOKEN", "vx11-local-token")


def pytest_configure(config):
    """Register custom markers for VX11 tests"""
    config.addinivalue_line("markers", "p0: Critical tests (must pass)")
    config.addinivalue_line("markers", "p1: Important tests (should pass)")
    config.addinivalue_line("markers", "e2e: End-to-end integration tests")
    config.addinivalue_line("markers", "docker: Docker-related tests")
    config.addinivalue_line("markers", "power_manager: Power Manager API tests")
    config.addinivalue_line("markers", "health: Health endpoint tests")
    config.addinivalue_line("markers", "db: Database tests")
    config.addinivalue_line("markers", "canon: Canonical specs tests")
    config.addinivalue_line("markers", "performance: Performance measurement")
    config.addinivalue_line("markers", "idempotence: Idempotence tests")
    config.addinivalue_line("markers", "security: Security & allowlist tests")
    config.addinivalue_line(
        "markers", "integration: Integration tests (skip by default)"
    )
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "ui: UI tests")


def pytest_collection_modifyitems(config, items):
    """Skip tests marked as 'integration' unless VX11_INTEGRATION=1."""
    if INTEGRATION_ENABLED:
        return
    skip = pytest.mark.skip(
        reason="Integration tests skipped by default. Set VX11_INTEGRATION=1 to run."
    )
    for item in list(items):
        if "integration" in item.keywords:
            item.add_marker(skip)


import pytest
from config.settings import settings


@pytest.fixture(scope="session", autouse=True)
def disable_auth_for_tests():
    """
    Disable auth during pytest to allow TestClient calls without headers.
    Override by setting settings.enable_auth True in specific tests if needed.
    """
    prev = settings.enable_auth
    prev_testing = settings.testing_mode
    settings.enable_auth = False
    settings.testing_mode = True
    yield
    settings.enable_auth = prev
    settings.testing_mode = prev_testing


# ============================================================================
# VX11 TEST FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def docker_project_name():
    """Docker compose project name"""
    return "vx11"


@pytest.fixture(scope="session")
def docker_available():
    """Check if docker is available for integration tests."""
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


@pytest.fixture(scope="session")
def db_path():
    """Path to VX11 database"""
    return Path(__file__).resolve().parent.parent / "data/runtime/vx11.db"


@pytest.fixture(scope="session")
def madre_port():
    """Madre service port"""
    return 8001


@pytest.fixture(scope="session")
def redis_port():
    """Redis service port"""
    return 6379


@pytest.fixture
def docker_state(docker_project_name):
    """Get current docker compose state"""
    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-p",
                docker_project_name,
                "ps",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Filter out empty lines
            containers = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
            return containers
        else:
            pytest.skip("Docker not available")
    except Exception as e:
        pytest.skip(f"Docker error: {e}")


@pytest.fixture
def db_connection(db_path):
    """Get DB connection to VX11 database"""
    if not db_path.exists():
        pytest.skip(f"Database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def port_waiter():
    """Fixture to wait for port to be listening"""

    def wait_for_port(port, timeout=10, max_retries=20):
        """Wait for port to be listening"""
        import socket

        start = time.time()
        retries = 0

        while retries < max_retries:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                sock.close()

                if result == 0:
                    return True

                elapsed = time.time() - start
                if elapsed > timeout:
                    return False

                time.sleep(0.5)
                retries += 1
            except Exception:
                time.sleep(0.5)
                retries += 1

        return False

    return wait_for_port


@pytest.fixture
def madre_health(madre_port):
    """Check madre health endpoint"""
    try:
        resp = requests.get(f"http://localhost:{madre_port}/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"status": "error", "code": resp.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@pytest.fixture
def db_integrity_check(db_connection):
    """Run DB integrity checks"""
    try:
        cursor = db_connection.cursor()

        cursor.execute("PRAGMA quick_check;")
        quick_result = cursor.fetchone()[0]

        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]

        return {
            "quick_check": quick_result,
            "integrity_check": integrity_result,
        }
    except Exception as e:
        return {"error": str(e)}


@pytest.fixture
def critical_tables(db_connection):
    """Check critical tables exist"""
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = {row[0] for row in cursor.fetchall()}

    critical = [
        "module_status",
        "copilot_actions_log",
        "switch_queue_v2",
        "daughters",
        "scheduler_history",
    ]

    return {
        "existing": existing_tables,
        "critical": critical,
        "coverage": {t: t in existing_tables for t in critical},
        "missing": [t for t in critical if t not in existing_tables],
    }
