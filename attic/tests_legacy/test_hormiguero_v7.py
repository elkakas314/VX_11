"""
test_hormiguero_v7.py - Tests para Hormiguero Queen + Ants v7.0
"""

import pytest
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.db_schema import Base, HormigaState, Incident, PheromoneLog
from hormiguero.hormiguero_v7 import (
    Ant, Queen, AntColony, AntRole, SeverityLevel, IncidentType, PheromoneType
)


@pytest.fixture(scope="function")
def test_db():
    """In-memory SQLite for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


# ============ ANT TESTS ============

class TestAnt:
    """Suite: Ant (Hormiga) functionality"""
    
    @pytest.mark.asyncio
    async def test_ant_creation(self):
        """Test: Ant created with correct role."""
        ant = Ant("ant_1", AntRole.SCANNER_DRIFT)
        assert ant.ant_id == "ant_1"
        assert ant.role == AntRole.SCANNER_DRIFT
        assert ant.mutation_level == 0
    
    @pytest.mark.asyncio
    async def test_ant_scan_drift(self):
        """Test: Ant can scan for drift (compile errors)."""
        ant = Ant("ant_drift", AntRole.SCANNER_DRIFT)
        incidents = await ant.scan()
        # Should return list (empty if no issues, or list of drift incidents)
        assert isinstance(incidents, list)
    
    @pytest.mark.asyncio
    async def test_ant_scan_memory(self):
        """Test: Ant can scan for memory issues."""
        ant = Ant("ant_memory", AntRole.SCANNER_MEMORY)
        incidents = await ant.scan()
        assert isinstance(incidents, list)
        # If system RAM is low, may have incidents
        if incidents:
            assert any(inc.get("type") == IncidentType.MEMORY_LEAK for inc in incidents)
    
    @pytest.mark.asyncio
    async def test_ant_never_emits_pheromones(self):
        """Test: Ants NEVER emit pheromones, only report."""
        ant = Ant("ant_reporter", AntRole.SCANNER_IMPORTS)
        incidents = await ant.scan()
        # Ant should only report, not create pheromones
        # (we verify this by checking ant doesn't have pheromone_emit method)
        assert not hasattr(ant, "emit_pheromone")
        assert hasattr(ant, "report_to_queen")
    
    @pytest.mark.asyncio
    async def test_ant_update_state(self):
        """Test: Ant updates its state in DB."""
        # Mock get_session to use test_db
        from unittest.mock import patch
        from config.db_schema import get_session
        
        with patch("hormiguero.hormiguero_v7.get_session") as mock_get_session:
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            
            def get_session_override(module="vx11"):
                return SessionLocal()
            
            mock_get_session.side_effect = get_session_override
            
            ant = Ant("ant_state_test", AntRole.SCANNER_DRIFT)
            await ant.update_state()
            
            session = SessionLocal()
            state = session.query(HormigaState).filter_by(ant_id="ant_state_test").first()
            assert state is not None
            assert state.role == AntRole.SCANNER_DRIFT.value
            assert state.status == "idle"
            session.close()


# ============ QUEEN TESTS ============

class TestQueen:
    """Suite: Queen (Reina) functionality"""
    
    def test_queen_creation(self):
        """Test: Queen created with all ant types."""
        queen = Queen()
        assert len(queen.ants) == 8  # 8 specialized ant types
        for ant_id, ant in queen.ants.items():
            assert isinstance(ant, Ant)
    
    @pytest.mark.asyncio
    async def test_queen_classify_incident_critical(self):
        """Test: Queen classifies CRITICAL incidents as spawn_hija."""
        queen = Queen()
        
        # Create mock incident
        from unittest.mock import MagicMock
        incident = MagicMock()
        incident.id = 1
        incident.incident_type = IncidentType.MEMORY_LEAK
        incident.severity = SeverityLevel.CRITICAL
        incident.location = "system"
        
        decision = await queen._classify_and_decide(incident)
        
        assert decision["route"] == "spawn_hija"
        assert "Critical" in decision["reason"]
    
    @pytest.mark.asyncio
    async def test_queen_classify_incident_error(self):
        """Test: Queen classifies ERROR incidents as switch_strategy."""
        queen = Queen()
        
        from unittest.mock import MagicMock
        incident = MagicMock()
        incident.id = 2
        incident.incident_type = IncidentType.BROKEN_IMPORT
        incident.severity = SeverityLevel.ERROR
        incident.location = "/app/test.py"
        
        decision = await queen._classify_and_decide(incident)
        
        assert decision["route"] == "switch_strategy"
    
    @pytest.mark.asyncio
    async def test_queen_classify_incident_info(self):
        """Test: Queen classifies INFO incidents as direct_action."""
        queen = Queen()
        
        from unittest.mock import MagicMock
        incident = MagicMock()
        incident.id = 3
        incident.incident_type = IncidentType.ORPHAN_LOG
        incident.severity = SeverityLevel.INFO
        incident.location = "/tmp/test.log"
        
        decision = await queen._classify_and_decide(incident)
        
        assert decision["route"] == "direct_action"


# ============ COLONY TESTS ============

class TestAntColony:
    """Suite: AntColony orchestration"""
    
    def test_colony_creation(self):
        """Test: Colony created with Queen and Ants."""
        colony = AntColony()
        assert colony.queen is not None
        assert len(colony.ants) == 8
    
    @pytest.mark.asyncio
    async def test_colony_scan_cycle(self):
        """Test: Colony scan cycle aggregates incidents."""
        from unittest.mock import patch
        
        with patch("hormiguero.hormiguero_v7.get_session"):
            colony = AntColony()
            result = await colony.scan_cycle()
            
            assert "total_incidents" in result
            assert "queen_decisions" in result
            assert isinstance(result["total_incidents"], int)
            assert isinstance(result["queen_decisions"], list)


# ============ DATABASE TESTS ============

class TestHormigueroDB:
    """Suite: Database model integration"""
    
    def test_hormiga_state_table(self, test_db):
        """Test: HormigaState table creation and insertion."""
        state = HormigaState(
            ant_id="ant_test_1",
            role="scanner_drift",
            status="idle",
            cpu_percent=15.5,
            ram_percent=42.0,
        )
        test_db.add(state)
        test_db.commit()
        
        retrieved = test_db.query(HormigaState).filter_by(ant_id="ant_test_1").first()
        assert retrieved is not None
        assert retrieved.role == "scanner_drift"
        assert retrieved.cpu_percent == 15.5
    
    def test_incident_table(self, test_db):
        """Test: Incident table creation and insertion."""
        incident = Incident(
            ant_id="ant_memory",
            incident_type=IncidentType.MEMORY_LEAK.value,
            severity=SeverityLevel.WARNING.value,
            location="system",
            details=json.dumps({"ram_usage": 85.5}),
            status="open",
        )
        test_db.add(incident)
        test_db.commit()
        
        retrieved = test_db.query(Incident).filter_by(ant_id="ant_memory").first()
        assert retrieved is not None
        assert retrieved.incident_type == "memory_leak"
        assert retrieved.status == "open"
    
    def test_pheromone_log_table(self, test_db):
        """Test: PheromoneLog table creation and insertion."""
        pheromone = PheromoneLog(
            pheromone_type=PheromoneType.ALERT.value,
            intensity=5,
            source_incident_ids=json.dumps([1, 2, 3]),
            madre_intent_id="intent_123",
            payload=json.dumps({"action": "cleanup"}),
        )
        test_db.add(pheromone)
        test_db.commit()
        
        retrieved = test_db.query(PheromoneLog).first()
        assert retrieved is not None
        assert retrieved.pheromone_type == "alert"
        assert retrieved.intensity == 5


# ============ INTEGRATION TESTS ============

class TestHormigueroIntegration:
    """Suite: End-to-end Hormiguero flows"""
    
    @pytest.mark.asyncio
    async def test_incident_detection_and_queen_decision_flow(self):
        """Test: Incident detected → Queen decides → Feromona emitted."""
        from unittest.mock import patch, MagicMock
        
        with patch("hormiguero.hormiguero_v7.get_session") as mock_get_session:
            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)
            SessionLocal = sessionmaker(bind=engine)
            
            def get_session_override(module="vx11"):
                return SessionLocal()
            
            mock_get_session.side_effect = get_session_override
            
            # Create colony
            colony = AntColony()
            
            # Manually add an incident
            session = SessionLocal()
            incident = Incident(
                ant_id="ant_drift",
                incident_type=IncidentType.DRIFT.value,
                severity=SeverityLevel.ERROR.value,
                location="/app/test.py",
                details="Syntax error",
                status="open",
            )
            session.add(incident)
            session.commit()
            
            # Queen processes
            decision = await colony.queen._classify_and_decide(incident)
            assert decision["route"] in ["spawn_hija", "switch_strategy", "direct_action"]
            
            session.close()


# ============ ENUM TESTS ============

class TestEnums:
    """Suite: Enum definitions"""
    
    def test_ant_role_values(self):
        """Test: All AntRole values are defined."""
        roles = [role.value for role in AntRole]
        assert "scanner_drift" in roles
        assert "scanner_memory" in roles
        assert "scanner_imports" in roles
        assert "scanner_logs" in roles
        assert "scanner_db" in roles
        assert "scanner_modules" in roles
        assert "scanner_processes" in roles
        assert "scanner_ports" in roles
    
    def test_severity_levels(self):
        """Test: All severity levels defined."""
        levels = [level.value for level in SeverityLevel]
        assert "info" in levels
        assert "warning" in levels
        assert "error" in levels
        assert "critical" in levels
    
    def test_incident_types(self):
        """Test: All incident types defined."""
        types = [t.value for t in IncidentType]
        assert "drift" in types
        assert "memory_leak" in types
        assert "broken_import" in types
        assert "orphan_log" in types
        assert "orphan_db" in types
        assert "orphan_module" in types
        assert "zombie_process" in types
        assert "blocked_port" in types


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
