"""
PASO 7: Integration Tests for VX11 v7.1 PASOS 2-6

Tests para validar:
1. PASO 2: Switch Intelligence Layer (/switch/chat + /switch/task)
2. PASO 3: DSL Compiler + Workflows
3. PASO 4: Daughters (Hijas reales)
4. PASO 5: Ant Colony (Hormiguero)
5. PASO 6: Manifestator Patches

Status: Production Validation
"""

import pytest
import asyncio
import json
from typing import Dict, Any


# ============ PASO 2: Switch Intelligence Layer Tests ============

class TestSwitchIntelligenceLayer:
    """Validar SwitchIntelligenceLayer integration en Switch"""
    
    def test_intelligence_layer_import(self):
        """Test: SIL can be imported"""
        from switch.intelligence_layer import (
            get_switch_intelligence_layer,
            RoutingContext,
            RoutingDecision,
        )
        
        sil = get_switch_intelligence_layer()
        assert sil is not None
        assert hasattr(sil, 'make_routing_decision')
    
    def test_routing_context_creation(self):
        """Test: RoutingContext dataclass works"""
        from switch.intelligence_layer import RoutingContext
        
        ctx = RoutingContext(
            task_type="audio_restore",
            source="madre",
            messages=[{"role": "user", "content": "restore audio"}],
            metadata={"file": "test.wav"},
        )
        
        assert ctx.task_type == "audio_restore"
        assert ctx.source == "madre"
        assert len(ctx.messages) == 1
    
    def test_ga_router_import(self):
        """Test: GA Router can be imported"""
        from switch.ga_router import get_ga_router
        
        ga_router = get_ga_router(None)
        assert ga_router is not None
        assert hasattr(ga_router, 'record_execution_result')
    
    def test_routing_decision_enum(self):
        """Test: RoutingDecision enum values"""
        from switch.intelligence_layer import RoutingDecision
        
        decisions = [
            RoutingDecision.LOCAL,
            RoutingDecision.CLI,
            RoutingDecision.HYBRID,
            RoutingDecision.SHUB,
            RoutingDecision.MADRE,
            RoutingDecision.MANIFESTATOR,
            RoutingDecision.FALLBACK,
        ]
        
        assert len(decisions) == 7
        assert all(d.value for d in decisions)


class TestSwitchChatEndpoint:
    """Test /switch/chat endpoint con SIL"""
    
    def test_switch_chat_imports(self):
        """Test: switch/main.py has SIL integration"""
        from switch.main import app
        
        assert app is not None
        # Verify endpoint exists
        routes = [route.path for route in app.routes]
        assert "/switch/chat" in routes


class TestSwitchTaskEndpoint:
    """Test /switch/task endpoint con SIL"""
    
    def test_switch_task_imports(self):
        """Test: switch/main.py has /switch/task endpoint"""
        from switch.main import app
        
        assert app is not None
        routes = [route.path for route in app.routes]
        assert "/switch/task" in routes


# ============ PASO 3: DSL Compiler Tests ============

