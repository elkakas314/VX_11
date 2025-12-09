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
