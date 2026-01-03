#!/bin/bash
set -euo pipefail

# FASE 0.5: FORENSIC + CANONICAL + CONTRACTS
# Objetivo: capturar foto canónica antes de tocar código

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIT_DIR="docs/audit/fase_0_5_${TIMESTAMP}"
STATUS_DIR="docs/status"
mkdir -p "$AUDIT_DIR" "$STATUS_DIR"

echo "════════════════════════════════════════════════════════════"
echo "  FASE 0.5: FORENSIC + CANONICAL + CONTRACTS"
echo "  TS: $TIMESTAMP"
echo "════════════════════════════════════════════════════════════"

# ─────────────────────────────────────────────────────────────
# 0.5.A Detectar compose real y fijar variables base
# ─────────────────────────────────────────────────────────────
echo ""
echo "=== 0.5.A: DETECTAR COMPOSE + PATHS ==="

COMPOSE=""
for f in docker-compose.full-test.yml docker-compose.full-test.yaml docker-compose.yml; do
  if [ -f "$f" ]; then
    COMPOSE="$f"
    echo "✅ Found: $COMPOSE"
    break
  fi
done

if [ -z "$COMPOSE" ]; then
  echo "❌ FAIL: No docker-compose*.yml found"
  ls -la
  exit 1
fi

# Token test: detect from env, not invent
TOKEN_TEST="${VX11_TEST_TOKEN:-}"
if [ -z "$TOKEN_TEST" ] && [ -f ".env" ]; then
  TOKEN_TEST=$(grep -E '^VX11_.*TOKEN=' .env 2>/dev/null | head -1 | cut -d= -f2- || true)
fi

if [ -z "$TOKEN_TEST" ]; then
  echo "⚠️  WARN: VX11_TEST_TOKEN not found in .env"
  echo "   Using fallback: vx11-test-token"
  TOKEN_TEST="vx11-test-token"
fi

echo "✅ TOKEN_TEST: $TOKEN_TEST"

# Detecta backend main.py (path autodetection)
BACKEND_PATHS=(
  "operator/backend/main.py"
  "operator_backend/app/main.py"
  "operator_backend/main.py"
  "backend/main.py"
)
BACKEND_MAIN=""
for p in "${BACKEND_PATHS[@]}"; do
  if [ -f "$p" ]; then
    BACKEND_MAIN="$p"
    echo "✅ BACKEND_MAIN: $BACKEND_MAIN"
    break
  fi
done

if [ -z "$BACKEND_MAIN" ]; then
  echo "⚠️  WARN: No backend/main.py found (expected paths: ${BACKEND_PATHS[*]})"
fi

# Detecta tentaculo_link main
TENTACULO_PATHS=(
  "tentaculo_link/main_v7.py"
  "tentaculo_link/main.py"
)
TENTACULO_MAIN=""
for p in "${TENTACULO_PATHS[@]}"; do
  if [ -f "$p" ]; then
    TENTACULO_MAIN="$p"
    echo "✅ TENTACULO_MAIN: $TENTACULO_MAIN"
    break
  fi
done

# ─────────────────────────────────────────────────────────────
# 0.5.B Renderizar compose y verificar entrypoint único
# ─────────────────────────────────────────────────────────────
echo ""
echo "=== 0.5.B: ENTRYPOINT DETECTION ==="

docker compose -f "$COMPOSE" config > "$AUDIT_DIR/COMPOSE_RENDERED.yml" 2>&1 || {
  echo "❌ FAIL: docker compose config failed"
  exit 1
}

echo "✅ Compose rendered to: $AUDIT_DIR/COMPOSE_RENDERED.yml"

# Verificar puertos: solo 8000 debe estar público
echo ""
echo "Port mapping (expect 8000 only public):"
grep -A 50 "services:" "$AUDIT_DIR/COMPOSE_RENDERED.yml" | grep -E "ports:|- \"" | head -20 || true

# ─────────────────────────────────────────────────────────────
# 0.5.C Esperar servicios y capturar OpenAPI / Contracts
# ─────────────────────────────────────────────────────────────
echo ""
echo "=== 0.5.C: OPENAPI BASELINE ==="

# Start servicios si no están ya corriendo
echo "Checking if services are running..."
if ! docker compose -f "$COMPOSE" ps | grep -q "Up"; then
  echo "⚠️  Services not running; attempting docker compose up..."
  docker compose -f "$COMPOSE" up -d --timeout 10 2>&1 || true
fi

# Espera tentaculo_link (max 15s)
for i in {1..30}; do
  if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ tentaculo_link ready on http://localhost:8000"
    break
  fi
  echo "  Waiting... ($i/30)"
  sleep 0.5
done

# Captura OpenAPI si existe
echo ""
echo "Attempting OpenAPI capture:"
curl -sS "http://localhost:8000/openapi.json" \
  -o "$AUDIT_DIR/OPENAPI_tentaculo_link.json" 2>/dev/null && \
  echo "✅ Saved: OPENAPI_tentaculo_link.json" || \
  echo "⚠️  No OpenAPI at http://localhost:8000/openapi.json"

curl -sS -H "X-VX11-Token: $TOKEN_TEST" "http://localhost:8000/operator/api/openapi.json" \
  -o "$AUDIT_DIR/OPENAPI_operator.json" 2>/dev/null && \
  echo "✅ Saved: OPENAPI_operator.json" || \
  echo "⚠️  No OpenAPI at operator endpoint"