class TestDSLCompiler:
    """Validar DSL Compiler"""
    
    def test_dsl_compiler_import(self):
        """Test: DSL Compiler can be imported"""
        from madre.dsl_compiler import VX11DSLCompiler, WorkflowPlan, WorkflowStep
        
        compiler = VX11DSLCompiler()
        assert compiler is not None
        assert hasattr(compiler, 'compile')
    
    def test_workflow_step_creation(self):
        """Test: WorkflowStep dataclass works"""
        from madre.dsl_compiler import WorkflowStep, ExecutorType
        
        step = WorkflowStep(
            executor=ExecutorType.HERMES,
            action="execute",
            parameters={"command": "ls -la"},
            timeout_ms=5000,
        )
        
        assert step.executor == ExecutorType.HERMES
        assert step.action == "execute"
        assert step.timeout_ms == 5000
    
    def test_workflow_plan_creation(self):
        """Test: WorkflowPlan dataclass works"""
        from madre.dsl_compiler import WorkflowPlan, WorkflowStep, ExecutorType
        
        step = WorkflowStep(
            executor=ExecutorType.HERMES,
            action="execute",
            parameters={},
        )
        
        plan = WorkflowPlan(
            workflow_id="wf_test",
            domain="HERMES",
            intent_action="execute",
            steps=[step],
        )
        
        assert plan.workflow_id == "wf_test"
        assert len(plan.steps) == 1
        assert plan.to_dict()["domain"] == "HERMES"
    
    def test_compile_task_intent(self):
        """Test: Compilar TASK intent"""
        from madre.dsl_compiler import VX11DSLCompiler
        
        compiler = VX11DSLCompiler()
        intent = {
            "domain": "TASK",
            "action": "create",
            "parameters": {"name": "test_task", "type": "audio"},
        }
        
        plan = compiler.compile(intent)
        assert plan is not None
        assert plan.domain == "TASK"
        assert len(plan.steps) > 0
    
    def test_compile_audio_intent(self):
        """Test: Compilar AUDIO intent"""
        from madre.dsl_compiler import VX11DSLCompiler
        
        compiler = VX11DSLCompiler()
        intent = {
            "domain": "AUDIO",
            "action": "restore",
            "parameters": {"file": "/test.wav", "preset": "default"},
        }
        
        plan = compiler.compile(intent)
        assert plan is not None
        assert plan.domain == "AUDIO"
        assert plan.intent_action == "restore"
    
    def test_compile_patch_intent(self):
        """Test: Compilar PATCH intent"""
        from madre.dsl_compiler import VX11DSLCompiler
        
        compiler = VX11DSLCompiler()
        intent = {
            "domain": "PATCH",
            "action": "generate",
            "parameters": {"scope": "sistema"},
        }
        
        plan = compiler.compile(intent)
        assert plan is not None
        assert plan.domain == "PATCH"
    
    def test_compile_and_validate(self):
        """Test: compile_and_validate con error handling"""
        from madre.dsl_compiler import VX11DSLCompiler
        
        compiler = VX11DSLCompiler()
        
        # Intent válido
        plan, errors = compiler.compile_and_validate({
            "domain": "TASK",
            "action": "create",
            "parameters": {},
        })
        assert plan is not None
        assert errors == []
        
        # Intent inválido
        plan, errors = compiler.compile_and_validate("not_a_dict")
        assert plan is None
        assert len(errors) > 0


# ============ PASO 4: Daughters Tests ============

class TestDaughterManager:
    """Validar Daughter Management"""
    
    def test_daughter_import(self):
        """Test: Daughter class can be imported"""
        from madre.daughters import Daughter, DaughterManager, get_daughter_manager
        
        assert Daughter is not None
        assert DaughterManager is not None
        manager = get_daughter_manager()
        assert manager is not None
    
    def test_daughter_creation(self):
        """Test: Crear Daughter"""
        from madre.daughters import Daughter
        
        daughter = Daughter(
            task_name="test_task",
            task_type="audio_restore",
            parameters={"file": "test.wav"},
            ttl_seconds=300,
        )
        
        assert daughter.id is not None
        assert daughter.status == "pending"
        assert daughter.ttl_seconds == 300
        assert daughter.progress == 0.0
    
    def test_daughter_ttl_check(self):
        """Test: Daughter TTL expiration check"""
        from madre.daughters import Daughter
        from datetime import datetime, timedelta
        
        daughter = Daughter("test", "test", {}, ttl_seconds=10)
        
        # No expirada inicialmente
        assert not daughter.is_expired()
        
        # Simular inicio
        daughter.started_at = datetime.utcnow() - timedelta(seconds=15)
        assert daughter.is_expired()
    
    def test_daughter_manager_creation(self):
        """Test: DaughterManager operations"""
        from madre.daughters import DaughterManager
        
        manager = DaughterManager()
        assert manager.max_concurrent == 8
        assert len(manager.daughters) == 0
    
    def test_daughter_to_dict(self):
        """Test: Daughter serialization"""
        from madre.daughters import Daughter
        
        daughter = Daughter("test", "audio", {}, ttl_seconds=300)
        d = daughter.to_dict()
        
        assert d["id"] == daughter.id
        assert d["task_name"] == "test"
        assert d["status"] == "pending"
        assert d["progress"] == 0.0


# ============ PASO 5: Ant Colony Tests ============

