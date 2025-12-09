#!/bin/bash
# VX11 System - Cleanup and reset

set -e

echo "=== VX11 System - Cleanup ==="

# Detener servicios
docker-compose down -v

# Limpiar volúmenes locales (opcional)
echo "Limpiando directorios temporales..."
rm -rf build/artifacts/logs/* build/artifacts/sandbox/* data/runtime/*.db 2>/dev/null || true

echo "✅ Sistema limpiado"
