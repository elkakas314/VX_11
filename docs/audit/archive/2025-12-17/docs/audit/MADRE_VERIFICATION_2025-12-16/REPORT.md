# MADRE VERIFICATION — 2025-12-16

Estado general: FAIL

Resumen breve:
- Se verificaron las implementaciones clave de `madre` en lectura solamente.
- Hallazgos críticos: parser detecta verbos destructivos y mapea `delete` → `domain="system"`, `action="delete"` (evidencia en `madre/core/parser.py`).
- Policy: `delete` es clasificado como `RiskLevel.HIGH`; `requires_confirmation` devuelve True para MED/HIGH; acciones suicidas contra `madre`/`tentaculo_link` son denegadas (evidencia en `madre/core/policy.py`).
- Spawner safety: `Runner` inserta en `daughter_tasks` sin lanzar hijas (evidencia en `madre/core/runner.py`).
- DB: existen funciones para manipular `intents_log`, `madre_actions`, `tasks`, `context`, `daughter_tasks` y la documentación indica que `spawns`/`hijas_runtime` no son escritas por `madre` (evidencia en `madre/core/db.py` y `madre/README.md`).
- Tests: 33 tests ejecutados; 32 passed, 1 failed — `test_main_module_importable` falló esperando `/madre/chat` en `routes` (salida completa en raw pytest). Esto produce un FAIL en la verificación estricta.
- Runtime: no se detectó servicio `madre` corriendo en `127.0.0.1:8001` (curl mostró "Connection refused"); por tanto no se pudo verificar `openapi.json` en ejecución.

Tabla de verificación:

Ítem | Evidencia | Archivo | Estado
---|---:|---|---
1) ESTRUCTURA | tree de `madre/` (depth=2) | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/tree_madre.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/tree_madre.txt) | PASS
2) ENDPOINTS | Decoradores y referencias a `/madre/chat` y `/health` en código | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/madre_routes_grep.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/madre_routes_grep.txt) | PASS (en código)
3) PARSER (destructivos) | `DESTRUCTIVE_VERBS` + mapeo delete→domain/action | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/parser_snippet.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/parser_snippet.txt) | PASS
4) POLICY (HIGH + confirm) | `classify_risk` & `requires_confirmation` + suicidal denial | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/policy_snippet.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/policy_snippet.txt) | PASS
5) FLUJO DELETE (sin ejecutar) | Tests que verifican `pending_confirmation` y token generation; planner/runner producen WAITING | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/delete_flow_hits.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/delete_flow_hits.txt) | PASS
6) SPAWNER SAFETY | Runner inserta `DaughterTask` en BD; no lanza hijas | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/runner_snippet.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/runner_snippet.txt) | PASS
7) BD (tablas escritas / no escritas) | Referencias a `intents_log`, `madre_actions`, `tasks`, `context`, `daughter_tasks`; README indica no escribir `spawns`/`hijas_runtime` | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/db_table_hits.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/db_table_hits.txt) | PASS
8) TESTS | `pytest tests/test_madre.py` salida completa | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/pytest_madre.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/pytest_madre.txt) | PARTIAL (1 failure)
9) RUNTIME (si existe) | Attempt curl `/madre/health` — connection refused (no servicio activo) | [docs/audit/MADRE_VERIFICATION_2025-12-16/raw/curl_madre_health.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/curl_madre_health.txt) | NOT VERIFIED (no runtime)

Lo que está bien:
- Parser detecta y clasifica verbos destructivos correctamente.
- Policy aplica nivel HIGH a `delete` y requiere confirmación; también bloquea acciones suicidas contra `madre` y `tentaculo_link`.
- Runner implementa inserción segura en `daughter_tasks` y evita lanzar hijas directamente.
- DB functions y README están alineadas con la política "insert-only" para `daughter_tasks`.

Lo que falta / anomalías:
- Un test crítico (`test_main_module_importable`) falló, reclamando ausencia de `/madre/chat` en `routes` durante ejecución de tests — aunque el código contiene el decorador, el test fallido impide un PASS total. Ver [raw/pytest_madre.txt](docs/audit/MADRE_VERIFICATION_2025-12-16/raw/pytest_madre.txt).
- No se pudo verificar `openapi.json` por ausencia de servicio corriendo en `127.0.0.1:8001`.

Riesgos P0 detectados:
- Test failure sobre endpoint crítico `/madre/chat` → implica riesgo de desalineamiento entre la app importada en tests y la implementación expuesta en `main` (investigar diferencias de import path o app factory entre `main.py` y el módulo usado en tests).

Conclusión:
- Madre está correctamente implementada en código respecto a parser, policy, spawner-safety y persistencia en BD. Sin embargo, la verificación automática falla en el test de existencia de `/madre/chat` (1/33 tests fallidos) y no se pudo verificar runtime (servicio apagado). Por tanto: **Madre no pasa la verificación completa** (FAIL) hasta resolver la discrepancia detectada en tests y verificar el `openapi.json` en ejecución.

Evidencia y archivos raw se encuentran bajo: `docs/audit/MADRE_VERIFICATION_2025-12-16/raw/`
