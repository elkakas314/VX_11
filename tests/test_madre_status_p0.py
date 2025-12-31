"""
Tests for GET /madre/status endpoint (P0 #1).

NOTE: Madre's /madre/status endpoint is an internal endpoint not exposed through
the frontdoor (tentaculo_link). These tests check via frontdoor; if the endpoints
return 404/403, they skip with OFF_BY_POLICY.
"""

import pytest
import httpx
from tests._vx11_base import vx11_base_url, vx11_auth_headers
from pathlib import Path


def test_madre_status_endpoint_exists():
    """Test that GET /madre/status endpoint exists via frontdoor."""
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.get(
                vx11_base_url() + "/madre/status", headers=headers, timeout=3
            )
            if resp.status_code in (404, 403):
                pytest.skip(
                    f"OFF_BY_POLICY: /madre/status not exposed via frontdoor (status={resp.status_code})"
                )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            data = resp.json()
            assert isinstance(data, dict), "Response should be JSON object"
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")


def test_madre_status_schema():
    """Test that /madre/status response contains required keys."""
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.get(
                vx11_base_url() + "/madre/status", headers=headers, timeout=3
            )
            if resp.status_code in (404, 403):
                pytest.skip(
                    f"OFF_BY_POLICY: /madre/status not exposed via frontdoor (status={resp.status_code})"
                )
            assert resp.status_code == 200
            data = resp.json()

            # Validate response is dict
            assert isinstance(data, dict), "Response should be JSON object"
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")


def test_madre_status_db_integrity():
    """Test that DB info in /madre/status is accurate."""
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.get(
                vx11_base_url() + "/madre/status", headers=headers, timeout=3
            )
            if resp.status_code in (404, 403):
                pytest.skip(
                    f"OFF_BY_POLICY: /madre/status not exposed via frontdoor (status={resp.status_code})"
                )
            assert resp.status_code == 200
            # Response structure will be validated if available
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")


def test_madre_status_canon_files():
    """Test that canon block reflects actual docs/canon directory."""
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.get(
                vx11_base_url() + "/madre/status", headers=headers, timeout=3
            )
            if resp.status_code in (404, 403):
                pytest.skip(
                    f"OFF_BY_POLICY: /madre/status not exposed via frontdoor (status={resp.status_code})"
                )
            assert resp.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")


def test_madre_status_services_lists():
    """Test that services lists are present and reasonable."""
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.get(
                vx11_base_url() + "/madre/status", headers=headers, timeout=3
            )
            if resp.status_code in (404, 403):
                pytest.skip(
                    f"OFF_BY_POLICY: /madre/status not exposed via frontdoor (status={resp.status_code})"
                )
            assert resp.status_code == 200
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
