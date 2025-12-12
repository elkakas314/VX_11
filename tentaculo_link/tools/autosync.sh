#!/bin/bash
# VX11 Autosync v2 — Autonomous Repository Synchronization
# Belongs to: tentaculo_link module
# Usage: ./tentaculo_link/tools/autosync.sh [branch]
# 
# Features:
#  - Detects real changes before committing
#  - Prevents infinite loops with lockfile
#  - Clears lock on success/failure
#  - Minimal logging (timestamp + result)
#  - Exits cleanly if no changes

set -e

BRANCH="${1:-feature/ui/operator-advanced}"
REMOTE="vx_11_remote"
REPO_ROOT="$(cd "$(dirname "$0")/../../" && pwd)"
LOCK_FILE="$REPO_ROOT/.autosync.lock"
LOG_FILE="$REPO_ROOT/.autosync.log"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
  local level="$1"
  shift
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] [$level] $*" | tee -a "$LOG_FILE"
}

log_only_file() {
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$timestamp] $*" >> "$LOG_FILE"
}

cleanup_lock() {
  rm -f "$LOCK_FILE"
  log_only_file "Lock removed"
}

trap cleanup_lock EXIT

# Check for lockfile (prevent concurrent execution)
if [[ -f "$LOCK_FILE" ]]; then
  LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null || echo "unknown")
  if ps -p "$LOCK_PID" > /dev/null 2>&1; then
    log "ERROR" "Autosync already running (PID: $LOCK_PID). Exiting."
    exit 1
  else
    log "WARN" "Stale lockfile detected (PID: $LOCK_PID). Removing and proceeding."
    rm -f "$LOCK_FILE"
  fi
fi

# Create lockfile with current PID
echo $$ > "$LOCK_FILE"
log_only_file "Lock acquired (PID: $$)"

# Ensure we're in the repo root
cd "$REPO_ROOT" || {
  log "ERROR" "Cannot cd to repo root: $REPO_ROOT"
  exit 1
}

log "INFO" "Starting autosync on branch: $BRANCH"

# Check if there are actual changes (before stashing)
CHANGES_COUNT=$(git status --porcelain | wc -l)
if [[ $CHANGES_COUNT -eq 0 ]]; then
  log "INFO" "No changes detected. Exiting cleanly."
  exit 0
fi

log "INFO" "Detected $CHANGES_COUNT changed/new file(s)"

# 1. Stash uncommitted changes
log "INFO" "Stashing local changes..."
STASH_COUNT_BEFORE=$(git stash list | wc -l)
git stash push -m "autosync-$(date +%s)" > /dev/null 2>&1 || {
  log "ERROR" "Stash failed"
  exit 1
}
STASH_COUNT_AFTER=$(git stash list | wc -l)

# 2. Fetch latest from remote
log "INFO" "Fetching from remote: $REMOTE/$BRANCH..."
if ! git fetch "$REMOTE" "$BRANCH" 2>&1 | tee -a "$LOG_FILE" | grep -q "From\|fatal"; then
  log "ERROR" "Fetch failed; restoring stash"
  [[ $STASH_COUNT_AFTER -gt $STASH_COUNT_BEFORE ]] && git stash pop > /dev/null 2>&1
  exit 1
fi

# 3. Rebase onto remote branch
log "INFO" "Rebasing onto $REMOTE/$BRANCH..."
if ! git rebase "$REMOTE/$BRANCH" > /dev/null 2>&1; then
  log "ERROR" "Rebase conflict; aborting and restoring stash"
  git rebase --abort
  [[ $STASH_COUNT_AFTER -gt $STASH_COUNT_BEFORE ]] && git stash pop > /dev/null 2>&1
  exit 1
fi

# 4. Apply stash (if any)
if [[ $STASH_COUNT_AFTER -gt $STASH_COUNT_BEFORE ]]; then
  log "INFO" "Applying stashed changes..."
  if ! git stash pop > /dev/null 2>&1; then
    log "WARN" "Stash pop conflict; manual resolution required"
    exit 1
  fi
fi

# 5. Check again if there are changes after rebase
FINAL_CHANGES=$(git status --porcelain | wc -l)
if [[ $FINAL_CHANGES -eq 0 ]]; then
  log "INFO" "No changes remain after rebase. Nothing to commit."
  exit 0
fi

# 6. Commit changes
log "INFO" "Committing changes ($FINAL_CHANGES file(s))..."
git add -A
COMMIT_HASH=$(git commit -m "autosync: $(date '+%Y-%m-%d %H:%M:%S %Z')" 2>&1 | grep -oP '\[.*\K[a-f0-9]+' || echo "unknown")
log "INFO" "Committed: $COMMIT_HASH"

# 7. Push to remote
log "INFO" "Pushing to $REMOTE/$BRANCH..."
if ! git push "$REMOTE" "$BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
  log "ERROR" "Push failed"
  exit 1
fi

log "INFO" "✅ Autosync completed successfully!"
exit 0
