#!/bin/bash

set -e

echo "🚀 Starting Million-Scale Image Similarity Engine..."

echo "🧹 Cleaning up existing services..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.scale.yml down 2>/dev/null || true

echo "�� Starting scaled infrastructure..."
docker-compose -f docker-compose.scale.yml up -d

echo "⏳ Waiting for services to initialize..."
sleep 30

echo "✅ Checking service health..."
for port in 8001 8002 8003; do
    if curl -f http://localhost:$port/api/v1/health 2>/dev/null; then
        echo "Backend on port $port is healthy"
    else
        echo "Warning: Backend on port $port is not responding"
    fi
done

echo ""
echo "📍 Endpoints:"
echo "   Backend 1: http://localhost:8001"
echo "   Backend 2: http://localhost:8002"
echo "   Backend 3: http://localhost:8003"
echo "   Load Balancer: http://localhost:8080"
echo "   HAProxy Stats: http://localhost:8081"
echo ""
echo "🧪 To run load test:"
echo "   cd backend && poetry run python ../scripts/load_test_million.py"
