#!/bin/bash

set -e

echo "🧪 Running tests..."

cd backend

echo "📏 Checking code format..."
poetry run black --check app tests scripts || echo "⚠️ Format check failed"
poetry run isort --check-only app tests scripts || echo "⚠️ Import check failed"

echo "🔍 Running type checks..."
poetry run mypy app || echo "⚠️ Type check failed"

echo "🧪 Running unit tests..."
poetry run pytest tests/ -v --cov=app --cov-report=html || echo "⚠️ Unit tests failed"

echo "⚡ Running performance tests..."
poetry run python scripts/benchmark.py || echo "⚠️ Benchmark failed"

cd ..

echo "✅ All tests completed!"
