"""
Unit tests for VX11 Stability P0 Runner.

Tests the harness without executing docker commands (mocked).
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.vx11_stability_p0 import (
    StabilityP0Runner,
    MODULE_DEPENDENCY_MAP,
    topological_sort,
    find_test_files,
)


class TestTopologicalSort:
    """Test dependency sorting."""

    def test_topological_sort_basic(self):
        """Test that topological_sort respects dependencies."""
        modules = ["switch", "hermes", "hormiguero"]
        sorted_modules = topological_sort(modules)

        # switch should come before hermes (switch has no deps, hermes depends on switch)
        assert sorted_modules.index("switch") < sorted_modules.index("hermes")

    def test_topological_sort_all_modules(self):
        """Test sort on all canonical modules."""
        from scripts.vx11_stability_p0 import CANONICAL_MODULE_ORDER

        sorted_modules = topological_sort(CANONICAL_MODULE_ORDER)

        assert len(sorted_modules) == len(CANONICAL_MODULE_ORDER)
        assert set(sorted_modules) == set(CANONICAL_MODULE_ORDER)

    def test_topological_sort_respects_depends_on(self):
        """Verify that module dependencies are respected."""
        modules = ["hormiguero", "hermes", "switch"]
        sorted_modules = topological_sort(modules)

        # hormiguero depends on hermes, hermes depends on switch
        assert sorted_modules.index("switch") < sorted_modules.index("hermes")
        assert sorted_modules.index("hermes") < sorted_modules.index("hormiguero")


class TestModuleDependencyMap:
    """Test the module dependency configuration."""

    def test_module_dependency_map_structure(self):
        """Verify all modules have required keys."""
        for module_name, config in MODULE_DEPENDENCY_MAP.items():
            assert "description" in config
            assert "services" in config
            assert "depends_on" in config
            assert "health_endpoints" in config
            assert "test_patterns" in config
            assert isinstance(config["services"], list)
            assert isinstance(config["depends_on"], list)

    def test_all_dependencies_exist(self):
        """Check that all listed dependencies exist in map."""
        for module_name, config in MODULE_DEPENDENCY_MAP.items():
            for dep in config["depends_on"]:
                if dep != "baseline":
                    assert (
                        dep in MODULE_DEPENDENCY_MAP
                    ), f"Module {module_name} depends on {dep} which doesn't exist"


class TestFindTestFiles:
    """Test test file discovery."""

    def test_find_test_files_with_existing_pattern(self):
        """Test finding actual test files."""
        # This assumes test_switch_*.py files exist
        files = find_test_files("test_switch_*.py")
        # Should find at least one switch test
        assert any(
            "switch" in f for f in files
        ), f"Expected to find switch tests, got: {files}"

    def test_find_test_files_with_non_matching_pattern(self):
        """Test behavior when pattern doesn't match."""
        files = find_test_files("test_nonexistent_*.py")
        assert files == [], "Should return empty list for non-matching pattern"

    def test_find_test_files_respects_glob(self):
        """Test that glob patterns work."""
        files = find_test_files("test_*.py")
        # Should find many test files
        assert len(files) > 0, "Should find test files with test_*.py pattern"


class TestStabilityP0RunnerInit:
    """Test runner initialization."""

    def test_init_default_values(self):
        """Test runner initializes with defaults."""
        runner = StabilityP0Runner()

        assert runner.mode == "low_power"
        assert runner.cycles == 1
        assert runner.timeout_sec == 20
        assert runner.keep_core == True
        assert "vx11_stability_" in str(runner.audit_dir)

    def test_init_with_custom_values(self):
        """Test runner initializes with custom values."""
        runner = StabilityP0Runner(
            mode="operative_core",
            cycles=3,
            modules="switch,hermes",
            timeout_sec=30,
            keep_core=False,
        )

        assert runner.mode == "operative_core"
        assert runner.cycles == 3
        assert runner.modules == ["switch", "hermes"]
        assert runner.timeout_sec == 30
        assert runner.keep_core == False

    def test_audit_dir_creation(self):
        """Test that audit directory is created."""
        runner = StabilityP0Runner()
        assert runner.audit_dir.exists()
        assert (runner.audit_dir / "raw").exists()

    def test_results_structure(self):
        """Test that results dict is initialized correctly."""
        runner = StabilityP0Runner()

        assert "timestamp" in runner.results
        assert "mode" in runner.results
        assert "cycles" in runner.results
        assert "modules_tested" in runner.results
        assert "summary" in runner.results
        assert "modules" in runner.results


class TestReportGeneration:
    """Test report generation."""

    def test_markdown_generation(self):
        """Test markdown report generation."""
        runner = StabilityP0Runner()

        # Manually add a module result
        runner.results["modules"]["test-module"] = {
            "name": "test-module",
            "status": "PASS",
            "metrics": {},
            "test_results": {},
            "errors": [],
        }
        runner.results["modules_tested"].append("test-module")
        runner.results["summary"]["total_modules"] = 1
        runner.results["summary"]["passed"] = 1

        md = runner._generate_markdown()

        assert "VX11 Stability P0 Report" in md
        assert "test-module" in md
        assert "PASS" in md
        assert "Summary" in md

    def test_json_report_creation(self):
        """Test JSON report is created."""
        runner = StabilityP0Runner()
        runner._generate_reports()

        json_file = runner.audit_dir / "REPORT.json"
        assert json_file.exists()

        # Verify it's valid JSON
        data = json.loads(json_file.read_text())
        assert "timestamp" in data
        assert "modules" in data

    def test_markdown_report_creation(self):
        """Test Markdown report is created."""
        runner = StabilityP0Runner()
        runner._generate_reports()

        md_file = runner.audit_dir / "REPORT.md"
        assert md_file.exists()
        assert md_file.read_text(), "Markdown file should not be empty"


@pytest.mark.unit
@pytest.mark.stability
class TestStabilityP0Integration:
    """Integration tests at unit level (no docker calls)."""

    @patch("scripts.vx11_stability_p0.docker_up_services")
    @patch("scripts.vx11_stability_p0.docker_down_services")
    def test_run_with_mocked_docker(self, mock_down, mock_up):
        """Test harness execution with mocked docker."""
        mock_up.return_value = (0, "OK")
        mock_down.return_value = (0, "OK")

        runner = StabilityP0Runner(
            cycles=1,
            modules="switch",
            keep_core=True,
        )

        # Don't actually run (would call health_check with real curl)
        # Just verify setup is correct
        assert runner.modules == ["switch"]
        assert runner.cycles == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
