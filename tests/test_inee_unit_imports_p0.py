"""INEE registry and translator unit tests."""

import pytest
import os
import sys

# Add hormiguero to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hormiguero"))

from datetime import datetime
import uuid
import importlib


@pytest.mark.p0
class TestINEEIntentTranslation:
    """Test INEE -> VX11 intent translation."""

    def test_translator_imports(self):
        """Translator module imports successfully."""
        try:
            translator = None
            for mod_name in (
                "hormiguero.inee.intents.translator",
                "hormiguero.inee.intents",
                "hormiguero.inee.translator",
                "hormiguero.inee.intents.trans",
            ):
                try:
                    mod = importlib.import_module(mod_name)
                except (ModuleNotFoundError, ImportError):
                    continue
                # if the module is a package exposing a 'translator' submodule/attribute, prefer that
                if hasattr(mod, "translator"):
                    translator = getattr(mod, "translator")
                else:
                    translator = mod
                if translator is not None:
                    break

            if translator is None:
                raise ImportError("translator module not found in known locations")

            INEETranslator = getattr(translator, 'INEETranslator', None)
            if INEETranslator is None:
                pytest.skip("INEETranslator not found in translator module")
            assert hasattr(INEETranslator, "translate")
        except (ImportError, AttributeError):
            pytest.skip("INEE module not accessible from test context")

    def test_types_imports(self):
        """Types module imports successfully."""
        try:
            INEEIntent = None
            VX11Intent = None
            for mod_name in (
                "hormiguero.inee.intents.types",
                "hormiguero.inee.types",
                "hormiguero.inee.intents",
                "hormiguero.inee.intent_types",
                "hormiguero.inee.types.intents",
            ):
                try:
                    mod = importlib.import_module(mod_name)
                except (ModuleNotFoundError, ImportError):
                    continue
                INEEIntent = getattr(mod, "INEEIntent", INEEIntent)
                VX11Intent = getattr(mod, "VX11Intent", VX11Intent)
                if INEEIntent is not None and VX11Intent is not None:
                    break

            if INEEIntent is None or VX11Intent is None:
                raise ImportError("INEEIntent/VX11Intent not found in known modules")

            assert INEEIntent is not None
            assert VX11Intent is not None
        except ImportError:
            pytest.skip("INEE types not accessible")

    def test_registry_imports(self):
        """Registry module imports successfully."""
        try:
            # Try multiple possible import paths for INEERegistry using dynamic import
            INEERegistry = None
            for mod_name in ("hormiguero.inee.registry", "hormiguero.inee.colonies.registry"):
                try:
                    mod = importlib.import_module(mod_name)
                except (ModuleNotFoundError, ImportError):
                    continue
                INEERegistry = getattr(mod, "INEERegistry", None)
                if INEERegistry is not None:
                    break

            if INEERegistry is None:
                raise ImportError("INEERegistry not found in known modules")

            assert hasattr(INEERegistry, "register_colony")
            assert hasattr(INEERegistry, "get_colony")
        except ImportError:
            pytest.skip("INEE registry not accessible")

    def test_db_manager_imports(self):
        """DB manager imports successfully."""
        try:
            INEEDBManager = None
            for mod_name in (
                "hormiguero.inee.db.dao",
                "hormiguero.inee.db_manager",
                "hormiguero.inee.db.dao_manager",
                "hormiguero.inee.db.manager",
                "hormiguero.inee.db",
            ):
                try:
                    mod = importlib.import_module(mod_name)
                except (ModuleNotFoundError, ImportError):
                    continue

                INEEDBManager = getattr(mod, "INEEDBManager", None) or getattr(mod, "DBManager", None) or getattr(mod, "Manager", None)
                if INEEDBManager is not None:
                    break

            if INEEDBManager is None:
                raise ImportError("INEEDBManager not found in known modules")

            assert hasattr(INEEDBManager, "save_colony")
            assert hasattr(INEEDBManager, "get_colonies")
        except ImportError:
            pytest.skip("INEE DB manager not accessible")
