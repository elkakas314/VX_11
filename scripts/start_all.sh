#!/bin/bash
# VX11 System - Start all services with docker-compose

set -e

echo "=== VX11 System v5.0 ==="
echo "Iniciando todos los servicios..."

# Crear directorios si no existen
mkdir -p build/artifacts/logs build/artifacts/sandbox data/runtime models

# Construir imágenes
echo "🔨 Compilando imágenes Docker..."
docker-compose build --no-cache

# Iniciar servicios
echo "🚀 Arrancando servicios..."
docker-compose up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén disponibles..."
sleep 5

# Validar salud
echo "✅ Validando health checks..."
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008; do
    if curl -f http://localhost:$port/health > /dev/null 2>&1; then
        echo "✓ Port $port: OK"
    else
        echo "✗ Port $port: FAILED"
    fi
done

echo ""
echo "=== Estado del Gateway ==="
curl -s http://localhost:8000/vx11/status | python3 -m json.tool

echo ""
echo "✅ Sistema VX11 iniciado correctamente"
echo "Puertos: 8000-8007"
echo "Use 'docker-compose logs -f' para ver logs"