class TestAntColony:
    """Validar Hormiguero Mutante"""
    
    def test_pheromone_import(self):
        """Test: Pheromone class can be imported"""
        from hormiguero.ants_mutant import Pheromone, PheromoneType
        
        assert Pheromone is not None
        assert PheromoneType.DRIFT is not None
    
    def test_pheromone_creation(self):
        """Test: Crear Pheromone"""
        from hormiguero.ants_mutant import Pheromone, PheromoneType
        from datetime import datetime
        
        pheromone = Pheromone(
            id="ph_test",
            pheromone_type=PheromoneType.DRIFT,
            intensity=0.8,
            location="sistema",
        )
        
        assert pheromone.id == "ph_test"
        assert pheromone.pheromone_type == PheromoneType.DRIFT
        assert pheromone.intensity == 0.8
    
    def test_pheromone_decay(self):
        """Test: Pheromone decay mechanism"""
        from hormiguero.ants_mutant import Pheromone, PheromoneType
        
        pheromone = Pheromone(
            id="ph_test",
            pheromone_type=PheromoneType.DRIFT,
            intensity=0.8,
            location="test",
        )
        
        initial = pheromone.intensity
        pheromone.decay(rate=0.1)
        assert pheromone.intensity < initial
        assert abs(pheromone.intensity - 0.7) < 0.01  # Allow floating point precision
    
    def test_ant_creation(self):
        """Test: Crear Ant"""
        from hormiguero.ants_mutant import Ant
        
        ant = Ant("ant_1", "col_1", mutation_level=0)
        assert ant.id == "ant_1"
        assert ant.colony_id == "col_1"
        assert ant.energy == 1.0
        assert ant.is_alive()
    
    def test_ant_energy_system(self):
        """Test: Ant energy consumption"""
        from hormiguero.ants_mutant import Ant
        
        ant = Ant("ant_1", "col_1")
        initial = ant.energy
        
        ant.lose_energy(0.2)
        assert ant.energy < initial
        
        ant.gain_energy(0.1)
        assert ant.energy > (initial - 0.2)
    
    def test_colony_creation(self):
        """Test: Crear AntColony"""
        from hormiguero.ants_mutant import AntColony
        
        colony = AntColony("col_1", size=8, mutation_level=0)
        assert colony.id == "col_1"
        assert colony.size == 8
        assert len(colony.ants) == 8
    
    def test_colony_pheromone_deposit(self):
        """Test: Deposit pheromone en colonia"""
        from hormiguero.ants_mutant import AntColony, PheromoneType
        
        colony = AntColony("col_1", size=4)
        ph = colony.deposit_pheromone(
            PheromoneType.DRIFT,
            location="sistema",
            intensity=0.7,
        )
        
        assert ph is not None
        assert ph.intensity == 0.7
        assert len(colony.pheromones) > 0
    
    def test_queen_brain_creation(self):
        """Test: Crear QueenBrain"""
        from hormiguero.ants_mutant import QueenBrain, get_queen_brain
        
        queen = QueenBrain("queen_1")
        assert queen.id == "queen_1"
        assert len(queen.colonies) == 0
        
        # Test singleton
        queen2 = get_queen_brain()
        assert queen2 is not None


# ============ PASO 6: Manifestator Tests ============

