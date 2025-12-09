#!/usr/bin/env bash
# Run a single anti-caos scan and emit organize intent (uses hormiguero auto-organizer CLI).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "Running hormiguero auto-organizer once (emit enabled)..."
python3 -m hormiguero.auto_organizer --emit --json

# Opcional: aplicar PATCH_OPS de drift raíz si aún existen
if [[ -d "logs" || -d "sandbox" || -d "shub_sandbox" || -d "forensic" ]]; then
  echo "Applying drift patch ops (vx11 v6.6)..."
  python3 scripts/apply_patch_ops_vx11_v6_6.py || echo "Patch ops script reported an error; review output."
fi

echo "Anti-caos scan completed."
