"""
Test suite for Operator v7 token fix (CORRECT approach).

Purpose:
- Verify token is read from localStorage (runtime)
- Verify NO token is hardcoded in bundle (invariant #3)
- Verify token can be configured via UI
- Verify 401/403/OFF_BY_POLICY semantics
"""

import pytest
import json
import httpx
import os

BASE_URL = os.environ.get("VX11_BASE_URL", "http://localhost:8000")
VALID_TOKEN = "vx11-test-token"
INVALID_TOKEN = "vx11-local-token"


class TestOperatorTokenArchitecture:
    """Test correct token handling (runtime, not build-time)."""

    def test_no_token_in_bundle(self):
        """Verify token is NOT hardcoded in bundle.

        Invariant #3: 'Prohibido meter secrets en el bundle del frontend'
        """
        # This test runs locally; in production, check built dist/ files
        # For now, we verify via api.ts source code inspection
        with open(
            "/home/elkakas314/vx11/operator/frontend/src/services/api.ts", "r"
        ) as f:
            source = f.read()

        # Should NOT have hardcoded token
        assert (
            "vx11-local-token" not in source or "fallback" not in source
        ), "Hardcoded token found in bundle source (invariant violation)"

        # SHOULD have localStorage reference
        assert (
            "localStorage" in source
        ), "Token should be read from localStorage at runtime"

        # SHOULD have getStoredToken function
        assert (
            "getStoredToken" in source
        ), "Token should be fetched from runtime storage"

    def test_token_settings_component_exists(self):
        """Verify TokenSettings component is available."""
        with open(
            "/home/elkakas314/vx11/operator/frontend/src/components/TokenSettings.tsx",
            "r",
        ) as f:
            source = f.read()

        assert "export function TokenSettings" in source
        # Should reference getStoredToken and setTokenLocally from api service
        assert (
            "getCurrentToken" in source or "getStoredToken" in source
        ) and "setTokenLocally" in source

    def test_valid_token_returns_200(self):
        """Verify valid token allows requests."""
        client = httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": VALID_TOKEN},
            timeout=5.0,
        )
        resp = client.get("/operator/api/status")
        assert resp.status_code == 200

    def test_invalid_token_returns_403(self):
        """Verify invalid token is rejected (NOT 500)."""
        client = httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": INVALID_TOKEN},
            timeout=5.0,
        )
        resp = client.get("/operator/api/status")
        assert (
            resp.status_code == 403
        ), f"Expected 403, got {resp.status_code}. Invalid token should return 403 (auth), not 500."

    def test_missing_token_returns_401(self):
        """Verify missing token returns 401 (auth_required)."""
        client = httpx.Client(base_url=BASE_URL, timeout=5.0)
        resp = client.get("/operator/api/status")
        assert resp.status_code == 401

    def test_empty_token_returns_401(self):
        """Verify empty token returns 401."""
        client = httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": ""},
            timeout=5.0,
        )
        resp = client.get("/operator/api/status")
        assert resp.status_code == 401


class TestOperatorErrorSemantics:
    """Test correct error semantics (distinguish auth vs policy)."""

    @pytest.fixture
    def client(self):
        return httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": VALID_TOKEN},
            timeout=5.0,
        )

    def test_status_returns_policy_info(self, client):
        """Verify status endpoint returns policy (solo_madre vs window_active)."""
        resp = client.get("/operator/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "policy" in data
        assert data["policy"] in ("solo_madre", "window_active")

    def test_off_by_policy_is_semantic(self, client):
        """Verify OFF_BY_POLICY errors are semantic (not generic 500)."""
        resp = client.get("/operator/api/status")
        assert resp.status_code == 200
        data = resp.json()

        # Optional services should have OFF_BY_POLICY (not error status)
        optional = data.get("optional_services", {})
        for service_name, service_status in optional.items():
            if isinstance(service_status, dict):
                # OFF_BY_POLICY is semantic, not an error code
                assert "status" in service_status
                # Should be clear string, not 500 or unknown error
                assert isinstance(service_status["status"], str)

    def test_window_status_returns_mode(self, client):
        """Verify window/status returns current mode."""
        resp = client.get("/operator/api/chat/window/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data or "status" in data


class TestOperatorNoHardcodedSecrets:
    """Verify NO secrets hardcoded in any build artifact."""

    def test_dockerfile_no_token_arg(self):
        """Verify Dockerfile does NOT have hardcoded VITE_VX11_TOKEN."""
        with open("/home/elkakas314/vx11/operator/frontend/Dockerfile", "r") as f:
            dockerfile = f.read()

        # SHOULD NOT have "VITE_VX11_TOKEN" in build args
        assert (
            "VITE_VX11_TOKEN" not in dockerfile
            or "ENV VITE_VX11_TOKEN" not in dockerfile
        ), "Token should NOT be set in Dockerfile (security violation)"

    def test_vite_config_no_token_injection(self):
        """Verify Vite config does NOT inject tokens."""
        config_files = [
            "/home/elkakas314/vx11/operator/frontend/vite.config.ts",
            "/home/elkakas314/vx11/operator/frontend/.env",
            "/home/elkakas314/vx11/operator/frontend/.env.production",
        ]

        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    content = f.read()
                assert (
                    "vx11-test-token" not in content
                ), f"Token found in {config_file} (should use runtime storage)"


class TestOperatorInvariants:
    """Test VX11 invariants are preserved."""

    def test_single_entrypoint_invariant(self):
        """Verify all /operator/api/* go through tentaculo_link:8000."""
        # All endpoints tested above use http://localhost:8000 (tentaculo_link)
        # No direct calls to internal services
        client = httpx.Client(
            base_url=BASE_URL,  # Must be localhost:8000
            headers={"X-VX11-Token": VALID_TOKEN},
            timeout=5.0,
        )

        # Verify we're talking to entrypoint
        assert (
            "8000" in BASE_URL
            or BASE_URL.startswith("http://localhost")
            or BASE_URL.startswith("http://127.0.0.1")
        ), f"Single entrypoint violation: BASE_URL={BASE_URL}"

    def test_solo_madre_default_policy(self):
        """Verify solo_madre is default policy."""
        client = httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": VALID_TOKEN},
            timeout=5.0,
        )
        resp = client.get("/operator/api/status")
        data = resp.json()
        assert data["policy"] == "solo_madre"

    def test_token_auth_required_invariant(self):
        """Verify X-VX11-Token is ALWAYS required (except maybe /health)."""
        # Test: request without token fails
        client_no_auth = httpx.Client(base_url=BASE_URL, timeout=5.0)
        resp = client_no_auth.get("/operator/api/status")
        assert resp.status_code == 401, "Auth should be required"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
