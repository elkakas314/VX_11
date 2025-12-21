#!/bin/bash
# Create remote repo and push branch
# Usage: ./tools/create_remote_and_push.sh <owner> <repo> [branch]

OWNER="${1:-elkakas314}"
REPO="${2:-VX_11}"
BRANCH="${3:-feature/ui/operator-advanced}"

if ! command -v gh &>/dev/null; then
  echo "ERROR: GitHub CLI (gh) not found. Install from https://cli.github.com/"
  exit 1
fi

echo "Creating private GitHub repo: $OWNER/$REPO"
gh repo create "$REPO" --private --source=. --remote=origin --push || {
  echo "ERROR: Failed to create repo (may already exist)"
  exit 1
}

echo "Pushing branch: $BRANCH"
git push -u origin "$BRANCH" || {
  echo "ERROR: Failed to push branch"
  exit 1
}

echo "✓ Remote created and branch pushed to: https://github.com/$OWNER/$REPO"
