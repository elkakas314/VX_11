"""
Anti-regression test: Verify frontdoor helpers are available and functional.

INVARIANT: All tests must use frontdoor (http://localhost:8000) via vx11_base_url().
"""

import pytest


@pytest.mark.security
def test_frontdoor_helpers_available():
    """
    ANTI-REGRESSION: Verify frontdoor helpers can be imported and used.
    """
    # Import the helpers and verify they're callable
    from tests._vx11_base import vx11_base_url, vx11_auth_headers
    
    # Verify they return expected values
    base_url = vx11_base_url()
    assert "8000" in base_url or "localhost" in base_url
    assert isinstance(base_url, str)
    assert len(base_url) > 0
    
    # Verify auth headers
    headers = vx11_auth_headers()
    assert isinstance(headers, dict)
    assert "X-VX11-Token" in headers or "X-VX11-GW-TOKEN" in headers
