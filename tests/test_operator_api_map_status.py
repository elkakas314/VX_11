"""
Test suite for operator backend API response schemas.
"""


def test_api_status_schema():
    status_response = {
        "status": "ok",
        "policy": "solo_madre",
        "core_services": {"tentaculo_link": {"status": "UP"}, "madre": {"status": "UP"}},
        "degraded": False,
        "window": {"mode": "solo_madre", "services": ["madre", "redis"]},
        "timestamp": "2025-12-27T02:30:00.000000",
    }

    assert "status" in status_response
    assert "policy" in status_response
    assert "core_services" in status_response
    assert "window" in status_response
    assert "timestamp" in status_response
    assert isinstance(status_response["core_services"], dict)


def test_modules_schema():
    modules_response = {
        "modules": {
            "madre": {"status": "UP", "category": "core"},
            "switch": {"status": "OFF_BY_POLICY", "category": "optional"},
        }
    }

    assert "modules" in modules_response
    assert isinstance(modules_response["modules"], dict)


def test_operator_chat_response_includes_provider():
    chat_response = {
        "response": "Plan executed. Mode: MADRE. Status: DONE",
        "session_id": "test-001",
        "intent_id": "i-123",
        "plan_id": "p-123",
        "status": "DONE",
        "mode": "MADRE",
        "provider": "fallback_local",
        "model": "local",
        "warnings": [],
        "targets": [],
        "actions": [],
    }

    assert "provider" in chat_response
    assert "model" in chat_response
    assert chat_response["provider"] in [
        "deepseek",
        "fallback_local",
        "deepseek_error",
        "no_token",
    ]
    assert chat_response["model"] in ["deepseek-reasoner", "local"]
