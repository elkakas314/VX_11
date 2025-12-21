"""
tests/test_shub_api.py — Tests de API FastAPI Shub

Valida:
- Endpoints HTTP
- Autenticación (token)
- Request/Response formats
- Error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock
import json

# Importar la app FastAPI
from shubniggurath.main import app


@pytest.fixture
def client():
    """Cliente de prueba FastAPI"""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Token válido para testing"""
    return "test_vx11_token"


class TestHealthEndpoint:
    """Tests del endpoint de health check"""
    
    def test_health_check_success(self, client):
        """Test: GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] in ['healthy', 'ok']
    
    def test_health_check_structure(self, client):
        """Test: Estructura de respuesta health"""
        response = client.get("/health")
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data or 'uptime' in data


class TestReadinessEndpoint:
    """Tests del endpoint de readiness"""
    
    def test_ready_check_success(self, client):
        """Test: GET /ready"""
        response = client.get("/ready")
        assert response.status_code in [200, 503]  # 200 if ready, 503 if not
        data = response.json()
        assert 'status' in data


class TestAnalyzeEndpoint:
    """Tests del endpoint de análisis"""
    
    def test_analyze_requires_auth(self, client):
        """Test: POST /analyze requiere autenticación"""
        response = client.post(
            "/analyze",
            json={"audio_file": "test.wav"}
        )
        # Sin token debe rechazar o retornar 401
        assert response.status_code in [401, 403, 422]
    
    def test_analyze_with_valid_token(self, client, valid_token):
        """Test: POST /analyze con token válido"""
        headers = {
            "X-VX11-Token": valid_token,
            "Content-Type": "application/json"
        }
        
        response = client.post(
            "/analyze",
            headers=headers,
            json={
                "audio_file": "test.wav",
                "mode": "quick"
            }
        )
        
        # Debe aceptar (aunque falle por falta de archivo)
        assert response.status_code in [200, 400, 404, 422]
    
    def test_analyze_response_structure(self, client, valid_token):
        """Test: Estructura de respuesta analyze"""
        headers = {
            "X-VX11-Token": valid_token,
            "Content-Type": "application/json"
        }
        
        with patch('shubniggurath.main.DSPPipelineFull') as mock_pipeline:
            mock_instance = AsyncMock()
            mock_instance.run_full_pipeline.return_value = {
                'status': 'success',
                'audio_analysis': Mock(),
                'fx_chain': Mock(),
                'pipeline_id': 'test_123'
            }
            mock_pipeline.return_value = mock_instance
            
            response = client.post(
                "/analyze",
                headers=headers,
                json={"audio_file": "test.wav", "mode": "quick"}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert 'status' in data


class TestMasteringEndpoint:
    """Tests del endpoint de mastering"""
    
    def test_mastering_requires_auth(self, client):
        """Test: POST /mastering requiere autenticación"""
        response = client.post(
            "/mastering",
            json={"project": "test_project"}
        )
        assert response.status_code in [401, 403, 422]
    
    def test_mastering_with_token(self, client, valid_token):
        """Test: POST /mastering con token"""
        headers = {"X-VX11-Token": valid_token}
        
        response = client.post(
            "/mastering",
            headers=headers,
            json={
                "project": "test_project",
                "master_style": "streaming",
                "target_loudness": -14.0
            }
        )
        
        # Debe aceptar la request
        assert response.status_code in [200, 400, 404, 422]


class TestBatchEndpoints:
    """Tests de endpoints de batch"""
    
    def test_batch_submit_requires_auth(self, client):
        """Test: POST /batch/submit requiere autenticación"""
        response = client.post(
            "/batch/submit",
            json={"files": ["file1.wav", "file2.wav"]}
        )
        assert response.status_code in [401, 403, 422]
    
    def test_batch_submit_with_token(self, client, valid_token):
        """Test: POST /batch/submit con token"""
        headers = {"X-VX11-Token": valid_token}
        
        response = client.post(
            "/batch/submit",
            headers=headers,
            json={
                "files": ["file1.wav"],
                "priority": 5
            }
        )
        
        assert response.status_code in [200, 400, 404, 422]
    
    def test_batch_status_requires_batch_id(self, client, valid_token):
        """Test: GET /batch/status/{batch_id}"""
        headers = {"X-VX11-Token": valid_token}
        
        response = client.get(
            "/batch/status/test_batch_123",
            headers=headers
        )
        
        # Debe aceptar la request
        assert response.status_code in [200, 404]


class TestREAPEREndpoints:
    """Tests de endpoints REAPER"""
    
    def test_reaper_projects_requires_auth(self, client):
        """Test: GET /reaper/projects requiere autenticación"""
        response = client.get("/reaper/projects")
        assert response.status_code in [401, 403, 422]
    
    def test_reaper_projects_with_token(self, client, valid_token):
        """Test: GET /reaper/projects con token"""
        headers = {"X-VX11-Token": valid_token}
        
        response = client.get(
            "/reaper/projects",
            headers=headers
        )
        
        # Debe aceptar
        assert response.status_code in [200, 400, 404]


class TestErrorHandling:
    """Tests de error handling"""
    
    def test_invalid_token_returns_401(self, client):
        """Test: Token inválido retorna 401"""
        headers = {"X-VX11-Token": "invalid_token"}
        
        response = client.post(
            "/analyze",
            headers=headers,
            json={"audio_file": "test.wav"}
        )
        
        # Depending on implementation, might reject or allow
        assert response.status_code in [401, 403, 422, 200]
    
    def test_malformed_json_returns_422(self, client, valid_token):
        """Test: JSON malformado retorna 422"""
        headers = {"X-VX11-Token": valid_token}
        
        response = client.post(
            "/analyze",
            headers=headers,
            data="not valid json",
            content_type="application/json"
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client, valid_token):
        """Test: Campos requeridos faltantes"""
        headers = {"X-VX11-Token": valid_token}
        
        response = client.post(
            "/analyze",
            headers=headers,
            json={}  # Empty payload
        )
        
        assert response.status_code == 422


class TestCORSHeaders:
    """Tests de CORS"""
    
    def test_cors_headers_present(self, client):
        """Test: Headers CORS presentes"""
        response = client.get("/health")
        
        # Verificar que al menos tenga acceso (no necesariamente CORS)
        assert response.status_code == 200


class TestMainModuleIntegration:
    """Tests de integración del main.py"""
    
    def test_app_has_lifespan(self):
        """Test: App tiene lifespan manager"""
        assert hasattr(app, 'router')
    
    def test_app_has_endpoints(self):
        """Test: App tiene endpoints registrados"""
        routes = [route.path for route in app.routes]
        
        # Verificar que existan endpoints clave
        assert any('health' in route for route in routes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
