#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

echo "Building production image..."
cd ../backend
docker build --platform linux/amd64 -f Dockerfile.production -t image-similarity-backend:prod .

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Tagging images..."
docker tag image-similarity-backend:prod $ECR_BACKEND:latest
docker tag image-similarity-backend:prod $ECR_BACKEND:$TIMESTAMP

echo "Pushing to ECR..."
docker push $ECR_BACKEND:latest
docker push $ECR_BACKEND:$TIMESTAMP

cd ../aws-deploy

echo "Updating ECS service..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --force-new-deployment \
  --region $REGION \
  --output json > /dev/null

echo "Deployment initiated!"
echo ""
echo "Monitor status with:"
echo "aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2 --query 'services[0].deployments[0]' --output json"
echo ""
sleep 5
aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2 --query 'services[0].[serviceName,deployments[0].[status,runningCount,desiredCount]]' --output table
