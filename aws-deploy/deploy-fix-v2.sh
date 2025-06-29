#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Building Docker image for AMD64..."
cd ../backend

# 使用传统 docker build 方法，指定平台
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t image-similarity-backend:latest .

echo "Tagging and pushing image..."
docker tag image-similarity-backend:latest $ECR_BACKEND:latest
docker tag image-similarity-backend:latest $ECR_BACKEND:$(date +%Y%m%d%H%M%S)

docker push $ECR_BACKEND:latest
docker push $ECR_BACKEND:$(date +%Y%m%d%H%M%S)

cd ../aws-deploy

echo "Force updating ECS service..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --force-new-deployment \
  --region $REGION

echo "Deployment fix completed!"
echo ""
echo "Check deployment status:"
echo "aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2 --query 'services[0].deployments[0]' --output json"

# 等待几秒后自动检查状态
sleep 10
echo ""
echo "Current status:"
aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2 --query 'services[0].deployments[0].[status,runningCount,desiredCount]' --output table
