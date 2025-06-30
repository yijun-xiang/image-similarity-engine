#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID="035711439189"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity"
CLUSTER="image-similarity-cluster"

echo "Building full Docker image..."
cd backend
docker build -t image-similarity:full .
cd ..

echo "Pushing to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI
docker tag image-similarity:full $ECR_URI:full
docker push $ECR_URI:full

echo "Deploying Redis..."
bash aws-deploy/deploy-redis.sh

echo "Deploying Qdrant..."
bash aws-deploy/deploy-qdrant.sh

echo "Updating backend to full version..."
aws ecs register-task-definition \
  --cli-input-json file://aws-deploy/task-definition-full.json \
  --region $REGION

aws ecs update-service \
  --cluster $CLUSTER \
  --service image-similarity-service \
  --task-definition image-similarity-full \
  --force-new-deployment \
  --region $REGION

echo "Deployment complete!"
