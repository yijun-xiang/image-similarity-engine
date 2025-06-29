#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"

echo "Cleaning up old images..."
docker rmi $(docker images -q image-similarity-backend) 2>/dev/null || true

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Building for AMD64 explicitly..."
cd ../backend

docker build \
  --platform linux/amd64 \
  --no-cache \
  -f Dockerfile.minimal \
  -t image-similarity-backend:amd64 \
  .

echo "Checking image platform..."
docker inspect image-similarity-backend:amd64 | grep -A5 "Architecture"

echo "Tagging and pushing..."
docker tag image-similarity-backend:amd64 $ECR_BACKEND:latest
docker tag image-similarity-backend:amd64 $ECR_BACKEND:amd64-$(date +%Y%m%d%H%M%S)

docker push $ECR_BACKEND:latest
docker push $ECR_BACKEND:amd64-$(date +%Y%m%d%H%M%S)

cd ../aws-deploy

echo "Force updating ECS service..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --force-new-deployment \
  --region $REGION

echo "Deployment initiated. Checking status in 30 seconds..."
sleep 30

aws ecs describe-services \
  --cluster image-similarity-cluster \
  --services image-similarity-service \
  --region us-west-2 \
  --query 'services[0].deployments[0]' \
  --output json
