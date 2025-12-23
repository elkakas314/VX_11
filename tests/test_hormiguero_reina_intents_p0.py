"""
P0 tests for Reina -> Madre INTENT escalation payload.
"""

import os
import sys
from unittest.mock import patch

import pytest

SERVICE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "hormiguero")
)
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from hormiguero.core.queen import Queen
from hormiguero.config import settings
from hormiguero.core.db.sqlite import ensure_schema


def test_reina_escalation_payload_and_send(tmp_path, monkeypatch):
    db_path = tmp_path / "vx11.db"
    monkeypatch.setattr(settings, "db_path", str(db_path))
    ensure_schema()

    queen = Queen(root_path=str(tmp_path))
    incident_id = "incident-123"
    payload = {"missing": ["a.txt"], "extra": []}

    with patch("hormiguero.core.queen.requests.post") as mock_post:
        queen._notify_madre_intent(incident_id, payload)

        assert mock_post.called
        call_args = mock_post.call_args
        json_data = call_args.kwargs.get("json") or call_args[1].get("json")

        assert json_data["correlation_id"] == incident_id
        intent_payload = json_data["payload"]

        required_fields = [
            "domain",
            "intent_type",
            "summary",
            "details",
            "correlation_id",
            "urgency",
            "maintenance_ok",
            "requester",
        ]
        for key in required_fields:
            assert key in intent_payload
        assert intent_payload["requester"] == "reina"
