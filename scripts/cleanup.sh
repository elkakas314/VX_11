#!/bin/bash
# VX11 System - Cleanup and reset

set -e

echo "=== VX11 System - Cleanup ==="

# Detener servicios
docker-compose down -v

# Hardening: load safe helpers to prevent touching CORE paths
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh" || exit 1

# Limpiar volúmenes locales (opcional)
echo "Limpiando directorios temporales..."
safe_rm build/artifacts/logs/* || true
safe_rm build/artifacts/sandbox/* || true
safe_rm data/runtime/*.db || true

echo "✅ Sistema limpiado"
