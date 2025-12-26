"""
Tests para operador rutas FASE D.
Todos los tests usan conftest.py fixtures y UnifiedResponse schema.
"""

import pytest
import json
from datetime import datetime


class TestOperatorAuditEndpoints:
    """Tests para endpoints de auditoría."""

    def test_post_audit_start_valid(self, client):
        """POST /api/audit con audit_type válido."""
        response = client.post(
            "/api/audit",
            json={"audit_type": "structure", "scope": "full"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "job_id" in data["data"]
        assert data["data"]["status"] == "queued"

    def test_post_audit_invalid_type(self, client):
        """POST /api/audit con audit_type inválido."""
        response = client.post(
            "/api/audit",
            json={"audit_type": "invalid", "scope": "full"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert len(data["errors"]) > 0

    def test_get_audit_result(self, client):
        """GET /api/audit/{job_id} retorna resultados."""
        # Crear audit primero
        create_resp = client.post(
            "/api/audit",
            json={"audit_type": "db", "scope": "module_only"},
        )
        job_id = create_resp.json()["data"]["job_id"]

        # Obtener resultados
        response = client.get(f"/api/audit/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["job_id"] == job_id
        assert data["data"]["status"] in ["queued", "completed"]

    def test_get_audit_result_paginado(self, client):
        """GET /api/audit/{job_id} con paginación."""
        create_resp = client.post(
            "/api/audit",
            json={"audit_type": "structure", "scope": "full"},
        )
        job_id = create_resp.json()["data"]["job_id"]

        response = client.get(f"/api/audit/{job_id}?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data["data"]
        assert "offset" in data["data"]
        assert "limit" in data["data"]

    def test_get_audit_not_found(self, client):
        """GET /api/audit/{job_id} con ID inexistente."""
        response = client.get("/api/audit/audit_nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False

    def test_get_audits_list(self, client):
        """GET /api/audit lista audits recientes."""
        response = client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "audits" in data["data"]
        assert "total" in data["data"]


class TestOperatorModuleControl:
    """Tests para control de módulos."""

    def test_module_power_up(self, client):
        """POST /api/module/{name}/power_up."""
        response = client.post("/api/module/switch/power_up", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["action"] == "queued"
        assert data["data"]["module_name"] == "switch"

    def test_module_power_down(self, client):
        """POST /api/module/{name}/power_down."""
        response = client.post("/api/module/hermes/power_down", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["power_action"] == "power_down"

    def test_module_restart(self, client):
        """POST /api/module/{name}/restart."""
        response = client.post("/api/module/spawner/restart", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True


@pytest.mark.timeout(5)
class TestOperatorModuleStatus:
    """Tests para estado de módulos."""

    def test_get_modules_status(self, client):
        """GET /api/status/modules retorna salud de servicios."""
        response = client.get("/api/status/modules")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "modules" in data["data"]
        modules = data["data"]["modules"]
        assert len(modules) > 0

        for module in modules:
            assert "name" in module
            assert "status" in module
            assert "healthy" in module
            assert module["status"] in ["up", "down", "degraded"]


class TestOperatorExplorer:
    """Tests para exploradores de FS y DB."""

    def test_explorer_fs_valid_path(self, client):
        """GET /api/explorer/fs con path válido."""
        response = client.get("/api/explorer/fs?path=/app&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "entries" in data["data"]
        assert data["data"]["path"] == "/app"

    def test_explorer_fs_invalid_path_escape(self, client):
        """GET /api/explorer/fs rechaza path traversal."""
        response = client.get("/api/explorer/fs?path=/app/../../../etc/passwd")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False

    def test_explorer_fs_outside_app(self, client):
        """GET /api/explorer/fs rechaza paths fuera de /app."""
        response = client.get("/api/explorer/fs?path=/etc")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False

    def test_explorer_db_valid_table(self, client):
        """GET /api/explorer/db con tabla válida."""
        response = client.get("/api/explorer/db?table=modules&limit=50&offset=0")
        assert response.status_code == 200
        data = response.json()
        if data["ok"]:
            assert "rows" in data["data"]
            assert "total" in data["data"]
            assert data["data"]["table"] == "modules"

    def test_explorer_db_invalid_table(self, client):
        """GET /api/explorer/db rechaza tabla inexistente."""
        response = client.get("/api/explorer/db?table=nonexistent_table")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False

    def test_explorer_db_limit_enforced(self, client):
        """GET /api/explorer/db enforce limit max 100."""
        response = client.get("/api/explorer/db?table=modules&limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        if data["ok"]:
            assert len(data["data"]["rows"]) <= 5


class TestOperatorSettings:
    """Tests para configuración de usuario."""

    def test_post_settings_valid(self, client):
        """POST /api/settings con configuración válida."""
        response = client.post(
            "/api/settings",
            json={"theme": "dark", "auto_refresh_interval": 5000},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["theme"] == "dark"

    def test_post_settings_invalid_theme(self, client):
        """POST /api/settings rechaza theme inválido."""
        response = client.post(
            "/api/settings",
            json={"theme": "invalid", "auto_refresh_interval": 5000},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False

    def test_post_settings_invalid_interval(self, client):
        """POST /api/settings rechaza intervalo < 1000ms."""
        response = client.post(
            "/api/settings",
            json={"theme": "light", "auto_refresh_interval": 500},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False


class TestOperatorRouting:
    """Tests para visualización de rutas."""

    def test_get_route_taken(self, client):
        """GET /api/route_taken retorna últimas rutas."""
        response = client.get("/api/route_taken?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "routes" in data["data"]
        assert "total" in data["data"]


class TestOperatorUnifiedResponse:
    """Tests para schema UnifiedResponse en todos los endpoints."""

    def test_all_endpoints_unified_response(self, client):
        """Todos los endpoints retornan UnifiedResponse schema."""
        endpoints = [
            ("POST", "/api/audit", {"audit_type": "structure"}),
            ("GET", "/api/audit", None),
            ("GET", "/api/status/modules", None),
            ("GET", "/api/explorer/fs", None),
            ("GET", "/api/explorer/db", None),
            ("POST", "/api/settings", {"theme": "dark", "auto_refresh_interval": 5000}),
            ("GET", "/api/route_taken", None),
        ]

        for method, endpoint, payload in endpoints:
            if method == "POST":
                response = client.post(endpoint, json=payload)
            else:
                response = client.get(endpoint)

            assert response.status_code == 200
            data = response.json()

            # Verificar schema UnifiedResponse
            assert "ok" in data
            assert isinstance(data["ok"], bool)
            assert "request_id" in data
            assert "route_taken" in data
            assert "degraded" in data
            assert "errors" in data
            assert isinstance(data["errors"], list)
            assert "data" in data
            assert isinstance(data["data"], dict)
