#!/bin/bash
set -e

ENVIRONMENT="${1:-dev}"
NAMESPACE="image-similarity-${ENVIRONMENT}"

echo "Deploying to ${ENVIRONMENT} environment..."

# Apply base resources with overlay
kubectl apply -k kubernetes/overlays/${ENVIRONMENT}

# Wait for deployments
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/backend \
  deployment/celery-worker \
  -n ${NAMESPACE}

# Check pod status
echo "Pod status:"
kubectl get pods -n ${NAMESPACE}

# Get service endpoints
echo "Service endpoints:"
kubectl get svc -n ${NAMESPACE}

echo "Deployment complete!"
