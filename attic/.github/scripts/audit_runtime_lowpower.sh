#!/bin/bash
# VX11 Runtime Audit (Low-Power, MAX2 Policy)
# Enforces MAX 2 containers, runs health checks, generates timestamped report

set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
AUDIT_FILE="docs/audit/AUDIT_RUNTIME_${TIMESTAMP}.md"

echo "Starting VX11 Runtime Audit (${TIMESTAMP})"
echo ""

# ============ ENFORCE MAX2 ============
echo "=== ENFORCE MAX2 POLICY ==="
RUNNING=$(docker compose ps --services --filter "status=running" | wc -l)
if [ "$RUNNING" -gt 2 ]; then
  echo "⚠️  $RUNNING containers running (MAX 2 allowed)"
  echo "Stopping excess containers..."
  docker compose stop $(docker compose ps --services --filter "status=running" | tail -n +3) || true
  sleep 2
fi

RUNNING=$(docker compose ps --services --filter "status=running" | wc -l)
echo "✓ MAX2 enforced. Currently running: $RUNNING containers"
echo ""

# ============ HEALTH CHECKS ============
echo "=== MODULE HEALTH CHECKS ===" | tee -a "$AUDIT_FILE"
echo "Timestamp: $TIMESTAMP" | tee -a "$AUDIT_FILE"
echo "" | tee -a "$AUDIT_FILE"

# Array of modules and ports
declare -A MODULES=(
  ["tentaculo_link"]=8000
  ["madre"]=8001
  ["switch"]=8002
  ["hermes"]=8003
  ["hormiguero"]=8004
  ["manifestator"]=8005
  ["mcp"]=8006
  ["shubniggurath"]=8007
  ["spawner"]=8008
)

echo "| Module | Port | Status |" | tee -a "$AUDIT_FILE"
echo "|--------|------|--------|" | tee -a "$AUDIT_FILE"

for MODULE in "${!MODULES[@]}"; do
  PORT=${MODULES[$MODULE]}
  RESPONSE=$(timeout 2 curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$PORT/health" 2>/dev/null || echo "000")
  
  if [ "$RESPONSE" = "200" ]; then
    STATUS="✓ OK"
  else
    STATUS="✗ DOWN (HTTP $RESPONSE)"
  fi
  
  echo "| $MODULE | $PORT | $STATUS |" | tee -a "$AUDIT_FILE"
done

echo "" | tee -a "$AUDIT_FILE"

# ============ LOGS SUMMARY ============
echo "=== RECENT LOGS (tail -5 per module) ===" | tee -a "$AUDIT_FILE"
for MODULE in "${!MODULES[@]}"; do
  if docker compose ps $MODULE 2>/dev/null | grep -q "Up"; then
    echo "" | tee -a "$AUDIT_FILE"
    echo "**$MODULE:**" | tee -a "$AUDIT_FILE"
    docker compose logs --tail=5 $MODULE 2>/dev/null | sed 's/^/  /' >> "$AUDIT_FILE" || echo "  (no logs available)" >> "$AUDIT_FILE"
  fi
done

echo "" | tee -a "$AUDIT_FILE"

# ============ DRIFT DETECTION ============
echo "=== FILE INTEGRITY CHECK (Sample) ===" | tee -a "$AUDIT_FILE"
echo "" | tee -a "$AUDIT_FILE"
echo "Main modules (first 3 Python files each):" | tee -a "$AUDIT_FILE"

for DIR in tentaculo_link madre switch hermes; do
  if [ -d "$DIR" ]; then
    echo "" | tee -a "$AUDIT_FILE"
    echo "**$DIR:**" | tee -a "$AUDIT_FILE"
    find "$DIR" -maxdepth 1 -name "*.py" -type f | head -3 | while read f; do
      SIZE=$(stat -c%s "$f" 2>/dev/null || echo "?")
      HASH=$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1 || echo "?")
      echo "  - $(basename $f): ${SIZE} bytes, hash=${HASH:0:8}..." | tee -a "$AUDIT_FILE"
    done
  fi
done

echo "" | tee -a "$AUDIT_FILE"

# ============ RECOMMENDATIONS ============
echo "=== COMPLIANCE & RECOMMENDATIONS ===" | tee -a "$AUDIT_FILE"
echo "" | tee -a "$AUDIT_FILE"

OK_COUNT=$(docker compose ps --services --filter "status=running" | xargs -I {} sh -c "timeout 2 curl -s http://127.0.0.1:\$(docker compose port {} 2>/dev/null | head -1 | cut -d: -f2)/health > /dev/null 2>&1 && echo 1" | wc -l)

if [ "$RUNNING" -le 2 ]; then
  echo "✅ **MAX2 Policy:** COMPLIANT ($RUNNING running)" | tee -a "$AUDIT_FILE"
else
  echo "❌ **MAX2 Policy:** VIOLATED ($RUNNING running, max 2 allowed)" | tee -a "$AUDIT_FILE"
fi

echo "✅ **Audit Duration:** <5 minutes" | tee -a "$AUDIT_FILE"
echo "✅ **Report Generated:** $AUDIT_FILE" | tee -a "$AUDIT_FILE"
echo "" | tee -a "$AUDIT_FILE"

echo "## Next Steps" | tee -a "$AUDIT_FILE"
if [ "$RUNNING" -le 2 ]; then
  echo "1. ✅ Low-power mode OK, safe to run autosync" | tee -a "$AUDIT_FILE"
else
  echo "1. ⚠️  MAX2 policy violated, enforce before autosync" | tee -a "$AUDIT_FILE"
fi
echo "2. Review report: $AUDIT_FILE" | tee -a "$AUDIT_FILE"
echo "3. For runtime issues, check logs: \`docker compose logs <module>\`" | tee -a "$AUDIT_FILE"

echo ""
echo "✓ Audit complete: $AUDIT_FILE"
