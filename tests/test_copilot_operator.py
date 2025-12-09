"""
COPILOT OPERATOR MODE: Test Suite (FASE 6)
Tests exhaustivos para validadores y puente Copilot Operator

Cobertura:
  - Validadores individuales (5)
  - Orquestador de validación
  - Payloads válidos e inválidos
  - Edge cases
"""

import pytest
import asyncio
from datetime import datetime
from config.copilot_bridge_validator_operator import (
    validate_message_length,
    validate_metadata_format,
    validate_mode_flag,
    validate_security_constraints,
    sanitize_payload,
    CopilotOperatorBridgeValidator,
    get_validator_stats,
    build_test_payload,
)


# ============================================================================
# TESTS: VALIDATOR 1 - Message Length
# ============================================================================

class TestMessageLength:
    """Tests para validate_message_length()"""
    
    def test_valid_message(self):
        """Mensaje válido debe pasar"""
        valid, error = validate_message_length("Hello VX11")
        assert valid is True
        assert error == ""
    
    def test_empty_message(self):
        """Mensaje vacío debe fallar"""
        valid, error = validate_message_length("")
        assert valid is False
        assert "empty" in error.lower()
    
    def test_none_message(self):
        """Mensaje None debe fallar"""
        valid, error = validate_message_length(None)
        assert valid is False
    
    def test_message_too_long(self):
        """Mensaje > 16 KB debe fallar"""
        big_message = "A" * (16384 + 1)
        valid, error = validate_message_length(big_message)
        assert valid is False
        assert "too long" in error.lower()
    
    def test_message_max_length(self):
        """Mensaje exactamente 16 KB debe pasar"""
        max_message = "X" * 16384
        valid, error = validate_message_length(max_message)
        assert valid is True
    
    def test_null_bytes_in_message(self):
        """Mensaje con null bytes debe fallar"""
        message_with_null = "Hello\x00World"
        valid, error = validate_message_length(message_with_null)
        assert valid is False
        assert "null" in error.lower()


# ============================================================================
# TESTS: VALIDATOR 2 - Metadata Format
# ============================================================================

class TestMetadataFormat:
    """Tests para validate_metadata_format()"""
    
    def test_valid_metadata(self):
        """Metadata válido debe pasar"""
        metadata = {
            "source": "copilot_operator",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "context7_version": "7.0"
        }
        valid, errors = validate_metadata_format(metadata)
        assert valid is True
        assert len(errors) == 0
    
    def test_metadata_not_dict(self):
        """Metadata que no es dict debe fallar"""
        valid, errors = validate_metadata_format("not a dict")
        assert valid is False
        assert len(errors) > 0
    
    def test_missing_source(self):
        """Metadata sin 'source' debe fallar"""
        metadata = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "context7_version": "7.0"
        }
        valid, errors = validate_metadata_format(metadata)
        assert valid is False
        assert any("source" in e.lower() for e in errors)
    
    def test_invalid_source(self):
        """Metadata con source != 'copilot_operator' debe fallar"""
        metadata = {
            "source": "invalid_source",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "context7_version": "7.0"
        }
        valid, errors = validate_metadata_format(metadata)
        assert valid is False
        assert any("source" in e.lower() for e in errors)
    
    def test_invalid_timestamp(self):
        """Metadata con timestamp inválido debe fallar"""
        metadata = {
            "source": "copilot_operator",
            "timestamp": "not-a-timestamp",
            "context7_version": "7.0"
        }
        valid, errors = validate_metadata_format(metadata)
        assert valid is False
        assert any("timestamp" in e.lower() for e in errors)
    
    def test_invalid_context7_version(self):
        """Metadata con version != '7.0' debe fallar"""
        metadata = {
            "source": "copilot_operator",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "context7_version": "6.0"
        }
        valid, errors = validate_metadata_format(metadata)
        assert valid is False
        assert any("version" in e.lower() for e in errors)


# ============================================================================
# TESTS: VALIDATOR 3 - Mode Flag
# ============================================================================

class TestModeFlag:
    """Tests para validate_mode_flag()"""
    
    def test_valid_operator_mode(self):
        """Mode 'vx11_operator' debe pasar"""
        payload = {"operator_mode": "vx11_operator"}
        valid, error = validate_mode_flag(payload)
        assert valid is True
    
    def test_disabled_mode(self):
        """Mode 'disabled' debe fallar"""
        payload = {"operator_mode": "disabled"}
        valid, error = validate_mode_flag(payload)
        assert valid is False
        assert "disabled" in error.lower()
    
    def test_missing_mode(self):
        """Payload sin mode debe fallar"""
        payload = {}
        valid, error = validate_mode_flag(payload)
        assert valid is False
        assert "missing" in error.lower()
    
    def test_invalid_mode_value(self):
        """Mode con valor inválido debe fallar"""
        payload = {"operator_mode": "invalid_mode"}
        valid, error = validate_mode_flag(payload)
        assert valid is False
    
    def test_mode_as_fallback(self):
        """Si 'operator_mode' falta, usa 'mode' como fallback"""
        payload = {"mode": "vx11_operator"}
        valid, error = validate_mode_flag(payload)
        assert valid is True


