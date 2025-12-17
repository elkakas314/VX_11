# EVIDENCE INDEX — MADRE VERIFICATION 2025-12-16

Listado de archivos (raw) generados durante la verificación:

- Tree (madre/ depth=2): [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/tree_madre.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/tree_madre.txt)
- Busqueda openapi/paths: [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/openapi_and_paths_search.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/openapi_and_paths_search.txt)
- Rutas FastAPI detectadas: [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/madre_routes_grep.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/madre_routes_grep.txt)
- Parser (DESTRUCTIVE_VERBS y mapeo): [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/parser_delete_mappings.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/parser_delete_mappings.txt)
- Fragmento parser: [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/parser_snippet.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/parser_snippet.txt)
- Policy (RiskLevel, requires_confirmation, suicidal denial): [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/policy_and_suicide_checks.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/policy_and_suicide_checks.txt)
- Fragmento policy: [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/policy_snippet.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/policy_snippet.txt)
- Runner (inserción daughter_tasks): [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/runner_snippet.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/runner_snippet.txt)
- BD: referencias tablas y funciones: [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/db_table_hits.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/db_table_hits.txt)
- Delete flow / confirmation hits: [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/delete_flow_hits.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/delete_flow_hits.txt)
- Pytest output (tests/test_madre.py): [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/pytest_madre.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/pytest_madre.txt)
- Runtime curl (health): [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/curl_madre_health.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/curl_madre_health.txt)

Notas:
- Todos los archivos son lecturas y salidas de comandos (no se modificó código).
- Para reproducir: activar el entorno virtual y ejecutar los mismos comandos (ls/find, grep, pytest, curl) con la misma ruta del repo.