class TestDriftScanner:
    """Validar Drift Detection"""
    
    def test_drift_scanner_import(self):
        """Test: DriftScanner can be imported"""
        from manifestator.patch_generator_v2 import (
            DriftScanner,
            get_drift_scanner,
        )
        
        scanner = DriftScanner()
        assert scanner is not None
        
        scanner_singleton = get_drift_scanner()
        assert scanner_singleton is not None
    
    def test_file_diff_creation(self):
        """Test: Crear FileDiff"""
        from manifestator.patch_generator_v2 import FileDiff
        
        diff = FileDiff(
            file_path="test.py",
            operation="modified",
            old_hash="abc123",
            new_hash="def456",
        )
        
        assert diff.file_path == "test.py"
        assert diff.operation == "modified"
        assert diff.to_dict()["op"] == "modified"
    
    def test_drift_report_creation(self):
        """Test: Crear DriftReport"""
        from manifestator.patch_generator_v2 import DriftReport, FileDiff
        
        diff = FileDiff(
            file_path="test.py",
            operation="added",
            new_hash="abc123",
        )
        
        report = DriftReport(
            drift_id="drift_1",
            detected_at="2025-12-10T00:00:00",
            scope="sistema",
            diffs=[diff],
            total_files_changed=1,
            severity=0.5,
        )
        
        assert report.drift_id == "drift_1"
        assert len(report.diffs) == 1
        assert report.to_dict()["files_changed"] == 1
    
    def test_patch_generator_import(self):
        """Test: PatchGenerator can be imported"""
        from manifestator.patch_generator_v2 import PatchGenerator
        
        assert PatchGenerator is not None
        assert hasattr(PatchGenerator, 'generate_patch')
    
    def test_patch_generation(self):
        """Test: Generate patch from drift report"""
        from manifestator.patch_generator_v2 import (
            DriftReport,
            FileDiff,
            PatchGenerator,
        )
        
        diff = FileDiff(
            file_path="config.json",
            operation="modified",
            old_hash="old",
            new_hash="new",
        )
        
        report = DriftReport(
            drift_id="drift_1",
            detected_at="2025-12-10T00:00:00",
            scope="config",
            diffs=[diff],
            total_files_changed=1,
            severity=0.3,
        )
        
        patch = PatchGenerator.generate_patch(report)
        assert patch is not None
        assert patch["patch_id"] is not None
        assert len(patch["operations"]) > 0
    
    def test_patch_validator_import(self):
        """Test: PatchValidator can be imported"""
        from manifestator.patch_generator_v2 import PatchValidator
        
        assert PatchValidator is not None
        assert hasattr(PatchValidator, 'validate_patch')


# ============ Compilation & Structure Tests ============

class TestCompilation:
    """Validar que todo compila"""
    
    def test_switch_main_compiles(self):
        """Test: switch/main.py compiles"""
        import py_compile
        import tempfile
        
        try:
            py_compile.compile('/home/elkakas314/vx11/switch/main.py', doraise=True)
            assert True
        except py_compile.PyCompileError:
            assert False, "switch/main.py compilation failed"
    
    def test_madre_main_compiles(self):
        """Test: madre/main.py compiles"""
        import py_compile
        
        try:
            py_compile.compile('/home/elkakas314/vx11/madre/main.py', doraise=True)
            assert True
        except py_compile.PyCompileError:
            assert False, "madre/main.py compilation failed"
    
    def test_hormiguero_main_compiles(self):
        """Test: hormiguero/main_v7.py compiles"""
        import py_compile
        
        try:
            py_compile.compile('/home/elkakas314/vx11/hormiguero/main_v7.py', doraise=True)
            assert True
        except py_compile.PyCompileError:
            assert False, "hormiguero/main_v7.py compilation failed"
    
    def test_manifestator_main_compiles(self):
        """Test: manifestator/main.py compiles"""
        import py_compile
        
        try:
            py_compile.compile('/home/elkakas314/vx11/manifestator/main.py', doraise=True)
            assert True
        except py_compile.PyCompileError:
            assert False, "manifestator/main.py compilation failed"


# ============ Module Integration Tests ============

class TestModuleIntegration:
    """Validar integración entre módulos"""
    
    def test_all_imports_available(self):
        """Test: Todos los módulos pueden importarse"""
        try:
            from switch.intelligence_layer import get_switch_intelligence_layer
            from switch.ga_router import get_ga_router
            from madre.dsl_compiler import VX11DSLCompiler
            from madre.daughters import get_daughter_manager
            from hormiguero.ants_mutant import get_queen_brain
            from manifestator.patch_generator_v2 import get_drift_scanner
            
            assert True
        except ImportError as e:
            assert False, f"Import failed: {e}"
    
    def test_no_circular_imports(self):
        """Test: No hay imports circulares"""
        # Si esto no falla, no hay circulares detectables
        import sys
        
        modules_to_check = [
            'switch.main',
            'madre.main',
            'hormiguero.main_v7',
            'manifestator.main',
        ]
        
        for module_name in modules_to_check:
            try:
                __import__(module_name)
                assert True
            except (ImportError, Exception) as e:
                # Pueden haber otros errores, pero no circulares
                if "circular" in str(e).lower():
                    assert False, f"Circular import in {module_name}"


# ============ Summary Report ============

if __name__ == "__main__":
    # Run with: pytest tests/test_paso7_integration.py -v
    pytest.main([__file__, "-v", "--tb=short"])