# ============================================================================
# TESTS: VALIDATOR 4 - Security Constraints
# ============================================================================

class TestSecurityConstraints:
    """Tests para validate_security_constraints()"""
    
    def test_clean_message(self):
        """Mensaje limpio debe pasar"""
        message = "Please check VX11 status and report health"
        valid, errors = validate_security_constraints(message)
        assert valid is True
        assert len(errors) == 0
    
    def test_shell_execution_patterns(self):
        """Mensaje con shell execution patterns debe fallar"""
        dangerous_messages = [
            "os.system('rm -rf /')",
            "subprocess.Popen('bash -c echo')",
            "/bin/bash -c malicious_command",
            "eval('some_code')",
        ]
        for msg in dangerous_messages:
            valid, errors = validate_security_constraints(msg)
            assert valid is False, f"Should reject: {msg}"
            assert len(errors) > 0
    
    def test_dangerous_paths(self):
        """Mensaje con rutas peligrosas debe fallar"""
        dangerous_messages = [
            "modify /etc/passwd",
            "delete /root/.ssh",
            "write to /sys/kernel",
        ]
        for msg in dangerous_messages:
            valid, errors = validate_security_constraints(msg)
            assert valid is False, f"Should reject: {msg}"
    
    def test_blocked_actions(self):
        """Mensaje con acciones bloqueadas debe fallar"""
        dangerous_messages = [
            "spawn_daughters now",
            "execute docker pull",
            "run as sudo",
        ]
        for msg in dangerous_messages:
            valid, errors = validate_security_constraints(msg)
            assert valid is False, f"Should reject: {msg}"
    
    def test_sql_keywords(self):
        """Mensaje con SQL peligroso debe fallar"""
        dangerous_sql = [
            "SELECT * FROM users; DROP TABLE users;",
            "DELETE FROM important_data WHERE true",
            "TRUNCATE TABLE critical_info",
        ]
        for sql in dangerous_sql:
            valid, errors = validate_security_constraints(sql)
            assert valid is False, f"Should reject: {sql}"


# ============================================================================
# TESTS: VALIDATOR 5 - Sanitize Payload
# ============================================================================

class TestSanitizePayload:
    """Tests para sanitize_payload()"""
    
    def test_sanitize_removes_extra_keys(self):
        """Sanitize remueve keys no autorizadas"""
        payload = {
            "source": "copilot_operator",
            "message": "test",
            "metadata": {},
            "extra_key": "should be removed",
            "another_extra": "also removed"
        }
        sanitized = sanitize_payload(payload)
        assert "extra_key" not in sanitized
        assert "another_extra" not in sanitized
    
    def test_sanitize_masks_paths(self):
        """Sanitize enmascara rutas absolutas"""
        payload = {
            "source": "copilot_operator",
            "message": "check /etc/config and /root/.ssh",
            "metadata": {}
        }
        sanitized = sanitize_payload(payload)
        assert "/etc/config" not in sanitized["message"]
        assert "/root/.ssh" not in sanitized["message"]
        assert "***masked_path***" in sanitized["message"]
    
    def test_sanitize_removes_sensitive_metadata(self):
        """Sanitize remueve tokens/secrets del metadata"""
        payload = {
            "source": "copilot_operator",
            "message": "test",
            "metadata": {
                "source": "copilot_operator",
                "token": "secret-token-value",
                "password": "secret-password"
            }
        }
        sanitized = sanitize_payload(payload)
        assert "token" not in sanitized["metadata"]
        assert "password" not in sanitized["metadata"]
    
    def test_sanitize_normalizes_mode_field(self):
        """Sanitize normaliza 'mode' a 'operator_mode'"""
        payload = {
            "source": "copilot_operator",
            "message": "test",
            "mode": "vx11_operator"
        }
        sanitized = sanitize_payload(payload)
        assert "operator_mode" in sanitized
        assert "mode" not in sanitized or sanitized["operator_mode"] == "vx11_operator"


# ============================================================================
# TESTS: Orchestrator - Complete Validation
# ============================================================================

