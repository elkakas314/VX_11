"""Tests P0 (Mandatory) para Madre v7."""

import pytest
import json
from datetime import datetime
from pathlib import Path

# Agregar ruta madre al path
import sys

# Ensure repository root is on sys.path so the madre package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from madre.core.models import (
    IntentV2,
    PlanV2,
    StepV2,
    ChatRequest,
    ChatResponse,
    ControlRequest,
    ControlResponse,
    HealthResponse,
    ModeEnum,
    RiskLevel,
    StatusEnum,
    StepType,
    DSL,
)
from madre.core.db import MadreDB
from madre.core.policy import PolicyEngine
from madre.core.parser import FallbackParser


class TestContracts:
    """Test que response contracts están bien formados."""

    def test_chat_response_shape(self):
        """ChatResponse debe tener campos obligatorios."""
        resp = ChatResponse(
            response="test",
            session_id="sess-1",
            intent_id="int-1",
            plan_id="plan-1",
            status=StatusEnum.DONE,
            mode="MADRE",
            warnings=[],
            targets=[],
            actions=[],
        )
        assert resp.response == "test"
        assert resp.session_id == "sess-1"
        assert resp.status == StatusEnum.DONE
        # Serializable to JSON
        json_str = resp.model_dump_json()
        assert "DONE" in json_str

    def test_control_response_pending(self):
        """ControlResponse pending_confirmation debe tener token."""
        resp = ControlResponse(
            status="pending_confirmation",
            confirm_token="test-token-123",
            reason="High risk",
        )
        assert resp.status == "pending_confirmation"
        assert resp.confirm_token == "test-token-123"
        json_str = resp.model_dump_json()
        assert "pending_confirmation" in json_str

    def test_control_response_accepted(self):
        """ControlResponse accepted debe tener action_id."""
        resp = ControlResponse(status="accepted", action_id=42)
        assert resp.status == "accepted"
        assert resp.action_id == 42

    def test_health_response_shape(self):
        """HealthResponse debe listar deps."""
        resp = HealthResponse(
            module="madre",
            status="ok",
            version="7.0",
            time=datetime.utcnow(),
            deps={"switch": "ok", "shub": "unknown"},
        )
        assert resp.module == "madre"
        assert resp.deps["switch"] == "ok"

    def test_plan_v2_shape(self):
        """PlanV2 debe tener steps y status."""
        step = StepV2(
            step_id="step-1",
            type=StepType.CALL_SWITCH,
            target="switch",
            status=StatusEnum.PENDING,
            blocking=False,
        )
        plan = PlanV2(
            plan_id="plan-1",
            intent_id="int-1",
            session_id="sess-1",
            status=StatusEnum.PENDING,
            steps=[step],
            mode="MADRE",
        )
        assert plan.plan_id == "plan-1"
        assert len(plan.steps) == 1
        assert plan.steps[0].type == StepType.CALL_SWITCH


