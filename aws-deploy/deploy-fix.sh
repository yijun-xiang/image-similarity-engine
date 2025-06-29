#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"

echo "Setting up Docker buildx for multi-platform builds..."
docker buildx create --name multiarch-builder --use || docker buildx use multiarch-builder
docker buildx inspect --bootstrap

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Building and pushing multi-platform Docker image..."
cd ../backend

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t $ECR_BACKEND:latest \
  -t $ECR_BACKEND:$(date +%Y%m%d%H%M%S) \
  --push \
  .

cd ../aws-deploy

echo "Force updating ECS service..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --force-new-deployment \
  --region $REGION

echo "Deployment fix completed!"
echo ""
echo "Monitor the deployment progress:"
echo "watch 'aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2 --query \"services[0].deployments[0].[status,runningCount,desiredCount]\" --output table'"
