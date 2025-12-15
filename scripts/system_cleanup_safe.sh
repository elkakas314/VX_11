#!/usr/bin/env bash
# scripts/system_cleanup_safe.sh
# Safe system cleanup script for VX11 (dry-run by default)
# - DRY-RUN default: shows actions without executing
# - To actually apply, set APPLY=1 (NOT recommended without review)

set -euo pipefail
APPLY=${APPLY:-0}
LOG_DIR="logs"
LOG_DIR_DEFAULT="logs/system_cleanup_actions.log"
mkdir -p "$LOG_DIR"
LOG=${LOG:-$LOG_DIR_DEFAULT}

echo "System cleanup safe script started: $(date -u)" | tee -a "$LOG"

echo "\n-- Zombies detected (dry-run) --" | tee -a "$LOG"
ZOMBIES=$(ps -eo pid,ppid,stat,user,comm,args | awk '$3 ~ /Z/ {print $1":"$2":"$4":"$5":"substr($0, index($0,$6)) }')
if [ -z "$ZOMBIES" ]; then
  echo "No zombies found" | tee -a "$LOG"
else
  echo "$ZOMBIES" | tee -a "$LOG"
  while IFS= read -r line; do
    IFS=":" read -r pid ppid user comm args <<<"$line"
    echo "Found zombie PID=$pid PPID=$ppid USER=$user CMD=$comm $args" | tee -a "$LOG"
    if [ "$APPLY" -eq 1 ]; then
      echo "Terminar proceso zombie PID=$pid (SIGTERM)" | tee -a "$LOG"
      kill -TERM "$pid" || true
      sleep 2
      if ps -p "$pid" > /dev/null; then
        echo "PID $pid still alive; sending SIGKILL" | tee -a "$LOG"
        kill -KILL "$pid" || true
      fi
    else
      echo "DRY-RUN: would terminate PID=$pid (no action taken)" | tee -a "$LOG"
    fi
  done <<< "$ZOMBIES"
fi

# Python/uvicorn orphan detection
echo "\n-- Python/uvicorn processes (candidates) --" | tee -a "$LOG"
ps -eo pid,ppid,stat,user,comm,args | egrep 'python|uvicorn' | egrep -v 'grep' | while read -r pid ppid stat user comm rest; do
  cmdline=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
  cgroup=$(cat /proc/$pid/cgroup 2>/dev/null || true)
  in_container=0
  if echo "$cgroup" | egrep -q 'docker|kubepods|containerd'; then
    in_container=1
  fi
  echo "PID=$pid PPID=$ppid STAT=$stat USER=$user CMD=$comm in_container=$in_container CMDLINE=$cmdline" | tee -a "$LOG"
  # decision: stop only if not in container and not obviously belonging to vx11
  if [ "$APPLY" -eq 1 ]; then
    if [ "$in_container" -eq 0 ]; then
      echo "Stopping orphan python PID=$pid" | tee -a "$LOG"
      kill -TERM "$pid" || true
    fi
  else
    echo "DRY-RUN: would consider stopping PID=$pid if orphan and safe" | tee -a "$LOG"
  fi
done

# systemd: report running and failed services and timers
echo "\n-- systemd running services --" | tee -a "$LOG"
systemctl --no-pager list-units --type=service --state=running | tee -a "$LOG" 2>/dev/null || true

echo "\n-- systemd failed services --" | tee -a "$LOG"
systemctl --no-pager list-units --type=service --state=failed | tee -a "$LOG" 2>/dev/null || true

echo "\n-- systemd timers (all) --" | tee -a "$LOG"
systemctl list-timers --all | tee -a "$LOG" 2>/dev/null || true

# Note: STOP/DISABLE operations are intentionally not performed in default DRY-RUN.
# To apply a stop/disable, set APPLY=1 and call systemctl stop/disable for the selected unit(s).
# Example (not executed here): systemctl stop some-obsolete.service && systemctl disable some-obsolete.service

echo "System cleanup safe script finished: $(date -u)" | tee -a "$LOG"

echo "Logs written to $LOG"
