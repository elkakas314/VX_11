# CORE_GATES_PACK

Propósito: checklist reproducible para validar el núcleo del sistema VX11 (single-entrypoint, solo_madre, policy, DB integrity).

Preparación
- Sincronizar rama `main` con ff-only (ver `docs/audit/<TS>_apply_plan/00_sync.txt`).

Comandos exactos (ejecutar desde la raíz del repo):

1) Sync ff-only
```
set -euo pipefail
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="docs/audit/${TS}_core_gates"
mkdir -p "$OUT"

echo "== SYNC =="
git checkout main
git fetch --all --prune
git pull --ff-only
```

2) Levantar solo perfil core
```
docker compose --profile core up -d --build
```

3) Health checks básicos (guardar salidas en `$OUT`)
```
curl -sS -o $OUT/tentaculo_health.json -w "%{http_code}" http://127.0.0.1:8000/health
curl -sS -o $OUT/operator_status.json -w "%{http_code}" http://127.0.0.1:8000/operator/api/v1/status || true
```

4) Verificar single-entrypoint
```
# Confirmar que sólo 8000 está publicado en producción y que frontend usa VITE_VX11_API_BASE
docker compose ps
rg -n "VITE_VX11_API_BASE|API_BASE|operator_url" -S || true
```

5) Aplicar solo_madre (si existe endpoint)
```
curl -sS -X POST http://127.0.0.1:8001/madre/power/policy/solo_madre/apply -H 'Content-Type: application/json' -d '{}' -o $OUT/solo_madre_apply.json || true
```

6) Abrir ventana TTL 120s (si existe)
```
curl -sS -X POST http://127.0.0.1:8001/madre/power/window/open -H 'Content-Type: application/json' -d '{"services":["switch"],"ttl_sec":120}' -o $OUT/window_open.json || true
sleep 2
curl -sS http://127.0.0.1:8000/operator/api/v1/some_ping_endpoint -o $OUT/ping_after_window.json || true
```

7) Confirmar OFF_BY_POLICY (servicio cerrado debe responder 403 JSON)
```
curl -sS -o $OUT/off_by_policy_response.json -w "%{http_code}" http://127.0.0.1:8000/operator/api/v1/some_restricted || true
```

8) DB sanity checks
```
sqlite3 data/runtime/vx11.db 'PRAGMA busy_timeout=5000; PRAGMA quick_check;'
sqlite3 data/runtime/vx11.db 'PRAGMA busy_timeout=5000; PRAGMA integrity_check;'
sqlite3 data/runtime/vx11.db 'PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON; PRAGMA foreign_key_check;'
```

9) Dónde pegar outputs
- `$OUT/tentaculo_health.json`
- `$OUT/operator_status.json`
- `$OUT/solo_madre_apply.json`
- `$OUT/off_by_policy_response.json`
- `$OUT/sqlite_quick_check.txt`

Evidencia: guardar todo en `docs/audit/<TS>_core_gates/`.

Notas
- Si no existen endpoints mencionados, registrar respuesta HTTP y contenido del endpoint de madre/proxy.
- No ejecutar `docker compose down` automáticamente.
