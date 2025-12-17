#!/bin/bash
################################################################################
# vx11-autosync-full.sh
# Sincronización automática para /home/elkakas314/VX_11-full
# Rama: feature/ui/operator-advanced
################################################################################

set -o pipefail

# Configuration
REPO_PATH="/home/elkakas314/VX_11-full"
BRANCH="feature/ui/operator-advanced"
REMOTE="vx_11_remote"
SYNC_INTERVAL=60
LOG_FILE="/tmp/vx11-autosync-full.log"
GITHUB_PAT="${GITHUB_PAT:-}"

# Inicializar log
init_log() {
    echo "[$(date -u)] ===== AUTOSYNC FULL START =====" > "$LOG_FILE"
    echo "[$(date -u)] Repo: $REPO_PATH" >> "$LOG_FILE"
    echo "[$(date -u)] Branch: $BRANCH" >> "$LOG_FILE"
    echo "[$(date -u)] Remote: $REMOTE" >> "$LOG_FILE"
    echo "[$(date -u)] Interval: ${SYNC_INTERVAL}s" >> "$LOG_FILE"
}

# Log message
log_msg() {
    local msg="$1"
    echo "[$(date -u)] $msg" >> "$LOG_FILE"
}

# Check if token is configured
check_token() {
    if [ -z "$GITHUB_PAT" ] && [ -f "/home/elkakas314/vx11/tokens.env" ]; then
        export GITHUB_PAT=$(grep "GITHUB_PAT=" "/home/elkakas314/vx11/tokens.env" 2>/dev/null | cut -d'=' -f2 | tr -d '\n' | tr -d '"' | tr -d "'")
    fi
    
    if [ -z "$GITHUB_PAT" ]; then
        log_msg "ERROR: GITHUB_PAT not found in env or tokens.env"
        return 1
    fi
    return 0
}

# Ensure remote is configured
setup_remote() {
    cd "$REPO_PATH" || exit 1
    
    if ! git remote get-url "$REMOTE" &>/dev/null; then
        log_msg "ERROR: Remote '$REMOTE' not configured"
        return 1
    fi
    
    git config credential.helper store 2>/dev/null || true
    return 0
}

# Main sync loop
sync_loop() {
    local conflict_pause=0
    
    while true; do
        cd "$REPO_PATH" || { log_msg "ERROR: Cannot cd to repo"; sleep "$SYNC_INTERVAL"; continue; }
        
        # Check if in conflict state
        if [ -f "$REPO_PATH/.git/MERGE_HEAD" ] || [ -f "$REPO_PATH/.git/REBASE_MERGE" ]; then
            if [ "$conflict_pause" -eq 0 ]; then
                log_msg "CONFLICT DETECTED: Merge/Rebase in progress. Pausing autosync."
                log_msg "ACTION REQUIRED: Resolve conflict manually in your editor."
                log_msg "Commands to fix:"
                log_msg "  git status         # See conflicted files"
                log_msg "  # Edit files to resolve conflicts"
                log_msg "  git add -A"
                log_msg "  git rebase --continue  OR  git merge --continue"
                conflict_pause=1
            fi
            
            # Check if conflict is resolved
            if [ ! -f "$REPO_PATH/.git/MERGE_HEAD" ] && [ ! -f "$REPO_PATH/.git/REBASE_MERGE" ]; then
                log_msg "CONFLICT RESOLVED: Resuming autosync."
                conflict_pause=0
            else
                sleep "$SYNC_INTERVAL"
                continue
            fi
        fi
        
        # 1. Commit local changes if any
        if [ -n "$(git status --porcelain)" ]; then
            log_msg ">> Uncommitted changes detected. Staging and committing..."
            if git add -A 2>&1 | grep -q "error"; then
                log_msg "ERROR during git add -A"
            else
                COMMIT_MSG="autosync-full: $(date '+%Y-%m-%d %H:%M:%S UTC')"
                if git commit -m "$COMMIT_MSG" --no-verify 2>&1 | tee -a "$LOG_FILE" | grep -q "create mode\|changed\|delete"; then
                    log_msg "✓ Committed local changes"
                else
                    log_msg "  (no changes to commit)"
                fi
            fi
        fi
        
        # 2. Fetch latest from remote
        log_msg ">> Fetching from $REMOTE/$BRANCH..."
        if ! git fetch "$REMOTE" "$BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
            log_msg "ERROR during fetch"
            sleep "$SYNC_INTERVAL"
            continue
        fi
        
        # 3. Check for remote changes and rebase
        LOCAL_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")
        REMOTE_COMMIT=$(git rev-parse "$REMOTE/$BRANCH" 2>/dev/null || echo "")
        
        if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
            log_msg ">> Remote has changes. Rebasing..."
            if git pull --rebase "$REMOTE" "$BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
                log_msg "✓ Rebased successfully"
            else
                REBASE_STATUS=$?
                log_msg "ERROR during rebase (exit code: $REBASE_STATUS)"
                log_msg "  Rebase is paused. Resolve conflicts and run 'git rebase --continue'"
                sleep "$SYNC_INTERVAL"
                continue
            fi
        else
            log_msg "  (local and remote are identical)"
        fi
        
        # 4. Push local commits to remote
        log_msg ">> Pushing to $REMOTE/$BRANCH..."
        if git push "$REMOTE" "$BRANCH" --no-verify 2>&1 | tee -a "$LOG_FILE"; then
            log_msg "✓ Push successful"
        else
            PUSH_STATUS=$?
            log_msg "ERROR during push (exit code: $PUSH_STATUS)"
        fi
        
        log_msg "  [waiting ${SYNC_INTERVAL}s for next sync]"
        sleep "$SYNC_INTERVAL"
    done
}

# Main entry point
main() {
    init_log
    
    if ! check_token; then
        log_msg "FATAL: Cannot proceed without GITHUB_PAT"
        exit 1
    fi
    
    if ! setup_remote; then
        log_msg "FATAL: Cannot setup remote"
        exit 1
    fi
    
    log_msg "Starting autosync loop (PID: $$)"
    sync_loop
}

# Trap for clean shutdown
trap 'log_msg "AUTOSYNC FULL STOPPED (PID: $$)"; exit 0' SIGTERM SIGINT

main "$@"
