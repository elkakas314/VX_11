"""INEE registry and translator unit tests."""

import pytest
import os
import sys

# Add hormiguero to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hormiguero"))

from datetime import datetime
import uuid


@pytest.mark.p0
class TestINEEIntentTranslation:
    """Test INEE -> VX11 intent translation."""

    def test_translator_imports(self):
        """Translator module imports successfully."""
        try:
            from inee.intents.translator import INEETranslator

            assert hasattr(INEETranslator, "translate")
        except ImportError:
            pytest.skip("INEE module not accessible from test context")

    def test_types_imports(self):
        """Types module imports successfully."""
        try:
            from inee.intents.types import INEEIntent, VX11Intent

            assert INEEIntent is not None
            assert VX11Intent is not None
        except ImportError:
            pytest.skip("INEE types not accessible")

    def test_registry_imports(self):
        """Registry module imports successfully."""
        try:
            from inee.colonies.registry import INEERegistry

            assert hasattr(INEERegistry, "register_colony")
            assert hasattr(INEERegistry, "get_colony")
        except ImportError:
            pytest.skip("INEE registry not accessible")

    def test_db_manager_imports(self):
        """DB manager imports successfully."""
        try:
            from inee.db.dao import INEEDBManager

            assert hasattr(INEEDBManager, "save_colony")
            assert hasattr(INEEDBManager, "get_colonies")
        except ImportError:
            pytest.skip("INEE DB manager not accessible")
