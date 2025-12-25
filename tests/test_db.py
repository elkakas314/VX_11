"""
P0 Tests: Database Integrity

Tests for DB integrity checks and critical tables.
Markers: @pytest.mark.p0, @pytest.mark.db
"""

import pytest
import sqlite3


@pytest.mark.p0
@pytest.mark.db
def test_p0_5_pragma_quick_check(db_integrity_check):
    """
    P0.5: Verify PRAGMA quick_check passes
    Expected: Result is "ok"
    """
    assert "error" not in db_integrity_check, "DB check failed with error"
    assert (
        db_integrity_check["quick_check"] == "ok"
    ), f"PRAGMA quick_check failed: {db_integrity_check['quick_check']}"


@pytest.mark.p0
@pytest.mark.db
def test_p0_6_critical_tables_exist(critical_tables):
    """
    P0.6: Verify critical tables exist in database
    Expected: All critical tables present
    """
    missing = critical_tables["missing"]
    assert len(missing) == 0, f"Missing critical tables: {missing}"

    # Verify at least 80% coverage
    coverage_pct = (
        sum(1 for v in critical_tables["coverage"].values() if v)
        / len(critical_tables["critical"])
        * 100
    )
    assert coverage_pct >= 80, f"Table coverage only {coverage_pct}%"
