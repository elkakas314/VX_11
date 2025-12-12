#!/bin/bash
# Safe autosync: stash → fetch → rebase → apply stash → commit → push
# Usage: ./tools/autosync.sh [branch]

set -e

BRANCH="${1:-feature/ui/operator-advanced}"
REMOTE="origin"

log() {
  echo "[autosync] $(date '+%H:%M:%S') $*"
}

log "Starting safe autosync on branch: $BRANCH"

# 1. Stash uncommitted changes
log "Stashing local changes..."
STASH_COUNT=$(git stash list | wc -l)
git stash push -m "autosync-$(date +%s)"
STASH_NEW_COUNT=$(git stash list | wc -l)

# 2. Fetch latest from remote
log "Fetching from remote..."
git fetch "$REMOTE" "$BRANCH" || {
  log "ERROR: fetch failed; restoring stash"
  [[ $STASH_NEW_COUNT -gt $STASH_COUNT ]] && git stash pop
  exit 1
}

# 3. Rebase onto remote branch
log "Rebasing onto $REMOTE/$BRANCH..."
git rebase "$REMOTE/$BRANCH" || {
  log "ERROR: rebase conflict; aborting rebase and restoring stash"
  git rebase --abort
  [[ $STASH_NEW_COUNT -gt $STASH_COUNT ]] && git stash pop
  exit 1
}

# 4. Apply stash (if any)
if [[ $STASH_NEW_COUNT -gt $STASH_COUNT ]]; then
  log "Applying stashed changes..."
  git stash pop || {
    log "WARNING: stash pop conflict; resolve manually and run 'git stash drop'"
    exit 1
  }
fi

# 5. Commit WIP if changes exist
if ! git diff-index --quiet HEAD; then
  log "Committing WIP changes..."
  git add -A
  git commit -m "WIP: autosync-$(date +%s)" || log "No changes to commit"
fi

# 6. Push to remote
log "Pushing to $REMOTE/$BRANCH..."
git push "$REMOTE" "$BRANCH" || {
  log "ERROR: push failed"
  exit 1
}

log "Autosync completed successfully!"
