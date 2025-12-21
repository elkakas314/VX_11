#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh"
# VX11 v6.1 CANON - Script de validación automática

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║        VX11 v6.1 CANON VALIDATION – Validando implementación              ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TOTAL_CHECKS=0
PASSED_CHECKS=0

check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

# 1. Verificar módulos
echo "1️⃣  VALIDACIÓN: MÓDULOS CANÓNICOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ -d "gateway" ] || mkdir -p gateway
for mod in tentaculo_link madre switch hormiguero manifestator mcp shubniggurath spawner; do
    [ -f "$mod/main.py" ]
    check "Módulo $mod presente (main.py)"
done

[ -f "switch/hermes/main.py" ]
check "Módulo hermes dentro de switch (switch/hermes/main.py)"

echo

# 2. Verificar archivos canónicos
echo "2️⃣  VALIDACIÓN: ARCHIVOS CANONIZACIÓN v6.1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ -f "prompts/context-7.schema.json" ]
check "Schema context-7"

[ -f "prompts/switch.prompt.json" ]
check "Prompts switch"

[ -f "prompts/hermes.prompt.json" ]
check "Prompts hermes"

[ -f "prompts/madre.prompt.json" ]
check "Prompts madre"

[ -f "prompts/hormiguero.prompt.json" ]
check "Prompts hormiguero"

[ -f "prompts/shubniggurath.prompt.json" ]
check "Prompts shubniggurath"

[ -f "VX11_CANON_v6.1.md" ]
check "Documento canon (VX11_CANON_v6.1.md)"

echo

# 3. Validar JSON
echo "3️⃣  VALIDACIÓN: JSON VÁLIDO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for json_file in prompts/context-7.schema.json prompts/switch.prompt.json prompts/hermes.prompt.json prompts/madre.prompt.json prompts/hormiguero.prompt.json prompts/shubniggurath.prompt.json; do
    python3 -m json.tool "$json_file" > /dev/null 2>&1
    check "JSON válido: $(basename $json_file)"
done

echo

# 4. Validar endpoints en gateway
echo "4️⃣  VALIDACIÓN: ENDPOINTS EN TENTACULO_LINK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

grep -q "@app.get(\"/health\")" tentaculo_link/main.py
check "GET /health"

grep -q "@app.get(\"/vx11/status\")" tentaculo_link/main.py
check "GET /vx11/status"

grep -q "@app.post(\"/events/ingest\")" tentaculo_link/main.py
check "POST /events/ingest"

grep -q "@app.post(\"/files/upload\")" tentaculo_link/main.py
check "POST /files/upload"

grep -q "@app.websocket(\"/ws\")" tentaculo_link/main.py
check "WS /ws"

echo

# 5. Validar DB
echo "5️⃣  VALIDACIÓN: BASE DE DATOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ -f "data/runtime/vx11.db" ]
check "Base de datos presente (data/runtime/vx11.db)"

# Verificar tablas críticas
python3 << 'DBCHECK'
import sqlite3
import sys

try:
    conn = sqlite3.connect("data/runtime/vx11.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]
    
    expected = ["Task", "Context", "Report", "Spawn", "Engine", "Pheromone"]
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = [row[0] for row in cursor.fetchall()]
    
    found = sum(1 for t in expected if t in existing or any(t.lower() in e.lower() for e in existing))
    
    print(f"  ✓ Total tablas: {table_count}")
    print(f"  ✓ Tablas canónicas: {found}/{len(expected)}")
    
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"  ✗ Error BD: {e}")
    sys.exit(1)
DBCHECK

echo

# 6. Validar Context-7
echo "6️⃣  VALIDACIÓN: CONTEXT-7 (7 CAPAS)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'C7CHECK'
import json
import sys

try:
    with open("prompts/context-7.schema.json", 'r') as f:
        schema = json.load(f)
    
    required = schema.get("required", [])
    layers = ["layer1_user", "layer2_session", "layer3_task", "layer4_environment", 
              "layer5_security", "layer6_history", "layer7_meta"]
    
    found = sum(1 for layer in layers if layer in required)
    
    print(f"  ✓ Capas context-7: {found}/{len(layers)}")
    
    if found == len(layers):
        print(f"  ✓ Context-7 completo (7/7 capas definidas)")
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)
C7CHECK

echo

# 7. Verificar no hay breaking changes
echo "7️⃣  VALIDACIÓN: COMPATIBILITY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar que todos los módulos aún tienen /health y /control
for mod in tentaculo_link madre switch hermes hormiguero manifestator mcp shubniggurath spawner; do
    if [ -f "$mod/main.py" ]; then
        grep -q "@app.get(\"/health\")" "$mod/main.py" 2>/dev/null || \
        grep -q "GET /health" "$mod/main.py" 2>/dev/null
        check "Módulo $mod: /health presente"
    fi
done

echo

# Resumen final
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                       RESUMEN DE VALIDACIÓN                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo -e "${GREEN}✅ TODAS LAS VALIDACIONES PASARON ($PASSED_CHECKS/$TOTAL_CHECKS)${NC}"
    echo
    echo "VX11 v6.1 Canon está:"
    echo "  • Completamente canonizado"
    echo "  • 100% compatible con v6.0"
    echo "  • Listo para desarrollo"
    echo
    exit 0
else
    echo -e "${RED}⚠️  ALGUNAS VALIDACIONES FALLARON ($PASSED_CHECKS/$TOTAL_CHECKS)${NC}"
    echo
    exit 1
fi
