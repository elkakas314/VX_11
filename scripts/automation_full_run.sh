#!/usr/bin/env bash
set -euo pipefail

# Full automation pipeline:
# 1) Start common services (non-interactive)
# 2) Run checks (scripts/run_checks.sh)
# 3) Generate scorecard and final report (scripts/generate_scorecard.py)
# 4) Stop all services except madre (leave Madre ON)

TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="docs/audit/$TS"
mkdir -p "$OUT"

echo "TS=$TS" > "$OUT/automation_run.log"
echo "Starting automation run at $(date -u --iso-8601=seconds)" >> "$OUT/automation_run.log"

echo "1) Starting services..." >> "$OUT/automation_run.log"
./scripts/start_services.sh >> "$OUT/automation_run.log" 2>&1 || true

echo "Waiting 8s for services to initialize..." >> "$OUT/automation_run.log"
sleep 8

echo "2) Running checks..." >> "$OUT/automation_run.log"
./scripts/run_checks.sh >> "$OUT/automation_run.log" 2>&1 || true

echo "3) Generating scorecard..." >> "$OUT/automation_run.log"
python3 scripts/generate_scorecard.py >> "$OUT/automation_run.log" 2>&1 || true

echo "4) Stopping non-madre services..." >> "$OUT/automation_run.log"
./scripts/stop_non_madre.sh >> "$OUT/automation_run.log" 2>&1 || true

echo "Automation run complete; evidence in $OUT" >> "$OUT/automation_run.log"
echo "$OUT"
