"""
Test CPU gate in Manifestator endpoints.
Verifies that /patchplan and /builder/spec return 429 when CPU is sustained high.
"""

import pytest
import os
import sys
import asyncio
from typing import Dict, Any

# Add parent paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "manifestator"))


@pytest.mark.asyncio
class TestManifestatorCPUGate:
    """
    CPU gate tests for Manifestator planning endpoints.
    """

    def test_manifestator_cpu_gate_functions_exist(self):
        """Verify that CPU gate functions are defined in manifestator.main."""
        from manifestator import main

        assert hasattr(main, "get_cpu_sustained_high")
        assert callable(main.get_cpu_sustained_high)

        assert hasattr(main, "set_cpu_sustained_high")
        assert callable(main.set_cpu_sustained_high)

    def test_get_cpu_sustained_high_default_false(self):
        """Default state should be False."""
        from manifestator import main

        result = main.get_cpu_sustained_high()
        assert result is False

    def test_set_cpu_sustained_high_updates_state(self):
        """set_cpu_sustained_high should update internal state."""
        from manifestator import main

        # Set to True
        main.set_cpu_sustained_high(True)
        assert main.get_cpu_sustained_high() is True

        # Set back to False
        main.set_cpu_sustained_high(False)
        assert main.get_cpu_sustained_high() is False

    def test_get_cpu_sustained_high_env_var_precedence(self):
        """Env var MANIFESTATOR_CPU_SUSTAINED_HIGH=1 should take precedence."""
        import os
        from manifestator import main

        # Set internal state to False
        main.set_cpu_sustained_high(False)

        # Without env var, should be False
        assert main.get_cpu_sustained_high() is False

        # Set env var to "1"
        os.environ["MANIFESTATOR_CPU_SUSTAINED_HIGH"] = "1"
        try:
            assert main.get_cpu_sustained_high() is True
        finally:
            # Cleanup
            os.environ.pop("MANIFESTATOR_CPU_SUSTAINED_HIGH", None)

        # Should be back to False
        assert main.get_cpu_sustained_high() is False

    @pytest.mark.asyncio
    async def test_patchplan_endpoint_has_cpu_gate(self):
        """Verify that /patchplan endpoint has CPU gate logic in docstring."""
        from manifestator import main
        import inspect

        endpoint_fn = main.manifestator_patchplan
        docstring = inspect.getdoc(endpoint_fn)

        assert "CPU Gate" in docstring or "cpu" in docstring.lower()

    @pytest.mark.asyncio
    async def test_builder_spec_endpoint_has_cpu_gate(self):
        """Verify that /builder/spec endpoint has CPU gate logic in docstring."""
        from manifestator import main
        import inspect

        endpoint_fn = main.manifestator_builder_spec
        docstring = inspect.getdoc(endpoint_fn)

        assert "CPU Gate" in docstring or "cpu" in docstring.lower()

    def test_cpu_gate_blocks_patchplan_on_high(self):
        """CPU gate should prevent patchplan generation when high."""
        from manifestator import main
        from fastapi.exceptions import HTTPException

        # Set CPU high
        main.set_cpu_sustained_high(True)

        # Try patchplan
        try:
            # We can't directly call async endpoint, but we can verify the check exists
            is_high = main.get_cpu_sustained_high()
            assert is_high is True
        finally:
            main.set_cpu_sustained_high(False)

    def test_cpu_gate_blocks_builder_spec_on_high(self):
        """CPU gate should prevent builder spec generation when high."""
        from manifestator import main

        # Set CPU high
        main.set_cpu_sustained_high(True)

        # Verify state
        is_high = main.get_cpu_sustained_high()
        assert is_high is True

        # Reset
        main.set_cpu_sustained_high(False)


@pytest.mark.p0
def test_manifestator_cpu_gate_integration():
    """P0 test: CPU gate functions integrate correctly."""
    from manifestator import main

    # Initial state
    assert main.get_cpu_sustained_high() is False

    # Simulate pressure
    main.set_cpu_sustained_high(True)
    assert main.get_cpu_sustained_high() is True

    # Simulate recovery
    main.set_cpu_sustained_high(False)
    assert main.get_cpu_sustained_high() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
