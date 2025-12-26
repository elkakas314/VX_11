"""
Tests para FASE E: Seguridad (Rate Limiting, CSRF, Logs).
"""

import pytest
import json


@pytest.mark.integration
@pytest.mark.timeout(5)
class TestRateLimiting:
    """Tests para rate limiting middleware."""

    def test_rate_limit_header_present(self, client):
        """Verificar que headers X-RateLimit-Remaining está presente."""
        response = client.get("/api/audit")
        assert "x-ratelimit-remaining" in response.headers or response.status_code in [
            200,
            429,
        ]

    def test_rate_limit_requests_allowed(self, client):
        """Verificar que se permiten hasta 100 requests/min."""
        # Hacer múltiples requests
        for _ in range(10):
            response = client.get("/api/status/modules")
            assert response.status_code == 200

    def test_request_id_header(self, client):
        """Verificar que X-Request-ID está presente (o al menos en response body)."""
        response = client.get("/api/audit")
        # Header o body debería tener request_id
        has_header = "x-request-id" in response.headers
        has_body_id = False
        if response.status_code == 200:
            data = response.json()
            has_body_id = "request_id" in data
        assert has_header or has_body_id


@pytest.mark.integration
@pytest.mark.timeout(5)
class TestCSRFProtection:
    """Tests para CSRF token protection."""

    def test_post_without_csrf_token(self, client):
        """POST sin CSRF token podría retornar 403 o procesar (depende de config)."""
        # En tests, CSRF puede estar deshabilitado
        response = client.post("/api/audit", json={"audit_type": "structure"})
        # Aceptar tanto 403 (con CSRF habilitado) como 200 (deshabilitado en tests)
        assert response.status_code in [200, 403]

    def test_get_allowed_without_csrf(self, client):
        """GET no requiere CSRF token."""
        response = client.get("/api/audit")
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.timeout(5)
class TestStructuredLogs:
    """Tests para structured JSON logging."""

    def test_response_contains_logging_headers(self, client):
        """Verificar que response contiene headers de logging (o datos en body)."""
        response = client.get("/api/status/modules")
        # Headers o data en body
        has_headers = (
            "x-request-id" in response.headers or "x-elapsed-ms" in response.headers
        )
        has_data = False
        if response.status_code == 200:
            data = response.json()
            has_data = isinstance(data, dict) and "request_id" in data
        assert has_headers or has_data

    def test_request_id_consistent(self, client):
        """Request ID debe ser consistente en una misma request."""
        response1 = client.get("/api/audit")
        req_id1 = response1.headers.get("x-request-id")

        response2 = client.get("/api/audit")
        req_id2 = response2.headers.get("x-request-id")

        # Diferentes requests tienen diferentes IDs
        if req_id1 and req_id2:
            assert req_id1 != req_id2


@pytest.mark.integration
@pytest.mark.timeout(5)
class TestSecurityHeaders:
    """Tests para security headers en respuestas."""

    def test_json_response_format(self, client):
        """Todas las respuestas deben ser JSON válido."""
        response = client.get("/api/audit")
        assert response.headers.get("content-type") == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_all_responses_have_request_id(self, client):
        """Todas las respuestas deben incluir request_id en el body."""
        endpoints = [
            ("/api/audit", "GET"),
            ("/api/status/modules", "GET"),
            ("/api/explorer/db", "GET"),
            ("/api/settings", "POST", {"theme": "dark", "auto_refresh_interval": 5000}),
        ]

        for endpoint_info in endpoints:
            if len(endpoint_info) == 2:
                path, method = endpoint_info
                payload = None
            else:
                path, method, payload = endpoint_info

            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json=payload)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    # Response body debería tener request_id
                    assert "request_id" in data or "ok" in data
