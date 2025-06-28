#!/bin/bash

set -e

echo "🚀 Starting Million-Scale Image Similarity Engine..."

echo "📊 System Requirements Check..."
TOTAL_RAM=$(free -g | awk 'NR==2{print $2}')
if [ $TOTAL_RAM -lt 64 ]; then
    echo "⚠️  Warning: System has ${TOTAL_RAM}GB RAM, recommended 64GB+ for million-scale"
fi

echo "🐳 Starting scaled infrastructure..."
docker-compose -f docker-compose.scale.yml up -d

echo "⏳ Waiting for services to initialize..."
sleep 60

echo "🔧 Initializing sharded collections..."
poetry run python -c "
import asyncio
from app.services.sharding_service import get_sharding_service

async def init():
    service = get_sharding_service()
    await service.create_collections('image_features', 512)

asyncio.run(init())
"

echo "📈 Starting performance monitoring..."
docker-compose -f docker-compose.monitoring.yml up -d

echo "✅ Million-scale system ready!"
echo ""
echo "📍 Endpoints:"
echo "   Load Balancer: http://localhost:8080"
echo "   HAProxy Stats: http://localhost:8081"
echo "   Grafana: http://localhost:3001"
echo ""
echo "🧪 Run load test:"
echo "   cd backend && poetry run python scripts/load_test_million.py"