# Contratos: detect pytest
echo ""
echo "Contract tests:"
if [ -f "pyproject.toml" ] || [ -f "pytest.ini" ] || [ -d "tests/" ]; then
  echo "Running pytest baseline..."
  (cd /home/elkakas314/vx11 && python3 -m pytest -q --disable-warnings --maxfail=1 2>&1 || true) | tee "$AUDIT_DIR/PYTEST_BASELINE.txt" || true
  (cd /home/elkakas314/vx11 && python3 -m pytest -q -k "contract" 2>&1 || true) | tee "$AUDIT_DIR/PYTEST_CONTRACTS.txt" || true
else
  echo "⚠️  No pytest found (no pyproject.toml, pytest.ini, or tests/ dir)"
fi

# ─────────────────────────────────────────────────────────────
# 0.5.D Forensic DB (SQLite-first)
# ─────────────────────────────────────────────────────────────
echo ""
echo "=== 0.5.D: DATABASE FORENSIC ==="

DB_PATH="data/runtime/vx11.db"
if [ -f "$DB_PATH" ]; then
  echo "✅ Found SQLite: $DB_PATH"
  echo ""
  echo "PRAGMA quick_check:"
  sqlite3 "$DB_PATH" "PRAGMA quick_check;" | tee "$AUDIT_DIR/DB_quick_check.txt"
  
  echo ""
  echo "PRAGMA integrity_check:"
  sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | tee "$AUDIT_DIR/DB_integrity_check.txt"
  
  echo ""
  echo "Table count:"
  sqlite3 "$DB_PATH" "SELECT count(*) AS tables FROM sqlite_master WHERE type='table';" | tee "$AUDIT_DIR/DB_table_count.txt"
  
  echo ""
  echo "File stat:"
  ls -lh "$DB_PATH" | tee "$AUDIT_DIR/DB_file_stat.txt"
else
  echo "⚠️  No SQLite DB found at $DB_PATH"
fi

# ─────────────────────────────────────────────────────────────
# 0.5.E Hashes + Baseline Logs
# ─────────────────────────────────────────────────────────────
echo ""
echo "=== 0.5.E: HASHING CORE FILES ==="

# Compose hash
echo "Compose file hash:"
sha256sum "$COMPOSE" 2>/dev/null | tee "$AUDIT_DIR/HASH_compose.txt" || true

# Backend hash
echo ""
echo "Backend main hash:"
if [ -n "$BACKEND_MAIN" ]; then
  sha256sum "$BACKEND_MAIN" | tee "$AUDIT_DIR/HASH_backend_main.txt"
else
  echo "⚠️  BACKEND_MAIN not found, skipping hash"
fi

# Tentaculo hash
echo ""
echo "Tentaculo main hash:"
if [ -n "$TENTACULO_MAIN" ]; then
  sha256sum "$TENTACULO_MAIN" | tee "$AUDIT_DIR/HASH_tentaculo_main.txt"
else
  echo "⚠️  TENTACULO_MAIN not found, skipping hash"
fi

# ─────────────────────────────────────────────────────────────
# 0.5.F Service Logs Baseline
# ─────────────────────────────────────────────────────────────
echo ""
echo "=== 0.5.F: SERVICE LOGS BASELINE ==="

docker compose -f "$COMPOSE" ps | tee "$STATUS_DIR/PS_BASELINE_${TIMESTAMP}.txt"

echo ""
echo "All services logs (last 50 lines):"
docker compose -f "$COMPOSE" logs --tail 50 2>&1 | tee "$AUDIT_DIR/LOGS_all_services_${TIMESTAMP}.txt" || true

echo ""
echo "Tentaculo logs (last 20 lines):"
docker compose -f "$COMPOSE" logs --tail 20 tentaculo-link 2>&1 | tee "$AUDIT_DIR/LOGS_tentaculo_link_${TIMESTAMP}.txt" || true

echo ""
echo "Operator backend logs (last 20 lines):"
docker compose -f "$COMPOSE" logs --tail 20 operator-backend 2>&1 | tee "$AUDIT_DIR/LOGS_operator_backend_${TIMESTAMP}.txt" || true

# ─────────────────────────────────────────────────────────────
# 0.5.G Summary
# ─────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ FASE 0.5 COMPLETE"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Evidencia guardada en:"
echo "  $AUDIT_DIR"
echo ""
echo "Archivos generados:"
ls -lh "$AUDIT_DIR" | tail -20

echo ""
echo "Configuración detectada:"
echo "  COMPOSE: $COMPOSE"
echo "  TOKEN_TEST: $TOKEN_TEST"
echo "  BACKEND_MAIN: ${BACKEND_MAIN:-NOT FOUND}"
echo "  TENTACULO_MAIN: ${TENTACULO_MAIN:-NOT FOUND}"
echo ""

# Guardar variables en archivo para siguiente fase
cat > "$AUDIT_DIR/VARS.env" <<VARS_EOF
COMPOSE=$COMPOSE
TOKEN_TEST=$TOKEN_TEST
BACKEND_MAIN=$BACKEND_MAIN
TENTACULO_MAIN=$TENTACULO_MAIN
AUDIT_DIR=$AUDIT_DIR
STATUS_DIR=$STATUS_DIR
TIMESTAMP=$TIMESTAMP
VARS_EOF

echo "✅ Variables saved to: $AUDIT_DIR/VARS.env"
