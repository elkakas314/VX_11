#!/bin/bash
# Apply a patch file to the working tree
# Usage: ./tools/apply_patch.sh <patch_file> [--check]

PATCH_FILE="${1}"
CHECK_MODE="${2}"

if [[ ! -f "$PATCH_FILE" ]]; then
  echo "ERROR: Patch file not found: $PATCH_FILE"
  exit 1
fi

if [[ "$CHECK_MODE" == "--check" ]]; then
  echo "Checking patch compatibility..."
  git apply --check "$PATCH_FILE" || {
    echo "ERROR: Patch does not apply cleanly"
    exit 1
  }
  echo "✓ Patch is compatible"
else
  echo "Applying patch: $PATCH_FILE"
  git apply "$PATCH_FILE" || {
    echo "ERROR: Failed to apply patch"
    exit 1
  }
  echo "✓ Patch applied successfully"
fi
