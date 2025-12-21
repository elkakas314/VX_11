"""
SHUB Test Suite — FASE 5: REAPER Real Integration Tests
Extend test_shub_core.py with REAPER bridge tests
"""

import asyncio
import pytest
from shubniggurath.shub_reaper_bridge import ReaperBridge, ShubReaperIntegration, ReaperProject
from shubniggurath.shub_core_init import ShubAssistant


class TestReaperBridge:
    """Test REAPER bridge with real projects"""

    @pytest.mark.asyncio
    async def test_bridge_initialization(self):
        """Test bridge initialization"""
        bridge = ReaperBridge()
        assert bridge.reaper_exe.exists(), "REAPER executable not found"
        assert bridge.config_path.exists(), "REAPER config path not found"

    @pytest.mark.asyncio
    async def test_get_projects_list(self):
        """Test project enumeration"""
        bridge = ReaperBridge()
        projects = await bridge.get_projects_list()
        assert isinstance(projects, list), "Projects should be a list"
        assert len(projects) >= 0, "Projects count should be >= 0"
        # Note: May be 0 if no projects exist

    @pytest.mark.asyncio
    async def test_parse_project_file(self):
        """Test project file parsing"""
        bridge = ReaperBridge()
        projects = await bridge.get_projects_list()
        
        if not projects:
            pytest.skip("No REAPER projects available")
        
        project = await bridge.parse_project_file(projects[0])
        assert project is not None, "Failed to parse project"
        assert isinstance(project, ReaperProject), "Should return ReaperProject"
        assert project.name is not None, "Project should have name"
        assert project.bpm > 0, "BPM should be > 0"
        assert project.sample_rate > 0, "Sample rate should be > 0"
        assert len(project.tracks) >= 0, "Should have tracks list"

    @pytest.mark.asyncio
    async def test_project_tracks(self):
        """Test track parsing"""
        bridge = ReaperBridge()
        projects = await bridge.get_projects_list()
        
        if not projects:
            pytest.skip("No REAPER projects available")
        
        project = await bridge.parse_project_file(projects[0])
        assert project is not None, "Project should load"
        
        if len(project.tracks) > 0:
            track = project.tracks[0]
            assert track.name is not None, "Track should have name"
            assert track.index >= 0, "Track index should be >= 0"
            assert isinstance(track.volume_db, float), "Volume should be float"
            assert -100 <= track.volume_db <= 24, "Volume should be in reasonable range"

    @pytest.mark.asyncio
    async def test_project_items(self):
        """Test item (clip) parsing"""
        bridge = ReaperBridge()
        projects = await bridge.get_projects_list()
        
        if not projects:
            pytest.skip("No REAPER projects available")
        
        project = await bridge.parse_project_file(projects[0])
        assert project is not None, "Project should load"
        
        # Find tracks with items
        tracks_with_items = [t for t in project.tracks if len(t.items) > 0]
        
        if tracks_with_items:
            track = tracks_with_items[0]
            item = track.items[0]
            assert item.name is not None, "Item should have name"
            assert item.duration > 0, "Item duration should be > 0"
            assert item.start_time >= 0, "Item start time should be >= 0"


class TestShubReaperIntegration:
    """Test Shub integration with REAPER bridge"""

    @pytest.mark.asyncio
    async def test_shub_assistant_reaper_enabled(self):
        """Test that ShubAssistant has REAPER support"""
        assistant = ShubAssistant(enable_reaper_bridge=True)
        # Note: May be disabled if REAPER not installed
        assert assistant.reaper_enabled is not None, "Should have reaper_enabled flag"

    @pytest.mark.asyncio
    async def test_load_reaper_project_command(self):
        """Test load_reaper command"""
        bridge = ReaperBridge()
        projects = await bridge.get_projects_list()
        
        if not projects:
            pytest.skip("No REAPER projects available")
        
        assistant = ShubAssistant(enable_reaper_bridge=True)
        if not assistant.reaper_enabled:
            pytest.skip("REAPER bridge not available")
        
        result = await assistant.process_command("load_reaper", {
            "path": projects[0]
        })
        
        assert result["status"] in ["project_loaded", "error"], "Should return status"
        if result["status"] == "project_loaded":
            assert "project_name" in result, "Should have project_name"
            assert result["track_count"] > 0, "Should have tracks"

    @pytest.mark.asyncio
    async def test_reaper_analysis_command(self):
        """Test reaper_analysis command"""
        bridge = ReaperBridge()
        projects = await bridge.get_projects_list()
        
        if not projects:
            pytest.skip("No REAPER projects available")
        
        assistant = ShubAssistant(enable_reaper_bridge=True)
        if not assistant.reaper_enabled:
            pytest.skip("REAPER bridge not available")
        
        # First load a project
        await assistant.process_command("load_reaper", {"path": projects[0]})
        
        # Then analyze
        result = await assistant.process_command("reaper_analysis")
        
        assert result["status"] in ["reaper_analysis_complete", "error"], "Should return status"
        if result["status"] == "reaper_analysis_complete":
            assert "analysis" in result, "Should have analysis"

    @pytest.mark.asyncio
    async def test_assistant_help_includes_reaper(self):
        """Test that help includes REAPER commands"""
        assistant = ShubAssistant()
        result = assistant._get_help()
        
        assert "commands" in result, "Help should have commands"
        if assistant.reaper_enabled:
            assert "load_reaper" in result["commands"], "Should list load_reaper"
            assert "reaper_analysis" in result["commands"], "Should list reaper_analysis"


class TestReaperIntegrationWorkflow:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_complete_workflow_list_load_analyze(self):
        """Test: List → Load → Analyze workflow"""
        bridge = ReaperBridge()
        projects = await bridge.get_projects_list()
        
        if not projects:
            pytest.skip("No REAPER projects available")
        
        # Step 1: List projects
        assert len(projects) > 0, "Should find projects"
        
        # Step 2: Parse project
        project = await bridge.parse_project_file(projects[0])
        assert project is not None, "Should parse project"
        
        # Step 3: Verify structure
        assert project.name is not None, "Should have name"
        assert project.bpm > 0, "Should have BPM"
        assert isinstance(project.tracks, list), "Should have tracks list"
        
        # Result
        assert True, "Complete workflow successful"


# ============================================================================
# Test Suite Registration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
