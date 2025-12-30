# CORE_GATES_PACK v7 — Single-Entrypoint Validation

**Propósito**: Checklist reproducible para validar núcleo VX11:
- Single-Entrypoint: solo `tentaculo_link:8000` expuesto
- Solo Madre policy (si existe endpoint)
- OFF_BY_POLICY behaviour (403 JSON cuando aplicable)
- DB integrity (quick_check, integrity_check, foreign_key_check)
- Auth token management (X-VX11-Token header, NO hardcode)

---

## Preparación

```bash
set -euo pipefail
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="docs/audit/${TS}_p0_single_entrypoint"
mkdir -p "$OUT"

# Sincronizar main
git checkout main
git fetch --all --prune
git pull --ff-only
git status -sb | tee "$OUT/git_pre.txt"

# Variables de entorno (NO commitear tokens)
export VX11_TOKEN="${VX11_TOKEN:-vx11-local-token}"
export CORR_ID="core-gates-$(date -u +%s)"
```

---

## 1. Modo DEV (core)

Levantar servicios core para desarrollo/test:

```bash
docker compose --profile core up -d --build
docker compose --profile core ps | tee "$OUT/core_ps.txt"
```

---

## 2. Modo PROD — Single-Entrypoint Only

Levantar con overlay de producción (solo puerto 8000 publicado):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps | tee "$OUT/prod_ps.txt"

# Verificar puertos
docker ps --format 'table {{.Names}}\t{{.Ports}}' | tee "$OUT/prod_ports.txt"

# Validación: prod_ports.txt DEBE mostrar puerto publicado SOLO para vx11-tentaculo-link (8000)
```

---

## 3. Health Check via Single Entrypoint (8000)

```bash
curl -sS -i \
  -H "X-Correlation-Id: $CORR_ID" \
  http://127.0.0.1:8000/health \
  | tee "$OUT/health_8000.txt"

# Esperado: 200 OK, JSON con {"status":"ok","module":"tentaculo_link",...}
```

---

## 4. Operator Status via Gateway (Auth Required)

```bash
curl -sS -i \
  -H "X-VX11-Token: $VX11_TOKEN" \
  -H "X-Correlation-Id: $CORR_ID" \
  http://127.0.0.1:8000/operator/api/v1/status \
  | tee "$OUT/operator_status_via_8000.txt"

# Esperado: 200 OK (si token válido) o 401/403 Unauthorized/Forbidden (si no autorizado)
```

---

## 5. Discover Madre OpenAPI — Power/Window/Policy Paths

```bash
curl -sS http://127.0.0.1:8001/openapi.json \
  | jq '.paths|keys[]|select(test("power|window|policy"))' \
  | tee "$OUT/madre_openapi_paths.txt" \
  || echo "OpenAPI discovery failed" | tee "$OUT/madre_openapi_paths.txt"

# Esperado: lista de paths relevantes o error si endpoint no existe
```

---

## 6. Solo Madre Policy (Conditional)

Si el endpoint `/madre/power/policy/solo_madre/apply` existe:

```bash
ENDPOINT="http://127.0.0.1:8001/madre/power/policy/solo_madre/apply"
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" "$ENDPOINT")

if [[ "$HTTP_CODE" =~ ^(200|301|302|307|308|404)$ ]]; then
  # Endpoint exists (200) or 404 es válido (no existe)
  if [[ "$HTTP_CODE" == "200" ]]; then
    curl -sS -X POST "$ENDPOINT" \
      -H 'Content-Type: application/json' \
      -d '{}' \
      -H "X-Correlation-Id: $CORR_ID" \
      -o "$OUT/solo_madre_apply.json"
    echo "APPLIED" | tee "$OUT/solo_madre_status.txt"
  else
    echo "ENDPOINT_NOT_FOUND (404 or not available)" | tee "$OUT/solo_madre_status.txt"
  fi
else
  echo "ENDPOINT_ERROR_HTTP_$HTTP_CODE" | tee "$OUT/solo_madre_status.txt"
fi
```

---

## 7. Window Policy (Conditional)

Si el endpoint `/madre/power/window/open` existe:

```bash
ENDPOINT="http://127.0.0.1:8001/madre/power/window/open"
HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" "$ENDPOINT")

if [[ "$HTTP_CODE" =~ ^(200|301|302|307|308)$ ]]; then
  curl -sS -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' \
    -d '{"services":["switch"],"ttl_sec":120}' \
    -H "X-Correlation-Id: $CORR_ID" \
    -o "$OUT/window_open.json"
  sleep 2
  curl -sS -i \
    -H "X-VX11-Token: $VX11_TOKEN" \
    -H "X-Correlation-Id: $CORR_ID" \
    http://127.0.0.1:8000/operator/api/v1/status \
    | tee "$OUT/operator_status_after_window.txt"
else
  echo "WINDOW_ENDPOINT_NOT_FOUND" | tee "$OUT/window_open.json"
