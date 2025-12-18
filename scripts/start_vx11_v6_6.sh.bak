#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh"
# Ajuste VX11 v6.6 – arranque operativo (2025-12-05)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "Arrancando VX11 v6.6 (docker-compose)..."
docker-compose up -d

echo "Servicios VX11:"
docker-compose ps

cat <<'EOF'
Endpoints útiles:
- Operator backend: http://127.0.0.1:8011
- Hormiguero: http://127.0.0.1:8004/health
- Madre: http://127.0.0.1:8001/health
- MCP: http://127.0.0.1:8006/health
- Spawner: http://127.0.0.1:8008/health
- Tentaculo Link/Gateway: http://127.0.0.1:8000/health (si está en compose)
EOF
