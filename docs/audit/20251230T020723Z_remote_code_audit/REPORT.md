# Auditoría de Código (local) — 2025-12-30T02:07:23Z

Resumen
- Directorio de evidencia: `docs/audit/20251230T020723Z_remote_code_audit/`
- Escaneos generados: `00_sync.txt`, `01_tree.txt`, `02_compose_ports.txt`, `03_operator_bypass_scan.txt`, `04_policy_corr_scan.txt`, `05_secrets_scan.txt`.

Hallazgos (evidencia en archivos anteriores)
- Estado Git y archivos modificados/ eliminados: ver `00_sync.txt`. Nota: hay múltiples eliminaciones bajo `operator/frontend/` y `operator/backend/` indicadas como `D` en git status.
- Comprobación de puertos y compose: ver `02_compose_ports.txt`.
- Búsqueda de bypass en Operator: ver `03_operator_bypass_scan.txt`.
- Política / correlation_id: ver `04_policy_corr_scan.txt`.
- Scan de secretos (nombres): ver `05_secrets_scan.txt` (solo patrones, sin valores).

GAPs y prioridades iniciales
- P0: Verificar restauración/estado de `operator/frontend` (archivos marcados como eliminados). Acción mínima: revisar `git restore` o recuperar desde remoto si fue borrado localmente.
- P0: Confirmar que el frontend no contenga hardcoded internal ports (evidencia: `03_operator_bypass_scan.txt`).
- P0: Asegurar `X-Correlation-Id` y que proxies devuelvan siempre `X-Correlation-Id` en respuestas (evidencia: `04_policy_corr_scan.txt`).
- P1: Verificación de `solo_madre` como runtime default y políticas OFF_BY_POLICY (ver `04_policy_corr_scan.txt`).

Siguientes pasos recomendados
1. Ejecutar `docs/audit/CORE_GATES_PACK.md` (pasos automáticos para core gates) y guardar salidas en `docs/audit/<TS>_core_gates/`.
2. Aplicar fixes P0 mínimos (ver plan CODEX). Cada fix = 1 commit atómico.
3. Re-ejecutar core gates y validar PASS/FAIL.

Archivos de evidence (copiar y revisar):
- `docs/audit/20251230T020723Z_remote_code_audit/00_sync.txt`
- `docs/audit/20251230T020723Z_remote_code_audit/01_tree.txt`
- `docs/audit/20251230T020723Z_remote_code_audit/02_compose_ports.txt`
- `docs/audit/20251230T020723Z_remote_code_audit/03_operator_bypass_scan.txt`
- `docs/audit/20251230T020723Z_remote_code_audit/04_policy_corr_scan.txt`
- `docs/audit/20251230T020723Z_remote_code_audit/05_secrets_scan.txt`

Nota: Este reporte se generó automáticamente a partir de las exploraciones locales; no se han aplicado cambios en código aún.
