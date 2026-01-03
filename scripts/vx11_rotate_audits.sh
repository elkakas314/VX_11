#!/bin/bash
#
# vx11_rotate_audits.sh
# Purpose: Rotate old audit directories (>1 week) to archive/; cleanup >3 months
# Usage: ./scripts/vx11_rotate_audits.sh [--dry-run] [--aggressive]
#
set -e

AUDIT_DIR="./docs/audit"
ARCHIVE_DIR="${AUDIT_DIR}/archive"
DRY_RUN=false
AGGRESSIVE=false

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift ;;
    --aggressive) AGGRESSIVE=true; shift ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================================

log_info "VX11 Audit Rotation Script"
[ "$DRY_RUN" = true ] && log_warn "DRY RUN: No changes will be made"
[ "$AGGRESSIVE" = true ] && log_warn "AGGRESSIVE: Will delete archives >3 months"

if [ ! -d "$AUDIT_DIR" ]; then
  log_err "Audit directory not found: $AUDIT_DIR"
  exit 1
fi

mkdir -p "$ARCHIVE_DIR"

# ============================================================================
# PHASE 1: Identify SCORECARD.json, DB_SCHEMA, DB_MAP (keep latest, don't move)
# ============================================================================

log_info "PHASE 1: Identifying core files (don't move)"

CRITICAL_FILES=(
  "SCORECARD.json"
  "DB_SCHEMA_v7_FINAL.json"
  "DB_MAP_v7_FINAL.md"
  "CLEANUP_EXCLUDES_CORE.txt"
)

for file in "${CRITICAL_FILES[@]}"; do
  if [ -f "${AUDIT_DIR}/${file}" ]; then
    log_info "  ✓ Keeping: $file"
  fi
done

# ============================================================================
# PHASE 2: Find OUTDIR directories (timestamp-based, e.g., 20251230T020936Z_apply_plan)
# ============================================================================

log_info "PHASE 2: Scanning OUTDIR directories"

OUTDIRS=($(find "$AUDIT_DIR" -maxdepth 1 -type d -name "*Z*" -o -name "*Z_*" 2>/dev/null | sort -r || true))

if [ ${#OUTDIRS[@]} -eq 0 ]; then
  log_warn "No OUTDIR directories found"
else
  log_info "Found ${#OUTDIRS[@]} OUTDIR directories"
fi

# ============================================================================
# PHASE 3: Archive old OUTDIRs (>7 days)
# ============================================================================

log_info "PHASE 3: Archiving OUTDIRs >7 days old"

ARCHIVE_COUNT=0

for dir in "${OUTDIRS[@]}"; do
  basename_dir=$(basename "$dir")
  
  # Skip if file (not dir)
  [ ! -d "$dir" ] && continue
  
  # Skip archive/ itself
  [[ "$basename_dir" == "archive" ]] && continue
  
  # Get age in days
  dir_time=$(stat -c %Y "$dir" 2>/dev/null || stat -f %m "$dir" 2>/dev/null || echo 0)
  now_time=$(date +%s)
  age_days=$(( ($now_time - $dir_time) / 86400 ))
  
  if [ "$age_days" -gt 7 ]; then
    log_warn "  Old OUTDIR ($age_days days): $basename_dir"
    
    tar_file="${ARCHIVE_DIR}/${basename_dir}.tar.gz"
    
    if [ "$DRY_RUN" = true ]; then
      log_info "    [DRY RUN] Would compress: $tar_file"
    else
      if [ ! -f "$tar_file" ]; then
        log_info "    Compressing to: $tar_file"
        tar -czf "$tar_file" -C "$AUDIT_DIR" "$basename_dir" 2>/dev/null || true
        rm -rf "$dir"
        ARCHIVE_COUNT=$((ARCHIVE_COUNT + 1))
      else
        log_warn "    Archive exists, skipping: $tar_file"
      fi
    fi
  else
    log_info "  Fresh OUTDIR ($age_days days): $basename_dir"
  fi
done

log_info "Archived: $ARCHIVE_COUNT directories"

# ============================================================================
# PHASE 4: Clean old archives (>3 months, optional --aggressive)
# ============================================================================

if [ "$AGGRESSIVE" = true ]; then
  log_warn "PHASE 4: Cleaning archives >3 months (--aggressive)"
  
  CLEANUP_COUNT=0
  for tar_file in "${ARCHIVE_DIR}"/*.tar.gz; do
    [ ! -f "$tar_file" ] && continue
    
    tar_time=$(stat -c %Y "$tar_file" 2>/dev/null || stat -f %m "$tar_file" 2>/dev/null || echo 0)
    age_days=$(( ($now_time - $tar_time) / 86400 ))
    
    if [ "$age_days" -gt 90 ]; then
      basename_tar=$(basename "$tar_file")
      log_warn "  Old archive ($age_days days): $basename_tar"
      
      if [ "$DRY_RUN" = true ]; then
        log_info "    [DRY RUN] Would delete: $tar_file"
      else
        rm "$tar_file"
        CLEANUP_COUNT=$((CLEANUP_COUNT + 1))
      fi
    fi
  done
  
  log_info "Deleted: $CLEANUP_COUNT old archives"
else
  log_info "PHASE 4: Skipped (use --aggressive to clean archives >3 months)"
fi

# ============================================================================
# PHASE 5: Report
# ============================================================================

log_info "PHASE 5: Final Report"

active_outdirs=$(find "$AUDIT_DIR" -maxdepth 1 -type d -name "*Z*" 2>/dev/null | wc -l || echo 0)
archived_files=$(find "$ARCHIVE_DIR" -type f -name "*.tar.gz" 2>/dev/null | wc -l || echo 0)
audit_size=$(du -sh "$AUDIT_DIR" 2>/dev/null | cut -f1)

log_info "Active OUTDIRs: $active_outdirs"
log_info "Archived .tar.gz files: $archived_files"
log_info "Total docs/audit/ size: $audit_size"

# ============================================================================

if [ "$DRY_RUN" = true ]; then
  log_warn "Dry-run complete. Run without --dry-run to apply changes."
else
  log_info "✅ Audit rotation complete"
fi

exit 0
