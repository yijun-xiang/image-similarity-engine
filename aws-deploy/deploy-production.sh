#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID="035711439189"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity"

echo "Building production Docker image..."
cd backend
docker build -f Dockerfile.full -t image-similarity:production .

echo "Tagging and pushing to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI
docker tag image-similarity:production $ECR_URI:production
docker push $ECR_URI:production

cd ..

echo "Registering new task definition..."
aws ecs register-task-definition --cli-input-json file://aws-deploy/task-definition-production.json --region $REGION

echo "Updating ECS service..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --task-definition image-similarity-production \
  --force-new-deployment \
  --region $REGION

echo "Deployment started! Monitor progress:"
echo "aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2"
