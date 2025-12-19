#!/bin/bash
source "$(dirname "${BASH_SOURCE[0]}")/cleanup_protect.sh"
# Quick startup script for Shub development

set -e

echo "🎵 Starting Shubniggurath v1.0..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install requirements
echo "📚 Installing dependencies..."
pip install -q -r requirements_shub.txt

# Environment check
if [ ! -f "tokens.env" ]; then
    echo "⚠️  tokens.env not found. Creating from sample..."
    cp tokens.env.sample tokens.env
    echo "   ⚠️  Please update tokens.env with your credentials"
fi

source tokens.env

# PostgreSQL check (development only)
if command -v docker &> /dev/null; then
    echo "🐘 Checking PostgreSQL..."
    if ! docker ps | grep -q postgres; then
        echo "   Starting PostgreSQL container..."
        docker run -d \
            --name shubniggurath-pg \
            -e POSTGRES_DB=shubniggurath \
            -e POSTGRES_PASSWORD=changeme \
            -p 5432:5432 \
            postgres:14-alpine
        sleep 2
    fi
fi

# Start services
echo "🚀 Starting services..."

# Start Shub
echo "   Starting Shubniggurath (8007)..."
python3 shubniggurath/main.py > logs/shub.log 2>&1 &

# Wait for startup
sleep 2

# Health check
if curl -s http://localhost:8007/health > /dev/null 2>&1; then
    echo "✅ Shubniggurath running at http://localhost:8007"
else
    echo "❌ Shubniggurath failed to start. Check logs/shub.log"
    exit 1
fi

echo ""
echo "📊 Endpoints:"
echo "   Shub API:        http://localhost:8007/shub"
echo "   Health:          http://localhost:8007/health"
echo "   Dashboard:       http://localhost:8011/operator/shub/dashboard"
echo ""
echo "🧪 Run tests:"
echo "   pytest tests/test_shubniggurath_complete_suite.py -v"
echo ""
echo "📖 Documentation:"
echo "   cat docs/SHUBNIGGURATH_COMPLETE.md"
echo ""
