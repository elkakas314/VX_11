#!/bin/bash

###############################################################################
# PROMPT C: Operator UI Visibility Diagnostic & Fix Checklist
# Purpose: Quick troubleshooting when /operator/ui/ is not visible
# Usage: ./operator_ui_visibility_diagnostic.sh
###############################################################################

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIT_DIR="docs/audit/OPERATOR_UI_VISIBILITY_DIAGNOSTIC_${TIMESTAMP}"
mkdir -p "$AUDIT_DIR"

echo "=========================================="
echo "PROMPT C: UI VISIBILITY DIAGNOSTIC"
echo "=========================================="
echo ""
echo "📁 Audit Dir: $AUDIT_DIR"
echo ""

# ============= STEP 1: CHECK VITE CONFIG =============
echo "STEP 1️⃣ : Check Vite Configuration"
echo "---"

VITE_CONFIG="operator/frontend/vite.config.ts"
if [ ! -f "$VITE_CONFIG" ]; then
    echo "❌ FAIL: $VITE_CONFIG not found"
    exit 1
fi

echo "Checking: $VITE_CONFIG"
if grep -qE "base:\s+['\"]\/operator\/ui\/['\"]" "$VITE_CONFIG"; then
    echo "✅ PASS: base: \"/operator/ui/\" (or '/operator/ui/') found"
else
    echo "❌ FAIL: base: \"/operator/ui/\" NOT found"
    echo "   Fix: Add 'base: \"/operator/ui/\"' to vite.config.ts export"
    exit 1
fi

grep -E "base:" "$VITE_CONFIG" | head -1 | tee -a "$AUDIT_DIR/vite_config_check.txt"
echo ""

# ============= STEP 2: CHECK BUILD =============
echo "STEP 2️⃣ : Check Frontend Build"
echo "---"

if [ ! -d "operator/frontend/dist" ]; then
    echo "⚠️  WARNING: operator/frontend/dist not found"
    echo "   Running: npm run build..."
    cd operator/frontend
    npm ci && npm run build
    cd ../../
fi

DIST_SIZE=$(du -sh operator/frontend/dist 2>/dev/null | cut -f1)
DIST_FILES=$(find operator/frontend/dist -type f | wc -l)
echo "✅ dist/ exists: $DIST_SIZE ($DIST_FILES files)"
echo "Dist details:" >> "$AUDIT_DIR/build_check.txt"
ls -lh operator/frontend/dist/ | head -10 >> "$AUDIT_DIR/build_check.txt"
echo ""

# ============= STEP 3: CHECK TENTACULO_LINK MOUNT =============
echo "STEP 3️⃣ : Check StaticFiles Mount in tentaculo_link/main_v7.py"
echo "---"

MAIN_FILE="tentaculo_link/main_v7.py"
if [ ! -f "$MAIN_FILE" ]; then
    echo "❌ FAIL: $MAIN_FILE not found"
    exit 1
fi

if grep -q 'app.mount' "$MAIN_FILE" && grep -q 'operator/ui' "$MAIN_FILE" && grep -q 'StaticFiles' "$MAIN_FILE"; then
    echo "✅ PASS: StaticFiles mount for /operator/ui found"
    grep -n 'app.mount' "$MAIN_FILE" -A 3 | head -6 | tee -a "$AUDIT_DIR/mount_check.txt"
else
    echo "❌ FAIL: StaticFiles mount NOT found"
    echo "   Fix: Add mount in tentaculo_link/main_v7.py:"
    echo '   app.mount("/operator/ui", StaticFiles(directory=...), name="operator_ui")'
    exit 1
fi
echo ""

# ============= STEP 4: CHECK TENTACULO_LINK RUNNING =============
echo "STEP 4️⃣ : Check tentaculo_link Service Health"
echo "---"

TENTACULO_URL="http://localhost:8000"
if curl -s "${TENTACULO_URL}/health" > /dev/null 2>&1; then
    echo "✅ PASS: tentaculo_link:8000 responding"
    curl -s "${TENTACULO_URL}/health" | jq . 2>/dev/null || curl -s "${TENTACULO_URL}/health"
else
    echo "❌ FAIL: tentaculo_link:8000 NOT responding"
    echo "   Fix: Start services with: docker-compose up -d"
    exit 1
fi
echo ""

# ============= STEP 5: CHECK /operator/ui/ SERVING =============
echo "STEP 5️⃣ : Test /operator/ui/ Endpoint"
echo "---"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TENTACULO_URL}/operator/ui/")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS: GET /operator/ui/ → 200 OK"
    curl -I "${TENTACULO_URL}/operator/ui/" 2>&1 | head -10 | tee -a "$AUDIT_DIR/endpoint_check.txt"
else
    echo "❌ FAIL: GET /operator/ui/ → HTTP $HTTP_CODE (expected 200)"
    echo "   Debug:"
    curl -I "${TENTACULO_URL}/operator/ui/" 2>&1 | tee -a "$AUDIT_DIR/endpoint_check.txt"
    exit 1
fi
echo ""

# ============= STEP 6: CHECK ASSETS =============
echo "STEP 6️⃣ : Test Static Assets"
echo "---"

CSS_FILE=$(curl -s "${TENTACULO_URL}/operator/ui/" 2>/dev/null | grep -oP 'index-[a-zA-Z0-9]+\.css' | head -1)
if [ -n "$CSS_FILE" ]; then
    echo "Found CSS: $CSS_FILE"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${TENTACULO_URL}/operator/ui/assets/${CSS_FILE}")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ PASS: CSS asset → 200"
    else
        echo "⚠️  WARN: CSS asset → HTTP $HTTP_CODE"
    fi
else
    echo "⚠️  WARN: Could not find CSS file reference in HTML"
fi
echo ""

# ============= STEP 7: DEV MODE OPTION =============
echo "STEP 7️⃣ : Option: Run Dev Server (DEV mode)"
echo "---"
echo "If you want to test with hot-reload:"
echo ""
echo "  cd operator/frontend"
echo "  npm run dev -- --host 0.0.0.0 --port 5173"
echo ""
echo "Then open: http://localhost:5173/operator/ui/"
echo ""

# ============= FINAL SUMMARY =============
echo "=========================================="
echo "✅ ALL CHECKS PASSED"
echo "=========================================="
echo ""
echo "UI should be visible at:"
echo "  → http://localhost:8000/operator/ui/"
echo ""
echo "Audit evidence saved to: $AUDIT_DIR/"
echo ""
echo "Quick verification commands:"
echo "  curl -s http://localhost:8000/operator/ui/ | head -5"
echo "  curl -I http://localhost:8000/operator/ui/"
echo ""
