"""INEE P0 tests - simplified."""

import os
import pytest


@pytest.mark.p0
class TestINEEBasic:
    """INEE basic checks - OFF by default."""

    def test_flags_off_by_default(self):
        """Feature flags default to OFF."""
        assert os.getenv("VX11_INEE_ENABLED", "0") == "0"

    def test_inee_module_in_hormiguero(self):
        """INEE module exists in hormiguero."""
        assert os.path.isdir("hormiguero/hormiguero/inee")
        assert os.path.isfile("hormiguero/hormiguero/inee/__init__.py")

    def test_inee_submodules_exist(self):
        """INEE submodules exist."""
        assert os.path.isdir("hormiguero/hormiguero/inee/api")
        assert os.path.isdir("hormiguero/hormiguero/inee/intents")
        assert os.path.isdir("hormiguero/hormiguero/inee/colonies")
        assert os.path.isdir("hormiguero/hormiguero/inee/db")

    def test_inee_cannonical_docs_exist(self):
        """INEE canonical documentation exists."""
        assert os.path.isfile("docs/canon/VX11_INEE_OPTIONAL_CANONICAL_v1.0.0.json")
        assert os.path.isfile("docs/canon/VX11_HORMIGUERO_CANONICAL_v7.3.0.json")

    def test_tentaculo_inee_routes_file_exists(self):
        """Tentaculo INEE remote routes file exists."""
        assert os.path.isfile("tentaculo_link/inee_remote_routes.py")
