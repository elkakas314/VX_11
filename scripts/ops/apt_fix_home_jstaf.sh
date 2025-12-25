#!/bin/bash
# apt_fix_home_jstaf.sh — Idempotent repair script for home:jstaf EXPKEYSIG
# 
# PURPOSE:
#   - Detects if /etc/apt/sources.list.d contains home:jstaf repo
#   - Runs apt-get update; if EXPKEYSIG error occurs, disables onedriver.list
#   - Retries apt-get update
#   - Logs all actions
#
# USAGE:
#   bash scripts/ops/apt_fix_home_jstaf.sh
#
# NOTES:
#   - Idempotent: safe to run multiple times
#   - Fail-open: if no home:jstaf, exits cleanly
#   - NO apt-key manipulation (too risky)
#   - Only disables, never deletes

set -e

SCRIPT_NAME="apt_fix_home_jstaf"
LOG_FILE="/tmp/${SCRIPT_NAME}_$(date +%Y%m%d_%H%M%S).log"
ONEDRIVER_LIST="/etc/apt/sources.list.d/onedriver.list"
ONEDRIVER_DISABLED="/etc/apt/sources.list.d/onedriver.list.disabled"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    local level="$1"
    shift
    local msg="$@"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [$level] $msg" | tee -a "$LOG_FILE"
}

info() { log "INFO" "$@"; }
warn() { log "WARN" "$@"; }
error() { log "ERROR" "$@"; }

header() {
    echo "======================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "======================================" | tee -a "$LOG_FILE"
}

main() {
    header "APT Fix: home:jstaf Repository"
    
    info "Log file: $LOG_FILE"
    info "System: $(uname -s) $(uname -r)"
    
    # Step 1: Check if onedriver.list exists
    if [[ ! -f "$ONEDRIVER_LIST" ]]; then
        info "No onedriver.list found. Nothing to do."
        info "Script exits successfully (idempotent)."
        return 0
    fi
    
    # Step 2: Check if already disabled
    if [[ -f "$ONEDRIVER_DISABLED" && ! -f "$ONEDRIVER_LIST" ]]; then
        info "onedriver.list already disabled. Exiting cleanly."
        return 0
    fi
    
    # Step 3: Check if home:jstaf is in the file
    if ! grep -q "home:jstaf\|jstaf" "$ONEDRIVER_LIST" 2>/dev/null; then
        info "onedriver.list does not contain home:jstaf. Skipping fix."
        return 0
    fi
    
    info "home:jstaf repository detected in $ONEDRIVER_LIST"
    
    # Step 4: Try apt-get update first (might work)
    info "Attempting apt-get update..."
    if sudo apt-get update &>> "$LOG_FILE"; then
        info "apt-get update succeeded. No fix needed."
        return 0
    fi
    
    warn "apt-get update failed. Checking for EXPKEYSIG / not signed error..."
    
    # Step 5: Check if error is related to EXPKEYSIG
    if tail -20 "$LOG_FILE" | grep -E "EXPKEYSIG|not signed" &>/dev/null; then
        warn "Detected EXPKEYSIG or 'not signed' error related to $ONEDRIVER_LIST"
        warn "Disabling repository by renaming to .disabled..."
        
        if sudo mv "$ONEDRIVER_LIST" "$ONEDRIVER_DISABLED"; then
            info "Successfully disabled: $ONEDRIVER_LIST -> $ONEDRIVER_DISABLED"
        else
            error "Failed to disable $ONEDRIVER_LIST (permission denied or already disabled)."
            return 1
        fi
        
        # Step 6: Retry apt-get update
        info "Retrying apt-get update with repository disabled..."
        if sudo apt-get update &>> "$LOG_FILE"; then
            info "apt-get update succeeded after disabling home:jstaf repo!"
            echo -e "${GREEN}✓ Fix successful${NC}"
            return 0
        else
            error "apt-get update still failed after disabling home:jstaf."
            error "Check $LOG_FILE for details."
            return 1
        fi
    else
        warn "Error not related to EXPKEYSIG. Leaving repository as-is."
        error "Manual investigation required. Log: $LOG_FILE"
        return 1
    fi
}

# Trap errors
trap 'error "Script interrupted"; exit 1' INT TERM

# Run
if main; then
    info "Script completed successfully."
    echo -e "${GREEN}Status: OK${NC}"
    exit 0
else
    error "Script failed. See $LOG_FILE"
    echo -e "${RED}Status: FAILED${NC}"
    exit 1
fi
