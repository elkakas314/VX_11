import os
import pytest


INTEGRATION_ENABLED = os.getenv("VX11_INTEGRATION", "") == "1"


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
    settings.enable_auth = False
    yield
    settings.enable_auth = prev
