#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYSTEMD_DIR="$BASE_DIR/scripts/systemd"

echo "Installing VX11 systemd units (dry-run-safe)."

for svc in tentaculo_link madre switch hermes hormiguero manifestator mcp shubniggurath; do
  unit="$SYSTEMD_DIR/vx11-${svc}.service"
  if [ -f "$unit" ]; then
    echo "Installing $unit -> /etc/systemd/system/"
    sudo cp "$unit" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable "vx11-${svc}.service"
    echo "Installed and enabled vx11-${svc}.service"
  else
    echo "Unit not found: $unit"
  fi
done

echo "All done. Start services with: sudo systemctl start vx11-tentaculo_link" 
