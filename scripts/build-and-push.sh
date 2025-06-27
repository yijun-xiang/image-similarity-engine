#!/bin/bash
set -e

REGISTRY="your-registry.com"
IMAGE_NAME="image-similarity-backend"
TAG="${1:-latest}"

echo "Building Docker image..."
cd backend
docker build -t ${IMAGE_NAME}:${TAG} .

echo "Tagging image..."
docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:${TAG}

echo "Pushing to registry..."
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}

echo "Build complete!"
echo "Image: ${REGISTRY}/${IMAGE_NAME}:${TAG}"
