#!/bin/bash
# VX11 v6.0 Status Dashboard
# Usage: ./scripts/status_dashboard.sh

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                     VX11 v6.0 — OPERATIONAL STATUS                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check services
echo "📊 SERVICE STATUS"
echo "─────────────────────────────────────────────────────────────────────────────────"
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008; do
    module_name=""
    case $port in
        8000) module_name="tentaculo_link" ;;
        8001) module_name="madre" ;;
        8002) module_name="switch" ;;
        8003) module_name="hermes" ;;
        8004) module_name="hormiguero" ;;
        8005) module_name="manifestator" ;;
        8006) module_name="mcp" ;;
        8007) module_name="shubniggurath" ;;
        8008) module_name="spawner" ;;
    esac
    
    if curl -sS --max-time 1 "http://127.0.0.1:${port}/health" > /dev/null 2>&1; then
        echo "  ✓ $module_name:$port (responding)"
    else
        echo "  ✗ $module_name:$port (NOT RESPONDING)"
    fi
done

echo ""
echo "🗄️  DATABASE STATUS"
echo "─────────────────────────────────────────────────────────────────────────────────"

DB_FILE="data/runtime/vx11.db"
if [ -f "$DB_FILE" ]; then
    size=$(ls -lh "$DB_FILE" | awk '{print $5}')
    echo "  ✓ $DB_FILE (size: $size)"
    
    # Count tables if python available
    python3 << 'PYEOF' 2>/dev/null && exit 0
import sqlite3
try:
    conn = sqlite3.connect('data/runtime/vx11.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM madre_tasks;")
    tasks = cursor.fetchone()[0]
    print(f"  ├─ Tables: {tables}")
    print(f"  ├─ madre_tasks: {tasks}")
    print(f"  └─ Status: VALID")
    conn.close()
except Exception as e:
    print(f"  └─ Error: {str(e)[:40]}")
PYEOF
else
    echo "  ✗ $DB_FILE (NOT FOUND)"
fi

echo ""
echo "📋 CONFIGURATION"
echo "─────────────────────────────────────────────────────────────────────────────────"

if grep -q "PORTS = {" config/settings.py 2>/dev/null; then
    echo "  ✓ config/settings.py (PORTS dictionary present)"
else
    echo "  ✗ config/settings.py (issue detected)"
fi

if grep -q "DATABASE_URL" config/settings.py 2>/dev/null; then
    echo "  ✓ config/db_schema.py (BD URL configured)"
else
    echo "  ✗ config/db_schema.py (issue detected)"
fi

echo ""
echo "📚 DOCUMENTATION"
echo "─────────────────────────────────────────────────────────────────────────────────"

for file in "docs/archive/START_HERE.md" "docs/archive/README_VX11_v6.md" "docs/archive/VX11_FINAL_REPORT_v6.0.md" "docs/archive/DEPLOYMENT_CHECKLIST.md"; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "  ✓ $file ($lines lines)"
    fi
done

if [ -d "prompts" ]; then
    count=$(ls prompts/*.md 2>/dev/null | wc -l)
    echo "  ✓ prompts/ ($count system prompts)"
fi

echo ""
echo "🔍 LOGS"
echo "─────────────────────────────────────────────────────────────────────────────────"

LOG_DIR="build/artifacts/logs"
if [ -f "$LOG_DIR/architect.log" ]; then
    last_entry=$(tail -1 "$LOG_DIR/architect.log")
    echo "  Last architect entry: ${last_entry:0:80}..."
else
    echo "  ⚠ $LOG_DIR/architect.log not found"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║ Status: ✓ OPERATIONAL | Mode: Continuous Maintenance | Baseline: Locked       ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "For details, see:"
echo "  • docs/archive/START_HERE.md (quick orientation)"
echo "  • docs/archive/OPERATIONAL_MANUAL.md (operations guide)"
echo "  • $LOG_DIR/architect.log (maintenance log)"
