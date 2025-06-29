#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"

echo "Step 1: Login to ECR"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Step 2: Pull nginx as test"
docker pull nginx:alpine

echo "Step 3: Tag properly"
docker tag nginx:alpine $ECR_BACKEND:latest

echo "Step 4: Push with tag"
docker push $ECR_BACKEND:latest

echo "Step 5: Verify push"
aws ecr describe-images \
  --repository-name image-similarity-backend \
  --region us-west-2 \
  --output table

echo "Step 6: Update ECS"
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --force-new-deployment \
  --region $REGION

echo "Done!"
