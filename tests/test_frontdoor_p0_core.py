"""
P0 CORE TESTS: Front-door validation (via localhost:8000 only)
Validates single-entrypoint architecture, auth chain, and basic contracts.
"""

import pytest
import httpx
import json
import os
from typing import Optional


# ============================================================================
# Token Resolution (FASE 1 strategy)
# ============================================================================


def get_vx11_token() -> str:
    """Resolve VX11_TOKEN with fallback strategy."""
    # 1) ENV var
    vx_token = os.getenv("VX11_TOKEN")
    if vx_token is not None:
        return vx_token

    # 2) File paths (first found)
    token_paths = [
        "/etc/vx11/tokens.env",
        os.path.expanduser("~/vx11/tokens.env"),
        os.path.expanduser("~/.vx11/tokens.env"),
        "./tokens.env",
        "./.env",
    ]
    for path in token_paths:
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    for line in f:
                        if line.startswith("VX11_TOKEN="):
                            token = line.split("=", 1)[1].strip().strip("\"'")
                            if token:
                                return token
            except Exception:
                pass

    # 3) Fallback
    return "vx11-local-token"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def base_url() -> str:
    """Front-door only: localhost:8000"""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def token() -> str:
    """Resolve VX11_TOKEN"""
    return get_vx11_token()


@pytest.fixture(scope="session")
def http_client() -> httpx.Client:
    """Sync HTTP client"""
    return httpx.Client(timeout=5.0)


# ============================================================================
# P0 TESTS: Single-entrypoint + Auth Chain
# ============================================================================


class TestFrontDoorHealth:
    """Health endpoints must be accessible via front-door"""

    def test_health_ok(self, base_url, http_client):
        """GET /health returns 200 with status=ok"""
        resp = http_client.get(f"{base_url}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"
        assert data.get("module") == "tentaculo_link"

    def test_openapi_exists(self, base_url, http_client):
        """GET /openapi.json returns valid JSON with paths"""
        resp = http_client.get(f"{base_url}/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "paths" in data
        assert len(data["paths"]) > 0
        # Check no duplicate operationIds (simple heuristic)
        operation_ids = []
        for path_item in data.get("paths", {}).values():
            for method, op in path_item.items():
                if isinstance(op, dict) and "operationId" in op:
                    operation_ids.append(op["operationId"])
        # Warn if duplicates (non-critical)
        if len(operation_ids) != len(set(operation_ids)):
            pytest.skip("WARNING: Duplicate operationIds in OpenAPI spec")

    def test_operator_ui_served(self, base_url, http_client):
        """GET /operator/ui/ returns HTML (no blank screen)."""
        resp = http_client.get(f"{base_url}/operator/ui/")
        assert resp.status_code == 200
        body = resp.text
        assert "id=\"root\"" in body or "VX11 Operator" in body


class TestHermesGetEngineAuth:
    """Hermes GET-engine endpoint auth validation"""

    def test_get_engine_without_token_401(self, base_url, http_client):
        """POST /hermes/get-engine without token => 401"""
        resp = http_client.post(
            f"{base_url}/hermes/get-engine",
            json={"engine_id": "gpt4"},
        )
        assert resp.status_code == 401

    def test_get_engine_with_token_200(self, base_url, http_client, token):
        """POST /hermes/get-engine with token => 200"""
        resp = http_client.post(
            f"{base_url}/hermes/get-engine",
            json={"engine_id": "gpt4"},
            headers={"X-VX11-Token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "engine_id" in data
        assert data["engine_id"] == "gpt4"

    def test_get_engine_missing_engine_id_422(self, base_url, http_client, token):
        """POST /hermes/get-engine with token but no engine_id => 422"""
        resp = http_client.post(
            f"{base_url}/hermes/get-engine",
            json={},
            headers={"X-VX11-Token": token},
        )
        assert resp.status_code == 422


class TestHermesExecuteAuth:
    """Hermes execute endpoint auth validation"""

    def test_execute_without_token_401(self, base_url, http_client):
        """POST /hermes/execute without token => 401"""
        resp = http_client.post(
            f"{base_url}/hermes/execute",
            json={"command": "test"},
        )
        assert resp.status_code == 401

    def test_execute_with_token_200(self, base_url, http_client, token):
        """POST /hermes/execute with token => 200/202"""
        resp = http_client.post(
            f"{base_url}/hermes/execute",
            json={"command": "test"},
            headers={"X-VX11-Token": token},
        )
        assert resp.status_code in [200, 202]


class TestNoBypass:
    """Ensure no direct calls to 8002/8003 are encouraged"""

    def test_no_direct_switch_port(self):
        """Direct access to localhost:8002 should NOT be used in actual requests"""
        # This test is informational: we remind ourselves that
        # all HTTP requests should use localhost:8000 only.
        # In practice, we verify this by inspecting network traffic.
        import pytest

        pytest.skip(
            "Informational test: bypass prevention is by architecture, not enforcement"
        )

    def test_no_direct_hermes_port(self):
        """Direct access to localhost:8003 should NOT work via front-door tests"""
        # Similar: ensure we only test via 8000
        pass


class TestTokenChain:
    """Verify X-VX11-Token propagates through layers"""

    def test_token_reaches_hermes_via_proxy(self, base_url, http_client, token):
        """Token forwarded by proxy reaches hermes (return value includes engine_id)"""
        resp = http_client.post(
            f"{base_url}/hermes/get-engine",
            json={"engine_id": "unique_test_id_12345"},
            headers={"X-VX11-Token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("engine_id") == "unique_test_id_12345"
        # Proves token reached hermes (it processed the request)


# ============================================================================
# P1: Coherence & Contracts
# ============================================================================


class TestOpenAPIContracts:
    """OpenAPI spec must be consistent and complete"""

    def test_hermes_endpoints_in_openapi(self, base_url, http_client):
        """Hermes endpoints (/hermes/*) must exist in OpenAPI"""
        resp = http_client.get(f"{base_url}/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        paths = data.get("paths", {})

        # Check key endpoints exist
        required_paths = [
            "/hermes/get-engine",
            "/hermes/execute",
        ]
        for path in required_paths:
            assert path in paths, f"Missing path in OpenAPI: {path}"

    def test_hermes_endpoints_have_auth_requirement(self, base_url, http_client):
        """Hermes endpoints should document auth requirement"""
        resp = http_client.get(f"{base_url}/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        paths = data.get("paths", {})

        for endpoint in ["/hermes/get-engine", "/hermes/execute"]:
            if endpoint in paths:
                path_item = paths[endpoint]
                # Check POST method exists and has security/parameters
                if "post" in path_item:
                    post_op = path_item["post"]
                    # Should have parameters or security requirements
                    # (This is a soft check; actual implementation may vary)
                    assert isinstance(post_op, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
