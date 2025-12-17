# Integration & Cleanup Blinding Report

Generated: 2025-12-17T22:11:22Z

**Fuente de verdad (verificadas):**
- [docs/audit/DB_MAP_v7_FINAL.md](docs/audit/DB_MAP_v7_FINAL.md)
- [docs/audit/DB_SCHEMA_v7_FINAL.json](docs/audit/DB_SCHEMA_v7_FINAL.json)

**Tests marcados como `integration` (saltan por defecto):**
- tests/test_all_healthchecks.py::test_health_all
- tests/test_health_endpoints.py::test_health_endpoints
- tests/test_switch_auto.py::test_switch_auto_returns_engine
- tests/test_switch_chat_and_breaker.py::test_switch_chat_endpoint
- tests/test_switch_deepseek_staging.py::test_switch_deepseek_fallback_when_no_key
- tests/test_switch_local.py::test_switch_local_route

**Cómo activar integración:**
Exportar `VX11_INTEGRATION=1` y ejecutar `pytest`.

**Archivo de exclusiones CORE:**
- docs/audit/CLEANUP_EXCLUDES_CORE.txt

**Qué se regeneró de DB_MAP/SCHEMA:**
- `docs/audit/DB_MAP_v7_FINAL.md` (actualizado)
- `docs/audit/DB_SCHEMA_v7_FINAL.json` (actualizado)
- `docs/audit/DB_MAP_v7_META.txt` (integrity + size)

**Commits recientes (local):**
```
$(git log -2 --oneline)
```

**Evidencias generadas en:**
- `docs/audit/integration_blind_*` (p.ej. la carpeta creada contiene: `00_pwd.txt`, `00_git_status_sb.txt`, `00_truth_sources_ls.txt`, `03_fail_summary_ref.txt` si existía, `01_pytest_unit_after_integration_marks.txt`, `02_cleanup_excludes_core.txt`, `02_contract_snippets.txt`, `03_dbmap_regen.txt`, `04_diff_stat.txt`, `05_last_two_commits.txt`)

---

Si necesita que ejecute los tests de integración ahora, confirmarlo explícitamente (operación destructiva: puede requerir levantar servicios). Para cualquier operación que mueva archivos a `attic/` o ejecute limpieza, el flujo deberá cargar `docs/audit/CLEANUP_EXCLUDES_CORE.txt` y abortar si hay coincidencias CORE.
