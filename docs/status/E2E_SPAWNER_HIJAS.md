# E2E Spawner "Hijas" Test — 2026-01-03

## Objetivo
Verificar que spawner puede crear, registrar y limpiar procesos "hija" (daughter processes) con TTL corto.

## Endpoints Reales (Via tentaculo_link:8000)

Basado en auditoría del código:

```
GET  /operator/api/spawner/status   — Lee estado de spawner
GET  /operator/api/spawner/runs     — Lista runs activos + histórico
POST /operator/api/spawner/submit   — Crea nueva run (Madre-gated en solo_madre)
```

**Auth**: Token via header `X-VX11-Token: vx11-test-token`

---

## Prueba E2E: Crear Hija + TTL + Verificar + Limpiar

### Paso 1: Verificar Spawner Status

```bash
curl -s -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/spawner/status | jq .
```

**Expected Output**:
```json
{
  "status": "running",
  "capacity": 5,
  "active_runs": 0,
  "pending_runs": 0
}
```

---

### Paso 2: Crear Hija con TTL Corto (10 segundos)

```bash
curl -s -X POST -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  http://localhost:8000/operator/api/spawner/submit \
  -d '{
    "task_type": "test_daughter",
    "payload": {
      "ttl_sec": 10,
      "reason": "e2e_test_20260103",
      "name": "e2e-test-hija-1"
    }
  }' | jq .
```

**Expected Output**:
```json
{
  "run_id": "<UUID>",
  "status": "created",
  "submitted_at": "2026-01-03T...",
  "ttl_sec": 10
}
```

**Guardar run_id** para pasos posteriores.

---

### Paso 3: Verificar Registro en BD (dentro de 1 segundo)

```bash
# Conectar a DB y verificar registro
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db << EOF
SELECT id, status, created_at, expires_at FROM spawner_runs 
  WHERE id LIKE '<run_id_prefix>%' 
  ORDER BY created_at DESC LIMIT 1;
EOF
```

**Expected**: Fila con `status='created'` y `expires_at = NOW + 10s`

---

### Paso 4: Listar Runs (Debe Aparecer la Hija)

```bash
curl -s -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/spawner/runs | jq '.runs[] | select(.name == "e2e-test-hija-1")'
```

**Expected**: Object con `run_id`, `status`, `created_at`, `expires_at`

---

### Paso 5: Esperar 11 Segundos (TTL expira)

```bash
sleep 11
echo "TTL expired, checking cleanup..."
```

---

### Paso 6: Verificar Limpieza (DB o /spawner/runs)

```bash
curl -s -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/spawner/runs | jq '.runs[] | select(.name == "e2e-test-hija-1")'

# Si no aparece o status='expired', limpieza OK
```

```bash
# Alternativa: Verificar DB
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db \
  "SELECT status FROM spawner_runs WHERE id LIKE '<run_id_prefix>%' LIMIT 1;"
# Expected: expired | completed (not 'created')
```

---

## Resultados Esperados

✅ **PASS**:
1. Spawner responde a status request
2. Hija se crea con run_id único
3. BD registra hija en tabla spawner_runs
4. Después de 11s, hija está marcada como 'expired' o limpiada
5. Runs list ya no muestra hija activa (o la marca como historical)

❌ **FAIL**:
- Spawner no responde (403, 500)
- Hija no se registra en BD
- TTL no se respeta (hija sigue "active" después de 11s)
- Limpieza no se ejecuta

---

## Notas

- En `solo_madre` mode, spawner.submit puede estar gated (requiere ventana temporal)
- Si ve 403 en submit, abra ventana temporal: `POST /madre/power/window/open {"services": ["spawner"]}`
- TTL es recomendation; acción real depende de timer background en spawner service

## Token de Prueba

```
vx11-test-token
```

## Comandos Rápidos (Copiar-Pegar)

```bash
# 1. Status
curl -s -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/spawner/status | jq .

# 2. Create (guarda run_id)
RUN_ID=$(curl -s -X POST -H "X-VX11-Token: vx11-test-token" -H "Content-Type: application/json" \
  http://localhost:8000/operator/api/spawner/submit \
  -d '{"task_type":"test","payload":{"ttl_sec":10,"name":"e2e-test"}}' | jq -r '.run_id')
echo "Created run: $RUN_ID"

# 3. List runs
curl -s -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/spawner/runs | jq '.runs | length'

# 4. Wait + cleanup check
sleep 11 && curl -s -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/spawner/runs | jq '.runs | map(select(.run_id == "'$RUN_ID'")) | length'
# Expected: 0 (cleaned)
```

