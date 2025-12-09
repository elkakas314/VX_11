#!/bin/bash
# VX11 System - Restart all services

set -e

echo "=== VX11 System - Restarting ==="

docker-compose down
sleep 2
docker-compose up -d

echo "⏳ Esperando servicios..."
sleep 5

echo "✅ Sistema reiniciado"
