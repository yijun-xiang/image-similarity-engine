#!/bin/bash

set -e

echo "🚀 Starting Image Similarity Search Engine..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed."
    exit 1
fi

cd backend

if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
fi

echo "📁 Creating directories..."
mkdir -p models data/images logs

echo "📥 Downloading ML models..."
poetry run python scripts/download_models.py

cd ..

echo "🐳 Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

echo "🗄️ Initializing database..."
cd backend
poetry run python scripts/init_database.py
cd ..

echo "🏥 Running health check..."
curl -f http://localhost:8000/api/v1/health

echo "✅ All services are running!"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Search API: http://localhost:8000/api/v1/search"
echo "📊 Health Check: http://localhost:8000/api/v1/health"
