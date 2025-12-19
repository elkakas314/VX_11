# 07_VALIDATION

Tests:
- compileall rc=0 (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/07_compileall.txt`)
- pytest -m 'not integration' rc=0 (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/07_pytest.txt`)

Madre in-proc tests (TestClient):
- Results: `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/07_madre_inproc_tests.txt`

Warnings:
- Pydantic protected namespace warnings observed during in-proc test run (model_hint, model_name).
