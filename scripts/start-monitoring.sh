#!/bin/bash

echo "🚀 Starting Monitoring Stack..."

# Create monitoring network if it doesn't exist
docker network create monitoring 2>/dev/null || true

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "✅ Monitoring stack is running!"
echo "📊 Prometheus: http://localhost:9090"
echo "📈 Grafana: http://localhost:3001 (admin/admin)"
echo "🚨 AlertManager: http://localhost:9093"

echo ""
echo "To view metrics:"
echo "1. Open Grafana at http://localhost:3001"
echo "2. Login with admin/admin"
echo "3. Navigate to Image Similarity Engine dashboard"
