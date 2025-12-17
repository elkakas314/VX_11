#!/usr/bin/env bash
# Minimal cleanup protection helpers
# Usage: source scripts/cleanup_protect.sh

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXCLUDES_FILE="$REPO_ROOT/docs/audit/CLEANUP_EXCLUDES_CORE.txt"

load_cleanup_excludes() {
  EXCLUDES=()
  if [ -f "$EXCLUDES_FILE" ]; then
    while IFS= read -r l; do
      [ -z "$l" ] && continue
      EXCLUDES+=("$l")
    done < "$EXCLUDES_FILE"
  fi
}

is_core_path() {
  local path="$1"
  # normalize
  case "$path" in
    /*) abs="$path" ;;
    *) abs="$REPO_ROOT/$path" ;;
  esac
  for pat in "${EXCLUDES[@]:-}"; do
    # treat patterns as prefixes
    # check both relative and absolute
    if [[ "$abs" == "$REPO_ROOT/$pat"* || "$path" == "$pat"* ]]; then
      return 0
    fi
  done
  return 1
}

safe_mv() {
  local src="$1"; shift
  local dst="$1"; shift || true
  load_cleanup_excludes
  if is_core_path "$src" || is_core_path "$dst"; then
    echo "ABORT: move would touch CORE path. src=$src dst=$dst" >&2
    exit 2
  fi
  mv "$src" "$dst"
}

safe_rm() {
  local target="$1"
  load_cleanup_excludes
  if is_core_path "$target"; then
    echo "ABORT: rm would touch CORE path: $target" >&2
    exit 2
  fi
  rm -rf "$target"
}
