#!/usr/bin/env bash
# Clean lightweight filesystem debris without touching backups or runtime DBs.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCHIVE_LOGS="${REPO_ROOT}/build/artifacts/logs/archive"
mkdir -p "${ARCHIVE_LOGS}"

prune_expr=(
  -path "${REPO_ROOT}/build/artifacts/backups" -o
  -path "${REPO_ROOT}/data/runtime"
)

echo "Removing __pycache__ directories..."
find "${REPO_ROOT}" \( "${prune_expr[@]}" \) -prune -o -type d -name "__pycache__" -print -exec safe_rm {} +

echo "Removing Python bytecode (*.pyc/*.pyo)..."
find "${REPO_ROOT}" \( "${prune_expr[@]}" \) -prune -o -type f \( -name "*.pyc" -o -name "*.pyo" \) -print -delete

echo "Removing .DS_Store..."
find "${REPO_ROOT}" \( "${prune_expr[@]}" \) -prune -o -type f -name ".DS_Store" -print -delete

echo "Archiving logs older than 14 days into ${ARCHIVE_LOGS}..."
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh" || exit 1
while IFS= read -r f; do
  safe_mv "$f" "${ARCHIVE_LOGS}/$(basename "$f")"
done < <(find "${REPO_ROOT}/build/artifacts/logs" -maxdepth 1 -type f -mtime +14 -print)
echo "Clean-up completed."