class TestCopilotOperatorBridgeValidator:
    """Tests para CopilotOperatorBridgeValidator - orquestador"""
    
    @pytest.mark.asyncio
    async def test_valid_complete_request(self):
        """Request válido completo debe pasar todas validaciones"""
        validator = CopilotOperatorBridgeValidator()
        
        payload = build_test_payload()
        
        is_valid, response, errors = await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        assert is_valid is True
        assert len(errors) == 0
        assert response["valid"] is True
    
    @pytest.mark.asyncio
    async def test_invalid_message_length(self):
        """Request con mensaje muy largo debe fallar"""
        validator = CopilotOperatorBridgeValidator()
        
        payload = build_test_payload()
        payload["message"] = "X" * (16384 + 1)
        
        is_valid, response, errors = await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert response["valid"] is False
    
    @pytest.mark.asyncio
    async def test_invalid_mode_disabled(self):
        """Request con mode 'disabled' debe fallar"""
        validator = CopilotOperatorBridgeValidator()
        
        payload = build_test_payload(mode="disabled")
        
        is_valid, response, errors = await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        assert is_valid is False
        assert any("disabled" in e.lower() for e in errors)
    
    @pytest.mark.asyncio
    async def test_invalid_security_constraint(self):
        """Request con shell execution debe fallar"""
        validator = CopilotOperatorBridgeValidator()
        
        payload = build_test_payload(message="os.system('malicious')")
        
        is_valid, response, errors = await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        assert is_valid is False
        assert len(errors) > 0
    
    @pytest.mark.asyncio
    async def test_fail_fast_strategy(self):
        """Si un validador falla, no se continúa (fail-fast)"""
        validator = CopilotOperatorBridgeValidator()
        
        payload = build_test_payload()
        payload["message"] = "X" * (16384 + 1)  # Mensaje muy largo
        payload["operator_mode"] = "disabled"     # Mode deshabilitado
        
        is_valid, response, errors = await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        assert is_valid is False
        assert len(errors) > 0  # Múltiples errores detectados
    
    @pytest.mark.asyncio
    async def test_validation_log_tracking(self):
        """Validador debe trackear log de validaciones"""
        validator = CopilotOperatorBridgeValidator()
        
        payload = build_test_payload()
        
        await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        log = validator.get_validation_log()
        assert len(log) > 0
        assert any("PASSED" in entry or "FAILED" in entry for entry in log)
    
    @pytest.mark.asyncio
    async def test_clear_log(self):
        """Clear log debe limpiar el tracking"""
        validator = CopilotOperatorBridgeValidator()
        
        payload = build_test_payload()
        await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        validator.clear_log()
        assert len(validator.get_validation_log()) == 0


# ============================================================================
# TESTS: Helper Functions
# ============================================================================

class TestHelperFunctions:
    """Tests para funciones helper"""
    
    def test_get_validator_stats(self):
        """get_validator_stats() debe retornar estadísticas correctas"""
        stats = get_validator_stats()
        
        assert "validators_count" in stats
        assert stats["validators_count"] == 5
        assert "validators" in stats
        assert len(stats["validators"]) == 5
        assert stats["strategy"] == "FAIL-FAST"
    
    def test_build_test_payload(self):
        """build_test_payload() debe construir payload válido"""
        payload = build_test_payload()
        
        assert "source" in payload
        assert payload["source"] == "copilot_operator"
        assert "message" in payload
        assert "metadata" in payload
        assert "context7" in payload


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Tests de integración - escenarios realistas"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_valid_request(self):
        """Flujo completo: request válido de Copilot → validación → sanitización"""
        validator = CopilotOperatorBridgeValidator()
        
        # Step 1: Build request
        payload = build_test_payload(message="Get status of VX11 modules")
        
        # Step 2: Validate
        is_valid, response, errors = await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        # Step 3: Verify result
        assert is_valid is True
        assert response["valid"] is True
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_security_rejection(self):
        """Flujo completo: request malicioso es rechazado en validación"""
        validator = CopilotOperatorBridgeValidator()
        
        payload = build_test_payload(message="Execute: sudo rm -rf /")
        
        is_valid, response, errors = await validator.validate_complete_request(
            message=payload["message"],
            metadata=payload["metadata"],
            payload=payload
        )
        
        assert is_valid is False
        assert len(errors) > 0


# ============================================================================
# PERFORMANCE & EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests para edge cases y límites"""
    
    def test_unicode_message(self):
        """Mensaje con unicode debe ser handled correctamente"""
        message = "Hola VX11: 你好 🚀 مرحبا"
        valid, error = validate_message_length(message)
        assert valid is True
    
    def test_very_long_blocked_actions_list(self):
        """Validador debe handle listas grandes de acciones bloqueadas"""
        big_blocked_list = [f"action_{i}" for i in range(1000)]
        message = "Check system health"
        valid, errors = validate_security_constraints(message, big_blocked_list)
        assert valid is True
    
    @pytest.mark.asyncio
    async def test_concurrent_validation_requests(self):
        """Validador debe poder manejar requests concurrentes"""
        validator = CopilotOperatorBridgeValidator()
        
        async def validate_one():
            payload = build_test_payload()
            is_valid, response, errors = await validator.validate_complete_request(
                message=payload["message"],
                metadata=payload["metadata"],
                payload=payload
            )
            return is_valid
        
        # Execute 10 validations concurrently
        results = await asyncio.gather(*[validate_one() for _ in range(10)])
        assert all(results)


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
def valid_payload():
    """Fixture: payload válido para reutilizar"""
    return build_test_payload()


@pytest.fixture
def invalid_payloads():
    """Fixture: lista de payloads inválidos"""
    return [
        build_test_payload(message="X" * 20000),  # Too long
        build_test_payload(mode="disabled"),       # Disabled mode
        build_test_payload(message="sudo rm -rf /"),  # Dangerous
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
