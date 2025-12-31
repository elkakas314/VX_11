"""
Shell Tests Deprecation Wrapper
─────────────────────────────────

Shell-based test scripts (*.sh files in tests/) are being deprecated.
All shell tests should be converted to pytest for:
  - Portability (no bash dependency)
  - CI/CD consistency
  - Better error reporting
  - Fixture support

This module provides the deprecation notice.
Shell tests will be phased out by 2025-Q1.

Affected files:
  - tests/test_inee_p0_dormant.sh
  - tests/test_inee_p1_builder_intent.sh
  - tests/test_inee_db_schema.sh
  - tests/ventana_tests_front_door.sh
"""

import pytest
import os
from pathlib import Path


def test_shell_tests_deprecation_notice():
    """
    DEPRECATION: Shell tests should be converted to pytest.

    Rationale:
      - Bash is not available in all CI/CD environments
      - pytest provides better error reporting and fixtures
      - Cross-platform compatibility

    Action items:
      1. For tests/test_inee_p0_dormant.sh → Create tests/test_inee_p0_dormant.py
      2. For tests/test_inee_p1_builder_intent.sh → Create tests/test_inee_p1_builder_intent.py
      3. For tests/test_inee_db_schema.sh → Create tests/test_inee_db_schema.py
      4. For tests/ventana_tests_front_door.sh → Create tests/test_ventana_front_door.py

    Until converted, shell tests must be run manually:
      bash tests/test_inee_p0_dormant.sh
      bash tests/test_inee_p1_builder_intent.sh
      bash tests/test_inee_db_schema.sh
      bash tests/ventana_tests_front_door.sh
    """
    shell_test_files = [
        "tests/test_inee_p0_dormant.sh",
        "tests/test_inee_p1_builder_intent.sh",
        "tests/test_inee_db_schema.sh",
        "tests/ventana_tests_front_door.sh",
    ]

    found_shell_tests = []
    for shell_test in shell_test_files:
        if Path(shell_test).exists():
            found_shell_tests.append(shell_test)

    # Deprecation warning (test passes; just documents status)
    if found_shell_tests:
        pytest.warns(
            DeprecationWarning, match="Shell tests are deprecated; convert to pytest"
        )

    # This test always passes; it's purely informational
    assert True


if __name__ == "__main__":
    # For manual verification
    print(__doc__)
