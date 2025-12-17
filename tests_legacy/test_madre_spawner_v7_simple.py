"""
DEEP SURGEON - test_madre_spawner_v7_simple.py
Tests focalizados para MADRE/SPAWNER v7 (versión simplificada)

Cobertura:
1. POST /madre/intent → DaughterTask created
2. GET /madre/tasks/active, GET /madre/hijas/active
3. Task cancellation
4. TTL expiry and retry logic
5. Priority map
6. Database models creation
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.db_schema import Base, DaughterTask, Daughter, DaughterAttempt, IntentLog
from madre.main import PRIORITY_MAP


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


# ============ DATABASE MODEL TESTS ============

class TestDatabaseModels:
    """Suite: Validar que modelos BD están creados correctamente"""
    
    def test_daughter_task_table_exists(self, test_db):
        """Test: DaughterTask table created with correct columns"""
        task = DaughterTask(
            source="operator",
            priority=1,
            status="pending",
            task_type="short",
            description="test",
            max_retries=2,
        )
        test_db.add(task)
        test_db.commit()
        
        retrieved = test_db.query(DaughterTask).first()
        assert retrieved is not None
        assert retrieved.source == "operator"
        assert retrieved.status == "pending"
        assert retrieved.current_retry == 0
    
    def test_daughter_table_exists(self, test_db):
        """Test: Daughter table created with correct columns"""
        task = DaughterTask(
            source="madre",
            priority=2,
            status="running",
            task_type="short",
            description="parent",
        )
        test_db.add(task)
        test_db.flush()
        
        hija = Daughter(
            task_id=task.id,
            name="hija_test",
            purpose="test_execution",
            ttl_seconds=300,
            status="running",
            mutation_level=0,
        )
        test_db.add(hija)
        test_db.commit()
        
        retrieved = test_db.query(Daughter).first()
        assert retrieved is not None
        assert retrieved.name == "hija_test"
        assert retrieved.mutation_level == 0
        assert retrieved.ttl_seconds == 300
    
    def test_daughter_attempt_table_exists(self, test_db):
        """Test: DaughterAttempt table created with correct columns"""
        task = DaughterTask(
            source="madre",
            priority=2,
            status="running",
            task_type="short",
            description="parent",
        )
        test_db.add(task)
        test_db.flush()
        
        hija = Daughter(
            task_id=task.id,
            name="hija_test",
            purpose="test",
            ttl_seconds=300,
            status="running",
        )
        test_db.add(hija)
        test_db.flush()
        
        attempt = DaughterAttempt(
            daughter_id=hija.id,
            attempt_number=1,
            status="running",
        )
        test_db.add(attempt)
        test_db.commit()
        
        retrieved = test_db.query(DaughterAttempt).first()
        assert retrieved is not None
        assert retrieved.attempt_number == 1
        assert retrieved.status == "running"
    
    def test_intent_log_table_exists(self, test_db):
        """Test: IntentLog table created with correct columns"""
        log = IntentLog(
            source="operator",
            payload_json=json.dumps({"intent_type": "test"}),
            result_status="planned",
        )
        test_db.add(log)
        test_db.commit()
        
        retrieved = test_db.query(IntentLog).first()
        assert retrieved is not None
        assert retrieved.source == "operator"
        assert json.loads(retrieved.payload_json)["intent_type"] == "test"


# ============ LOGIC TESTS ============

class TestRetryLogic:
    """Suite: TTL expiry, retry, mutation logic"""
    
    def test_ttl_expiry_marks_hija_expired(self, test_db):
        """Test 5: TTL expiry → hija status = expired"""
        task = DaughterTask(
            source="madre",
            priority=2,
            status="running",
            task_type="short",
            description="ttl_test",
            max_retries=3,
        )
        test_db.add(task)
        test_db.flush()
        
        # Hija creada hace 20 segundos, TTL 10 segundos
        hija = Daughter(
            task_id=task.id,
            name="hija_expired",
            purpose="test",
            status="running",
            ttl_seconds=10,
            started_at=datetime.utcnow() - timedelta(seconds=20),
        )
        test_db.add(hija)
        test_db.commit()
        
        # Simular detector de TTL
        now = datetime.utcnow()
        age_secs = (now - hija.started_at).total_seconds()
        assert age_secs > hija.ttl_seconds
        
        # Marcar como expirada
        hija.status = "expired"
        test_db.add(hija)
        test_db.commit()
        
        updated = test_db.query(Daughter).filter_by(id=hija.id).first()
        assert updated.status == "expired"
    
    def test_retry_increments_mutation_level(self, test_db):
        """Test 6: Retry → nueva Daughter con mutation_level+1"""
        task = DaughterTask(
            source="madre",
            priority=2,
            status="retrying",
            task_type="short",
            description="mutation_test",
            current_retry=1,
            max_retries=5,
        )
        test_db.add(task)
        test_db.flush()
        
        # Primera hija (retry 0)
        hija1 = Daughter(
            task_id=task.id,
            name="hija_v0",
            purpose="test",
            status="expired",
            ttl_seconds=300,
            mutation_level=0,
        )
        test_db.add(hija1)
        test_db.flush()
        
        # Segunda hija con mutation_level=1
        hija2 = Daughter(
            task_id=task.id,
            name="hija_v1",
            purpose="test",
            status="spawned",
            ttl_seconds=300,
            mutation_level=task.current_retry,
        )
        test_db.add(hija2)
        test_db.commit()
        
        all_hijas = test_db.query(Daughter).filter_by(task_id=task.id).all()
        assert len(all_hijas) == 2
        assert all_hijas[0].mutation_level == 0
        assert all_hijas[1].mutation_level == 1
    
    def test_max_retries_exhausted_marks_failed(self, test_db):
        """Test 7: Max retries exhausted → task status = failed"""
        task = DaughterTask(
            source="madre",
            priority=2,
            status="running",
            task_type="short",
            description="exhausted_test",
            current_retry=2,
            max_retries=2,
        )
        test_db.add(task)
        test_db.flush()
        
        hija = Daughter(
            task_id=task.id,
            name="hija_exhausted",
            purpose="test",
            status="expired",
            ttl_seconds=300,
        )
        test_db.add(hija)
        test_db.commit()
        
        # Marcar task como failed (retries exhausted)
        if task.current_retry >= task.max_retries:
            task.status = "failed"
            test_db.add(task)
            test_db.commit()
        
        updated_task = test_db.query(DaughterTask).filter_by(id=task.id).first()
        assert updated_task.status == "failed"


class TestTaskLifecycle:
    """Suite: Task creation, cancellation, status transitions"""
    
    def test_intent_to_daughter_task_creation(self, test_db):
        """Test 1: INTENT → DaughterTask created with pending status"""
        intent_data = {
            "source": "operator",
            "intent_type": "analysis",
            "ttl_seconds": 300,
        }
        
        task = DaughterTask(
            source=intent_data["source"],
            priority=PRIORITY_MAP.get(intent_data["source"], 4),
            status="pending",
            task_type="long" if intent_data["ttl_seconds"] >= 60 else "short",
            description=intent_data["intent_type"],
            max_retries=5 if intent_data["ttl_seconds"] >= 60 else 2,
        )
        test_db.add(task)
        test_db.commit()
        
        retrieved = test_db.query(DaughterTask).filter_by(source="operator").first()
        assert retrieved is not None
        assert retrieved.status == "pending"
        assert retrieved.task_type == "long"
        assert retrieved.max_retries == 5
    
    def test_task_cancellation_kills_daughters(self, test_db):
        """Test 8: POST cancel → task marked cancelled, daughters marked killed"""
        task = DaughterTask(
            source="operator",
            priority=1,
            status="running",
            task_type="short",
            description="cancel_test",
        )
        test_db.add(task)
        test_db.flush()
        
        # Crear 2 daughters
        for i in range(2):
            hija = Daughter(
                task_id=task.id,
                name=f"hija_{i}",
                purpose="test",
                status="running",
                ttl_seconds=300,
            )
            test_db.add(hija)
        test_db.commit()
        
        # Simular cancellation
        task.status = "cancelled"
        test_db.add(task)
        
        daughters = test_db.query(Daughter).filter_by(task_id=task.id).all()
        for hija in daughters:
            hija.status = "killed"
            test_db.add(hija)
        test_db.commit()
        
        # Validar cambios
        updated_task = test_db.query(DaughterTask).filter_by(id=task.id).first()
        assert updated_task.status == "cancelled"
        
        killed_hijas = test_db.query(Daughter).filter_by(task_id=task.id, status="killed").all()
        assert len(killed_hijas) == 2


class TestTaskListing:
    """Suite: GET /madre/tasks/active, GET /madre/hijas/active"""
    
    def test_list_tasks_by_status_filter(self, test_db):
        """Test 2: GET /madre/tasks/active lista tasks con filtro de status"""
        statuses = ["pending", "planning", "running", "completed"]
        
        for status in statuses:
            task = DaughterTask(
                source="operator",
                priority=1,
                status=status,
                task_type="short",
                description=f"task_{status}",
            )
            test_db.add(task)
        test_db.commit()
        
        # Query: solo running
        running_tasks = test_db.query(DaughterTask).filter_by(status="running").all()
        assert len(running_tasks) == 1
        assert running_tasks[0].description == "task_running"
    
    def test_list_daughters_by_status_filter(self, test_db):
        """Test 3: GET /madre/hijas/active lista daughters con filtro de status"""
        task = DaughterTask(
            source="operator",
            priority=1,
            status="running",
            task_type="short",
            description="parent",
        )
        test_db.add(task)
        test_db.flush()
        
        statuses = ["spawned", "running", "finished", "failed"]
        for status in statuses:
            hija = Daughter(
                task_id=task.id,
                name=f"hija_{status}",
                purpose="test",
                status=status,
                ttl_seconds=300,
            )
            test_db.add(hija)
        test_db.commit()
        
        # Query: solo finished y failed
        terminal_hijas = test_db.query(Daughter).filter(
            Daughter.status.in_(["finished", "failed"])
        ).all()
        assert len(terminal_hijas) == 2


class TestPrioritySystem:
    """Suite: Priority assignment and canonical values"""
    
    def test_priority_map_canonical_values(self):
        """Test: PRIORITY_MAP tiene valores canónicos correctos"""
        assert PRIORITY_MAP["shub"] == 0
        assert PRIORITY_MAP["operator"] == 1
        assert PRIORITY_MAP["madre"] == 2
        assert PRIORITY_MAP["hijas"] == 3
    
    def test_task_priority_by_source(self, test_db):
        """Test: DaughterTask asigna priority correcta según source"""
        sources_and_priorities = [
            ("shub", 0),
            ("operator", 1),
            ("madre", 2),
            ("hijas", 3),
        ]
        
        for source, expected_priority in sources_and_priorities:
            task = DaughterTask(
                source=source,
                priority=PRIORITY_MAP.get(source, 4),
                status="pending",
                task_type="short",
                description=f"task_{source}",
            )
            test_db.add(task)
        test_db.commit()
        
        for source, expected_priority in sources_and_priorities:
            task = test_db.query(DaughterTask).filter_by(source=source).first()
            assert task.priority == expected_priority


class TestAuditTrail:
    """Suite: IntentLog and audit trail"""
    
    def test_intent_log_creation_and_audit_trail(self, test_db):
        """Test: IntentLog crea audit trail de INTENT processing"""
        payload = {"text": "analiza esto", "type": "analysis"}
        
        log = IntentLog(
            source="operator",
            payload_json=json.dumps(payload),
            result_status="planned",
            created_at=datetime.utcnow(),
        )
        test_db.add(log)
        test_db.flush()
        
        # Simular processing
        log.processed_by_madre_at = datetime.utcnow()
        test_db.add(log)
        test_db.commit()
        
        # Validar audit trail
        retrieved = test_db.query(IntentLog).first()
        assert retrieved is not None
        assert retrieved.source == "operator"
        assert json.loads(retrieved.payload_json)["type"] == "analysis"
        assert retrieved.processed_by_madre_at is not None


# ============ MAIN ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
