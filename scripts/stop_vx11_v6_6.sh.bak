#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh"
# Ajuste VX11 v6.6 – parada operativa (2025-12-05)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "Deteniendo VX11 v6.6..."
docker-compose down
echo "VX11 v6.6 detenido."
