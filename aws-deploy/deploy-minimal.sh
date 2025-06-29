#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Building minimal Docker image..."
cd ../backend

export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker build -f Dockerfile.minimal -t image-similarity-backend:minimal .

echo "Pushing to ECR..."
docker tag image-similarity-backend:minimal $ECR_BACKEND:latest
docker push $ECR_BACKEND:latest

cd ../aws-deploy

echo "Updating ECS service..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --force-new-deployment \
  --region $REGION

echo "Done! Monitor deployment:"
while true; do 
    clear
    echo "ECS Service Status:"
    aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2 --query 'services[0].deployments[0].[status,runningCount,desiredCount]' --output table
    echo ""
    echo "Press Ctrl+C to exit"
    sleep 5
done
