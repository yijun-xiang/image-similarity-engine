#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Building Docker image for AMD64..."
cd ../backend

DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -f Dockerfile.amd64 -t image-similarity-backend:latest .

echo "Tagging and pushing image..."
docker tag image-similarity-backend:latest $ECR_BACKEND:latest
docker push $ECR_BACKEND:latest

cd ../aws-deploy

echo "Force updating ECS service..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --force-new-deployment \
  --region $REGION

echo "Deployment completed!"
echo ""
sleep 10
aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2 --query 'services[0].deployments[0].[status,runningCount,desiredCount]' --output table
