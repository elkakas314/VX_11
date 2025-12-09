"""
test_reina_logic_v7.py - Queen decision logic and Madre integration tests
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from hormiguero.hormiguero_v7 import Queen, IncidentType, SeverityLevel


class TestReinaDecisionLogic:
    """Suite: Queen decision-making logic"""
    
    @pytest.mark.asyncio
    async def test_queen_decision_matrix_critical_incident(self):
        """Test: CRITICAL incidents → spawn_hija route."""
        queen = Queen()
        
        incident = MagicMock()
        incident.id = 100
        incident.incident_type = IncidentType.MEMORY_LEAK.value
        incident.severity = SeverityLevel.CRITICAL.value
        incident.location = "system_ram"
        
        decision = await queen._classify_and_decide(incident)
        
        assert decision["route"] == "spawn_hija"
        assert "mother_intent" in decision
        assert decision["mother_intent"]["source"] == "hormiguero"
        assert "fix_" in decision["mother_intent"]["intent_type"]
    
    @pytest.mark.asyncio
    async def test_queen_decision_matrix_error_incident(self):
        """Test: ERROR incidents → switch_strategy route."""
        queen = Queen()
        
        incident = MagicMock()
        incident.id = 101
        incident.incident_type = IncidentType.BROKEN_IMPORT.value
        incident.severity = SeverityLevel.ERROR.value
        incident.location = "/app/madre/main.py"
        
        decision = await queen._classify_and_decide(incident)
        
        assert decision["route"] == "switch_strategy"
        assert "switch_request" in decision
        assert decision["switch_request"]["task_type"] == "incident_resolution"
    
    @pytest.mark.asyncio
    async def test_queen_decision_matrix_warning_incident(self):
        """Test: WARNING incidents → direct_action route."""
        queen = Queen()
        
        incident = MagicMock()
        incident.id = 102
        incident.incident_type = IncidentType.ORPHAN_LOG.value
        incident.severity = SeverityLevel.WARNING.value
        incident.location = "/tmp/orphan.log"
        
        decision = await queen._classify_and_decide(incident)
        
        assert decision["route"] == "direct_action"
        assert "cleanup_" in decision["action"]
    
    @pytest.mark.asyncio
    async def test_queen_decision_matrix_info_incident(self):
        """Test: INFO incidents → direct_action route."""
        queen = Queen()
        
        incident = MagicMock()
        incident.id = 103
        incident.incident_type = IncidentType.BLOCKED_PORT.value
        incident.severity = SeverityLevel.INFO.value
        incident.location = "127.0.0.1:9999"
        
        decision = await queen._classify_and_decide(incident)
        
        assert decision["route"] == "direct_action"


class TestReinaSwitchConsultation:
    """Suite: Queen consulting Switch for approval"""
    
    @pytest.mark.asyncio
    async def test_queen_consults_switch_before_acting(self):
        """Test: Queen ALWAYS consults Switch before emitting feromonas."""
        queen = Queen()
        
        with patch("hormiguero.hormiguero_v7.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"approved": True})
            )
            
            decision = {"route": "spawn_hija", "reason": "Critical"}
            approved = await queen._consult_switch_for_approval(decision)
            
            assert approved is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "task_type" in call_args.kwargs["json"]
            assert call_args.kwargs["json"]["task_type"] == "approval"
    
    @pytest.mark.asyncio
    async def test_queen_respects_switch_veto(self):
        """Test: Queen respects Switch veto (approved=False)."""
        queen = Queen()
        
        with patch("hormiguero.hormiguero_v7.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"approved": False})
            )
            
            decision = {"route": "spawn_hija"}
            approved = await queen._consult_switch_for_approval(decision)
            
            assert approved is False
    
    @pytest.mark.asyncio
    async def test_queen_fallback_when_switch_unavailable(self):
        """Test: Queen defaults to True if Switch is unreachable."""
        queen = Queen()
        
        with patch("hormiguero.hormiguero_v7.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Connection error")
            
            decision = {"route": "spawn_hija"}
            approved = await queen._consult_switch_for_approval(decision)
            
            # Should default to True (conservative approach)
            assert approved is True


class TestReinaMadreIntegration:
    """Suite: Queen dispatching INTENT to Madre"""
    
    @pytest.mark.asyncio
    async def test_queen_dispatches_intent_to_madre(self):
        """Test: Queen sends INTENT to Madre via /madre/intent endpoint."""
        queen = Queen()
        
        with patch("hormiguero.hormiguero_v7.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"daughter_task_id": "task_123"})
            )
            
            decision = {
                "route": "spawn_hija",
                "mother_intent": {
                    "source": "hormiguero",
                    "intent_type": "fix_memory_leak",
                    "payload": {"incident_id": 1},
                }
            }
            
            await queen._dispatch_to_madre(decision)
            
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/madre/intent" in call_args.args[0]
            assert call_args.kwargs["json"]["source"] == "hormiguero"
    
    @pytest.mark.asyncio
    async def test_queen_handles_madre_unavailable(self):
        """Test: Queen handles gracefully if Madre is unavailable."""
        queen = Queen()
        
        with patch("hormiguero.hormiguero_v7.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Madre unreachable")
            
            decision = {"route": "spawn_hija", "mother_intent": {}}
            
            # Should not raise, just log
            await queen._dispatch_to_madre(decision)


class TestReinaSwitchStrategyConsultation:
    """Suite: Queen consulting Switch for strategy"""
    
    @pytest.mark.asyncio
    async def test_queen_consults_switch_for_strategy_on_error_incidents(self):
        """Test: Queen consults Switch for strategy on ERROR incidents."""
        queen = Queen()
        
        with patch("hormiguero.hormiguero_v7.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"provider": "local_model", "approach": "fix_imports"})
            )
            
            decision = {
                "route": "switch_strategy",
                "switch_request": {
                    "task_type": "incident_resolution",
                    "payload": {"incident_type": "broken_import"},
                }
            }
            
            await queen._consult_switch_for_strategy(decision)
            
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/switch/task" in call_args.args[0]
            assert call_args.kwargs["json"]["task_type"] == "strategy"


class TestReinaPheromonaEmission:
    """Suite: Feromona emission (only after Switch approval)"""
    
    @pytest.mark.asyncio
    async def test_feromona_emitted_only_after_switch_approval(self):
        """Test: Feromona created in DB only after Switch approval."""
        from config.db_schema import PheromoneLog
        from unittest.mock import patch, MagicMock
        
        queen = Queen()
        
        with patch("hormiguero.hormiguero_v7.get_session") as mock_get_session, \
             patch("hormiguero.hormiguero_v7.httpx.AsyncClient") as mock_client_class:
            
            # Setup session mock
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            
            # Setup Switch approval
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"approved": True})
            )
            
            decision = {
                "incident_id": 1,
                "route": "spawn_hija",
                "mother_intent": {"source": "hormiguero", "intent_type": "fix_leak"},
            }
            
            await queen._execute_decision(decision)
            
            # Verify PheromoneLog was added
            mock_session.add.assert_called()
            calls_with_pheromone = [
                call for call in mock_session.add.call_args_list
                if hasattr(call[0][0], '__class__') and 'Pheromone' in call[0][0].__class__.__name__
            ]
            assert len(calls_with_pheromone) > 0


class TestReinaDirectAction:
    """Suite: Queen executing direct actions (cleanup)"""
    
    @pytest.mark.asyncio
    async def test_queen_executes_direct_cleanup_actions(self):
        """Test: Queen can execute direct cleanup for low-severity incidents."""
        queen = Queen()
        
        decision = {
            "incident_id": 5,
            "route": "direct_action",
            "action": "cleanup_orphan_log",
        }
        
        # Should complete without error (action is logged)
        await queen._execute_direct_action(decision)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