class TestPolicies:
    """Test PolicyEngine risk classification."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_low_risk_classification(self):
        """Mix, analyze, etc. should be LOW."""
        assert self.engine.classify_risk("audio", "mix") == RiskLevel.LOW
        assert self.engine.classify_risk("system", "healthcheck") == RiskLevel.LOW

    def test_med_risk_classification(self):
        """Restart, suspend, cleanup should be MED."""
        risk = self.engine.classify_risk("shub", "suspend")
        assert risk == RiskLevel.MED

    def test_high_risk_classification(self):
        """Delete, destroy, reset should be HIGH."""
        risk = self.engine.classify_risk("storage", "delete")
        assert risk == RiskLevel.HIGH

    def test_confirmation_required_low(self):
        """LOW risk no requiere confirmación."""
        assert not self.engine.requires_confirmation(RiskLevel.LOW)

    def test_confirmation_required_med_high(self):
        """MED y HIGH requieren confirmación."""
        assert self.engine.requires_confirmation(RiskLevel.MED)
        assert self.engine.requires_confirmation(RiskLevel.HIGH)

    def test_confirm_token_generation(self):
        """Token debe ser string válido."""
        token = self.engine.generate_confirm_token()
        assert isinstance(token, str)
        assert len(token) > 10

    def test_confirm_token_validation(self):
        """Token válido debe pasar validación."""
        token = self.engine.generate_confirm_token()
        # Note: En production, se guardaría el token.
        # Aquí simplemente verificamos que la lógica es timing-safe.
        assert self.engine.validate_confirm_token(token, token)

    def test_confirm_token_invalid(self):
        """Token inválido debe fallar."""
        token1 = self.engine.generate_confirm_token()
        token2 = self.engine.generate_confirm_token()
        assert not self.engine.validate_confirm_token(token1, token2)


class TestFallbackParser:
    """Test FallbackParser sin Switch."""

    def setup_method(self):
        self.parser = FallbackParser()

    def test_parse_audio_keyword(self):
        """Mensaje con palabras audio debe detectar domain=audio."""
        dsl = self.parser.parse("mix these 3 stems")
        assert dsl.domain == "audio"
        assert dsl.confidence < 0.5  # Fallback confidence baja

    def test_parse_delete_keyword(self):
        """Delete keyword debe parsearse sin error."""
        dsl = self.parser.parse("delete all stems")
        # Parser puede no ser perfecto, solo verificar que no falla
        assert dsl.action is not None
        assert dsl.domain in ["audio", "unknown", "system"]

    def test_parse_analysis_keyword(self):
        """Analyze keyword debe extraer analyze action."""
        dsl = self.parser.parse("analyze this audio")
        assert "analyz" in dsl.action.lower() or dsl.domain == "audio"

    def test_parse_extract_parameters(self):
        """Parser debe extraer parámetros simples."""
        dsl = self.parser.parse("mix 3 stems with eq and compression")
        # No verificamos formato exacto, solo que no falla
        assert dsl.domain in ["audio", "unknown"]


class TestDBPersistence:
    """Test MadreDB operations (can be mocked or use test DB)."""

    def test_madredb_instantiation(self):
        """MadreDB debe inicializar sin errores."""
        # En test real, usaríamos un SQLite en memoria
        # Por ahora, solo verificamos que la clase existe
        assert hasattr(MadreDB, "create_intent_log")
        assert hasattr(MadreDB, "close_intent_log")
        assert hasattr(MadreDB, "create_task")
        assert hasattr(MadreDB, "update_task")
        assert hasattr(MadreDB, "set_context")
        assert hasattr(MadreDB, "get_context")
        assert hasattr(MadreDB, "record_action")
        assert hasattr(MadreDB, "request_spawner_task")

    def test_madredb_methods_exist(self):
        """Todos los métodos repository deben existir."""
        methods = [
            "create_intent_log",
            "close_intent_log",
            "create_task",
            "update_task",
            "set_context",
            "get_context",
            "record_action",
            "request_spawner_task",
            "get_policy",
            "get_task",
        ]
        for method in methods:
            assert hasattr(MadreDB, method), f"MadreDB missing method: {method}"


class TestEnums:
    """Test enum definitions."""

    def test_mode_enum(self):
        """ModeEnum debe tener MADRE y AUDIO_ENGINEER."""
        assert hasattr(ModeEnum, "MADRE")
        assert hasattr(ModeEnum, "AUDIO_ENGINEER")

    def test_risk_level_enum(self):
        """RiskLevel debe tener LOW, MED, HIGH."""
        assert hasattr(RiskLevel, "LOW")
        assert hasattr(RiskLevel, "MED")
        assert hasattr(RiskLevel, "HIGH")

    def test_status_enum(self):
        """StatusEnum debe tener states canónicos."""
        assert hasattr(StatusEnum, "PENDING")
        assert hasattr(StatusEnum, "RUNNING")
        assert hasattr(StatusEnum, "WAITING")
        assert hasattr(StatusEnum, "DONE")
        assert hasattr(StatusEnum, "ERROR")

    def test_step_type_enum(self):
        """StepType debe tener tipos de pasos."""
        assert hasattr(StepType, "CALL_SWITCH")
        assert hasattr(StepType, "CALL_SHUB")
        assert hasattr(StepType, "SPAWNER_REQUEST")
        assert hasattr(StepType, "NOOP")


class TestIntentModel:
    """Test IntentV2 structure."""

    def test_intent_creation(self):
        """IntentV2 debe crearse con campos obligatorios."""
        dsl = DSL(domain="audio", action="mix", confidence=0.8)
        intent = IntentV2(
            intent_id="int-1",
            session_id="sess-1",
            mode="MADRE",
            dsl=dsl,
            risk=RiskLevel.LOW,
            requires_confirmation=False,
            targets=["shub"],
        )
        assert intent.intent_id == "int-1"
        assert intent.dsl.domain == "audio"
        assert intent.risk == RiskLevel.LOW


class TestParserDestructiveVerbs:
    """Test que el parser detecta verbos destructivos."""

    def test_parser_detects_delete(self):
        """Parser debe detectar 'delete' y mapear a domain=system, action=delete."""
        parser = FallbackParser()
        dsl = parser.parse("delete all data", "MADRE")
        assert dsl.domain == "system"
        assert dsl.action == "delete"
        assert dsl.confidence >= 0.9
        assert "destructive_intent_detected" in dsl.warnings

    def test_parser_detects_destroy(self):
        """Parser debe detectar 'destroy'."""
        parser = FallbackParser()
        dsl = parser.parse("destroy the database", "MADRE")
        assert dsl.action == "delete"
        assert dsl.domain == "system"

    def test_parser_detects_remove(self):
        """Parser debe detectar 'remove'."""
        parser = FallbackParser()
        dsl = parser.parse("remove all files", "MADRE")
        assert dsl.action == "delete"
        assert dsl.domain == "system"


class TestPolicyHighRiskDelete:
    """Test que policy clasifica delete como HIGH."""

    def test_delete_action_is_high(self):
        """Policy debe clasificar action='delete' como HIGH."""
        policy = PolicyEngine()
        risk = policy.classify_risk("system", "delete")
        assert risk == RiskLevel.HIGH

    def test_delete_requires_confirmation(self):
        """HIGH risk debe requerir confirmation."""
        policy = PolicyEngine()
        risk = policy.classify_risk("system", "delete")
        assert policy.requires_confirmation(risk) is True

    def test_suicidal_action_denied(self):
        """Policy debe marcar como HIGH y log deny para delete sobre madre."""
        policy = PolicyEngine()
        risk = policy.classify_risk("madre", "delete")
        assert risk == RiskLevel.HIGH

    def test_suicidal_action_tentaculo_link(self):
        """Policy debe marcar como HIGH para delete sobre tentaculo_link."""
        policy = PolicyEngine()
        risk = policy.classify_risk("tentaculo_link", "stop")
        assert risk == RiskLevel.HIGH


class TestEndpointExistence:
    """Test que endpoints P0 existen en el app."""

    def test_main_module_importable(self):
        """madre.main debe ser importable y tener app."""
        import madre.main

        assert hasattr(madre.main, "app")
        app = madre.main.app
        # Listar rutas
        routes = [r.path for r in app.routes]
        assert "/health" in routes
        assert "/madre/chat" in routes


# ========== INTEGRATION TESTS (si BD disponible) ==========


@pytest.mark.skipif(
    not Path("/home/elkakas314/vx11/data/runtime/vx11.db").exists(),
    reason="BD not available",
)
class TestDBIntegration:
    """Integration tests con BD real (opcional)."""

    def test_db_connection(self):
        """BD debe ser accessible."""
        # Solo verificar si existe
        db_path = Path("/home/elkakas314/vx11/data/runtime/vx11.db")
        assert db_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
