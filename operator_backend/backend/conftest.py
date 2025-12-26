"""
VX11 Operator Backend Test Configuration (conftest.py).
Fixtures for FastAPI TestClient, database sessions, auth, and VX11_MODE overrides.
"""

import asyncio
import json
import os
import pytest
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock, AsyncMock

# FastAPI TestClient
try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

# Try to import app from main_v7
try:
    from main_v7 import app
except ImportError:
    try:
        from operator_backend.backend.main_v7 import app
    except ImportError:
        app = None


# ============================================================================
# FIXTURES: Client & Auth
# ============================================================================


@pytest.fixture
def client():
    """Provide FastAPI TestClient for testing endpoints."""
    if TestClient is None or app is None:
        pytest.skip("FastAPI TestClient or app not available")
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Provide authorization headers for authenticated requests."""
    return {"Authorization": "Bearer test-token-vx11-operator"}


@pytest.fixture
def auth_token():
    """Provide bare auth token for request construction."""
    return "test-token-vx11-operator"


# ============================================================================
# FIXTURES: Database Session (Mock)
# ============================================================================


class MockSessionDB:
    """Mock database session for testing without real DB."""

    def __init__(self):
        self.data = {}

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None

    def all(self):
        return []

    def add(self, obj):
        pass

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

    async def aclose(self):
        pass


@pytest.fixture
def db_session():
    """Provide mock database session."""
    return MockSessionDB()


@pytest.fixture
def db() -> Generator:
    """Alias for db_session (some tests may use `db` directly)."""
    session = MockSessionDB()
    yield session
    session.close()


# ============================================================================
# FIXTURES: VX11_MODE Override (BLOCKER FIX for 409 errors)
# ============================================================================


@pytest.fixture
def operative_mode(monkeypatch):
    """
    Override VX11_MODE to 'operative_core' for E2E tests.
    Prevents 409 Conflict errors in test env.
    """
    monkeypatch.setenv("VX11_MODE", "operative_core")
    return


@pytest.fixture
def solo_madre_mode(monkeypatch):
    """Override VX11_MODE to 'solo_madre' for specific tests."""
    monkeypatch.setenv("VX11_MODE", "solo_madre")
    return


@pytest.fixture
def low_power_mode(monkeypatch):
    """Override VX11_MODE to 'low_power' for testing degraded scenarios."""
    monkeypatch.setenv("VX11_MODE", "low_power")
    return


# ============================================================================
# FIXTURES: SSE Mock (BLOCKER FIX for Jest/vitest infinite stream)
# ============================================================================


@pytest.fixture
def mock_sse_stream():
    """
    Mock SSE stream that yields N events then closes.
    Prevents infinite loop in tests.
    """

    async def stream_generator(event_count: int = 5, delay: float = 0.05):
        """Generate mock SSE events with a limit."""
        for i in range(event_count):
            event_data = {
                "id": i,
                "type": "event",
                "timestamp": "2025-12-26T02:15:00Z",
                "source": "test",
                "message": f"Test event {i}",
                "request_id": f"test-req-{i}",
            }
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(delay)

    return stream_generator


@pytest.fixture
def mock_sse_heartbeat():
    """Mock heartbeat SSE events."""

    async def heartbeat_generator(count: int = 3):
        for i in range(count):
            heartbeat = {
                "type": "heartbeat",
                "timestamp": "2025-12-26T02:15:00Z",
                "request_id": f"hb-{i}",
            }
            yield f"data: {json.dumps(heartbeat)}\n\n"
            await asyncio.sleep(0.2)

    return heartbeat_generator


# ============================================================================
# FIXTURES: Request Context & Tracking
# ============================================================================


@pytest.fixture
def request_context():
    """Provide mock request context with route_taken and request_id tracking."""
    return {
        "request_id": "test-req-12345",
        "route_taken": "operator_backend:chat",
        "degraded": False,
        "mode": "operative_core",
    }


# ============================================================================
# FIXTURES: Mock Providers (for FASE C: DeepSeek R1)
# ============================================================================


@pytest.fixture
def mock_deepseek_provider():
    """Mock DeepSeek R1 provider for testing without API calls."""

    async def call_deepseek(prompt: str) -> str:
        return f"Mock DeepSeek response to: {prompt[:50]}..."

    return call_deepseek


@pytest.fixture
def mock_fallback_provider():
    """Mock fallback provider (when DeepSeek disabled/offline)."""

    async def call_fallback(prompt: str) -> str:
        return f"Fallback response to: {prompt[:50]}..."

    return call_fallback


@pytest.fixture
def language_model_selector(
    monkeypatch, mock_deepseek_provider, mock_fallback_provider
):
    """Mock language model selector with provider routing."""

    class MockSelector:
        def __init__(self, deepseek_enabled: bool = True, offline: bool = False):
            self.deepseek_enabled = deepseek_enabled
            self.offline_mode = offline
            self.deepseek_token = "sk-test-deepseek"

        async def select_provider(self, prompt: str):
            if self.offline_mode or not self.deepseek_enabled:
                return await mock_fallback_provider(prompt)
            elif self.deepseek_token:
                return await mock_deepseek_provider(prompt)
            else:
                return await mock_fallback_provider(prompt)

    return MockSelector()


# ============================================================================
# MARKERS: Test Categories for selective execution
# ============================================================================


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "sse_stream: mark test as requiring SSE stream mock"
    )
    config.addinivalue_line(
        "markers", "operative_only: mark test as requiring operative_core mode"
    )
    config.addinivalue_line(
        "markers", "timeout: mark test with explicit timeout (prevent hangs)"
    )
    config.addinivalue_line("markers", "deepseek: mark test as using DeepSeek provider")


# ============================================================================
# HOOKS: Auto-apply fixtures based on markers
# ============================================================================


def pytest_runtest_setup(item):
    """Auto-apply operative_mode fixture to tests marked with @pytest.mark.operative_only."""
    if "operative_only" in item.keywords:
        item.fixturenames.append("operative_mode")


# ============================================================================
# EVENT LOOP (asyncio support)
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Provide event loop for async tests."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    yield loop
    loop.close()


# ============================================================================
# HELPER: Utility to consume N SSE events safely
# ============================================================================


def consume_sse_events(response, max_events: int = 5):
    """
    Safely consume SSE events from response with event limit.
    Prevents infinite stream hangs in tests.
    """
    events = []
    count = 0

    for line in response.iter_lines():
        if count >= max_events:
            break
        if line.startswith(b"data: "):
            try:
                event_data = json.loads(line[6:].decode())
                events.append(event_data)
                count += 1
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    return events
