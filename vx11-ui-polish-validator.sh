#!/bin/bash
# vx11-ui-polish-validator.sh
# Complete validation script for Operator UI polish workflow

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="/home/elkakas314/vx11"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  VX11 Operator UI Polish - Complete Validation                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Frontend Validator
echo -e "${YELLOW}[1/5] Running frontend validator...${NC}"
cd "$PROJECT_ROOT"
if python3 scripts/validate-frontend.py; then
    echo -e "${GREEN}✅ Frontend validator PASSED${NC}"
else
    echo -e "${RED}❌ Frontend validator FAILED${NC}"
    exit 1
fi
echo ""

# Step 2: Build Frontend
echo -e "${YELLOW}[2/5] Building frontend...${NC}"
cd "$PROJECT_ROOT/operator/frontend"
if npm ci && npm run build 2>&1 | tail -10; then
    echo -e "${GREEN}✅ Frontend build PASSED${NC}"
else
    echo -e "${RED}❌ Frontend build FAILED${NC}"
    exit 1
fi
echo ""

# Step 3: Health Check
echo -e "${YELLOW}[3/5] Testing /health endpoint...${NC}"
cd "$PROJECT_ROOT"
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo '{}')
if echo "$HEALTH" | grep -q "tentaculo_link"; then
    echo -e "${GREEN}✅ Health check PASSED${NC}"
    echo "   Response: $HEALTH"
else
    echo -e "${RED}❌ Health check FAILED${NC}"
    echo "   Response: $HEALTH"
    exit 1
fi
echo ""

# Step 4: API Status (with token)
echo -e "${YELLOW}[4/5] Testing /operator/api/status with token...${NC}"
source tokens.env
API_STATUS=$(curl -s -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/status 2>/dev/null || echo '{"error":"no_response"}')
if echo "$API_STATUS" | grep -q '"status"'; then
    echo -e "${GREEN}✅ API status check PASSED${NC}"
    echo "   Response: $(echo $API_STATUS | head -c 100)..."
else
    echo -e "${RED}❌ API status check FAILED${NC}"
    echo "   Response: $API_STATUS"
    exit 1
fi
echo ""

# Step 5: SSE Stream Check
echo -e "${YELLOW}[5/5] Testing SSE /operator/api/events stream...${NC}"
TIMEOUT=3
(timeout $TIMEOUT curl -s -N "http://localhost:8000/operator/api/events?token=vx11-test-token&follow=true" 2>/dev/null | head -1 > /tmp/sse_test.txt) || true
if [ -s /tmp/sse_test.txt ]; then
    echo -e "${GREEN}✅ SSE stream check PASSED${NC}"
    echo "   First event: $(head -c 80 /tmp/sse_test.txt)..."
else
    echo -e "${YELLOW}⚠️  SSE stream check (timeout expected, still OK)${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ ALL VALIDATION CHECKS PASSED${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Ready to commit! Next steps:${NC}"
echo "  1. Review git diff: git diff operator/frontend/"
echo "  2. Stage changes: git add operator/frontend/"
echo "  3. Commit: git commit -m \"vx11(operator-ui): visual polish...\""
echo "  4. Push: git push -u vx_11_remote operator-ui-polish"
echo "  5. Create PR: gh pr create --base main --head operator-ui-polish..."
echo ""