fi
```

---

## 8. OFF_BY_POLICY Behaviour

Probar que acceso denegado retorna 403 JSON cuando la política lo requiere:

```bash
# Intentar acceso sin token (esperado: 401/403)
curl -sS -w "\nHTTP_CODE: %{http_code}\n" \
  http://127.0.0.1:8000/operator/api/v1/status \
  | tee "$OUT/off_by_policy_response.json"

# Validar respuesta es JSON y contiene error details
if jq -e 'type=="object" and (.status? // .code? // .detail? // .message?)' "$OUT/off_by_policy_response.json" > /dev/null 2>&1; then
  echo "PASS: OFF_BY_POLICY returns JSON error" | tee "$OUT/off_by_policy_validation.txt"
else
  echo "FAIL or INCONCLUSIVE: not JSON or missing error fields" | tee "$OUT/off_by_policy_validation.txt"
fi
```

---

## 9. Database Integrity Checks

```bash
# Quick check
sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" \
  "PRAGMA quick_check;" \
  | tee "$OUT/sqlite_quick.txt"

# Full integrity check
sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" \
  "PRAGMA integrity_check;" \
  | tee "$OUT/sqlite_integrity.txt"

# Foreign key check (if constraints enabled)
sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON;" \
  "PRAGMA foreign_key_check;" \
  | tee "$OUT/sqlite_fk.txt"
```

Esperado: todas las salidas contienen `ok` o lista vacía (sin errores).

---

## 10. REPORT.md — Summary

Crear `$OUT/REPORT.md` con resultado PASS/FAIL:

```markdown
# CORE_GATES_PACK Report — [TS]

## Single-Entrypoint
- **Status**: PASS/FAIL
- **Evidence**: prod_ports.txt (solo 8000 publicado para tentaculo_link)

## Health Check (8000)
- **Status**: PASS/FAIL
- **Evidence**: health_8000.txt
- **Expected**: HTTP 200, JSON con status="ok"

## Operator Status via Gateway (auth required)
- **Status**: PASS/SECURE/FAIL
- **Evidence**: operator_status_via_8000.txt
- **Note**: Si 401/403, marcar como SECURE (auth working). Si 200, marcar como PASS. Si otro error, FAIL.

## Database Integrity
- **quick_check**: PASS/FAIL (sqlite_quick.txt)
- **integrity_check**: PASS/FAIL (sqlite_integrity.txt)
- **foreign_key_check**: PASS/FAIL (sqlite_fk.txt)

## OpenAPI Discovery (Madre)
- **Status**: DONE/NOT_AVAILABLE
- **Evidence**: madre_openapi_paths.txt

## Solo Madre Policy
- **Status**: AVAILABLE/NOT_AVAILABLE/ERROR
- **Evidence**: solo_madre_status.txt

## OFF_BY_POLICY Behaviour
- **Status**: PASS/INCONCLUSIVE
- **Evidence**: off_by_policy_validation.txt

## Auth Token Management
- **Token Source**: Environment variable VX11_TOKEN (NO hardcode)
- **Header**: X-VX11-Token: <value>
- **Correlation**: X-Correlation-Id header added to all requests

## Summary
- **Total**: N checks
- **Passed**: N/N
- **Secure (expected auth failure)**: N
- **Failed**: N/N
- **Overall**: PASS / PARTIAL / FAIL

---

**Generated**: $(date -u)
**OUTDIR**: $OUT
```

---

## 11. Token / Auth Best Practices

```bash
# Define token as env var (NEVER commit tokens)
export VX11_TOKEN="${VX11_TOKEN:-vx11-local-token}"

# Use in curl headers
curl -H "X-VX11-Token: $VX11_TOKEN" ...

# Use correlation ID for tracing
export CORR_ID="core-gates-$(date -u +%s)"
curl -H "X-Correlation-Id: $CORR_ID" ...
```

---

## 12. Finalization

```bash
# Save final git status
git status -sb | tee "$OUT/git_post.txt"
git log -5 --oneline | tee "$OUT/git_log.txt"

# List all evidence files
ls -lh "$OUT"/ | tee "$OUT/files_summary.txt"

echo "✓ CORE_GATES_PACK complete. Results in: $OUT"
```

**NOTE**: Do NOT `docker compose down` automatically. Operator decides lifecycle.

---

## Files Checklist (Evidence)

Required in `$OUT`:
- `git_pre.txt` — git status before
- `git_post.txt` — git status after
- `git_log.txt` — last 5 commits
- `prod_ps.txt` — docker compose ps (prod mode)
- `prod_ports.txt` — docker ps (verify single entrypoint)
- `health_8000.txt` — /health response
- `operator_status_via_8000.txt` — operator API with auth
- `madre_openapi_paths.txt` — OpenAPI discovery
- `solo_madre_status.txt` — solo_madre policy status
- `window_open.json` — window policy response
- `off_by_policy_response.json` — access denied scenario
- `off_by_policy_validation.json` — validation result
- `sqlite_quick.txt` — DB quick_check
- `sqlite_integrity.txt` — DB integrity_check
- `sqlite_fk.txt` — DB foreign key check
- `REPORT.md` — summary PASS/FAIL

---
