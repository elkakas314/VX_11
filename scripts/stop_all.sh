#!/bin/bash
# VX11 System - Stop all services

set -e

echo "=== VX11 System - Stopping ==="
docker-compose down

echo "✅ Todos los servicios detenidos"
