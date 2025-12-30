# CORE_GATES_PACK

Propósito: checklist reproducible para validar el núcleo del sistema VX11 (single-entrypoint, solo_madre, policy, DB integrity).

Preparación
- Sincronizar rama `main` con ff-only (ver `docs/audit/<TS>_apply_plan/00_sync.txt`).

Comandos exactos (ejecutar desde la raíz del repo):

1) Sync ff-only
## CORE_GATES_PACK

Propósito: checklist reproducible para validar el núcleo del sistema VX11: Single-Entrypoint (solo `tentaculo_link:8000` expuesto), mecanismos de `solo_madre`, comportamiento OFF_BY_POLICY (403 JSON), y sanity de BD.

Preparación
- Trabajar en `main`. Sincronizar con `--ff-only`.

Uso general
- Ejecutar desde la raíz del repositorio. Todas las salidas deben guardarse en `$OUT`.

Ejemplo sesión (comandos exactos):

1) Sync y crear OUT

```bash
set -euo pipefail
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="docs/audit/${TS}_p0_single_entrypoint"
mkdir -p "$OUT"

git checkout main
git fetch --all --prune
git pull --ff-only
git status -sb | tee "$OUT/git_pre.txt"
```

2) Archivos de overlay

- Archivo prod overlay: `docker-compose.prod.yml` (usar con el comando de abajo). No se modifica `docker-compose.yml` base.

3) Comprobar `ports:` en ambos ficheros

```bash
rg -n "^\s*ports:\b" docker-compose.yml docker-compose.prod.yml | tee "$OUT/ports_diff.txt" || true
```

4) Modo DEV (core)

```bash
# Levantar servicios core (dev/test)
docker compose --profile core up -d --build
# Guardar ps
docker compose --profile core ps | tee "$OUT/core_ps.txt"
```

5) Modo PROD (overlay) — Single-Entrypoint

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps | tee "$OUT/prod_ps.txt"
docker ps --format 'table {{.Names}}\t{{.Ports}}' | tee "$OUT/prod_ports.txt"
```

Verificación de Single-Entrypoint: `prod_ports.txt` debe mostrar puerto publicado solo para el contenedor `vx11-tentaculo-link` (host 8000).

6) Health y endpoints (usar token si es requerido)

# Definir token localmente (NO commitear tokens)
```bash
export VX11_TOKEN=${VX11_TOKEN:-vx11-local-token}
export CORR_ID="core-gates-$(date -u +%s)"

# Health
curl -sS -i -H "X-Correlation-Id: $CORR_ID" http://127.0.0.1:8000/health | tee "$OUT/health_8000.txt"

# Operator status via gateway (requires auth header X-VX11-Token)
curl -sS -i -H "X-VX11-Token: $VX11_TOKEN" -H "X-Correlation-Id: $CORR_ID" http://127.0.0.1:8000/operator/api/v1/status | tee "$OUT/operator_status_via_8000.txt" || true
```

7) Discover Madre OpenAPI paths relevant to power/window/policy

```bash
curl -sS http://127.0.0.1:8001/openapi.json | jq '.paths|keys[]|select(test("power|window|policy"))' | tee "$OUT/madre_openapi_paths.txt" || true
```

8) Aplicar `solo_madre` (si el endpoint existe)

```bash
if curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/madre/power/policy/solo_madre/apply | grep -q "20\|30"; then
	curl -sS -X POST http://127.0.0.1:8001/madre/power/policy/solo_madre/apply -H 'Content-Type: application/json' -d '{}' -H "X-Correlation-Id: $CORR_ID" -o "$OUT/solo_madre_apply.json" || true
else
	echo "NO_ENDPOINT" | tee "$OUT/solo_madre_apply.json"
fi
```

9) Abrir ventana (if endpoint exists) y verificar effect via operator endpoint

```bash
if curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/madre/power/window/open | grep -q "20\|30"; then
	curl -sS -X POST http://127.0.0.1:8001/madre/power/window/open -H 'Content-Type: application/json' -d '{"services":["switch"],"ttl_sec":120}' -H "X-Correlation-Id: $CORR_ID" -o "$OUT/window_open.json" || true
	sleep 2
	curl -sS -i -H "X-VX11-Token: $VX11_TOKEN" -H "X-Correlation-Id: $CORR_ID" http://127.0.0.1:8000/operator/api/v1/status | tee "$OUT/operator_status_after_window.txt" || true
else
	echo "NO_WINDOW_ENDPOINT" | tee "$OUT/window_open.json"
fi
```

10) Verificar OFF_BY_POLICY behaviour (expect 403 JSON when policy denies)

```bash
# Use a known operator endpoint that returns policy when restricted. If unknown, try /operator/api/v1/status without token.
curl -sS -o "$OUT/off_by_policy_response.json" -w "%{http_code}" http://127.0.0.1:8000/operator/api/v1/status || true
jq -e 'type=="object" and (.status? // .code? // .detail?)' "$OUT/off_by_policy_response.json" > /dev/null 2>&1 || true
```

11) DB checks

```bash
sqlite3 data/runtime/vx11.db "PRAGMA busy_timeout=5000; PRAGMA quick_check;" | tee "$OUT/sqlite_quick.txt"
sqlite3 data/runtime/vx11.db "PRAGMA busy_timeout=5000; PRAGMA integrity_check;" | tee "$OUT/sqlite_integrity.txt"
sqlite3 data/runtime/vx11.db "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON; PRAGMA foreign_key_check;" | tee "$OUT/sqlite_fk.txt"
```

12) REPORT.md

Crear `$OUT/REPORT.md` con un resumen PASS/FAIL de:
- Single-entrypoint (solo 8000 publicado)
- Health via 8000
- DB quick/integrity/foreign key checks
- Operator status via gateway (si `auth_required` => marcar como SECURE y documentar cómo probar con token)

Ejemplo mínimo para `REPORT.md`:

```text
Single-entrypoint: PASS/FAIL (ver prod_ports.txt)
Health 8000: PASS/FAIL (ver health_8000.txt)
DB quick_check: ok/fail (ver sqlite_quick.txt)
DB integrity_check: ok/fail (ver sqlite_integrity.txt)
DB foreign_key_check: ok/fail (ver sqlite_fk.txt)
Operator status via gateway: PASS (200) / SECURE (401/403 "auth_required") / FAIL (other)
```

Evidencia a guardar en `$OUT`:
- `git_pre.txt`, `ports_diff.txt`, `prod_ps.txt`, `prod_ports.txt`, `health_8000.txt`, `operator_status_via_8000.txt`, `madre_openapi_paths.txt`, `solo_madre_apply.json`, `window_open.json`, `off_by_policy_response.json`, `sqlite_quick.txt`, `sqlite_integrity.txt`, `sqlite_fk.txt`, `REPORT.md`.

Notas finales
- NO incluir tokens en commits. Use `X-VX11-Token` env var during testing. Add `X-Correlation-Id` header to all requests for traceability.
- Do not `docker compose down` automáticamente; operator will decide.
