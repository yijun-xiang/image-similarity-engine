#!/bin/bash
set -e

echo "🚀 Deploying to AWS App Runner"
echo "=============================="

PROJECT_NAME="image-similarity"
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="035711439189"

echo "1️⃣ Creating ECR repository..."
aws ecr create-repository --repository-name $PROJECT_NAME --region $AWS_REGION 2>/dev/null || true

echo "2️⃣ Building Docker image..."
cd ../../backend
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t $PROJECT_NAME .
docker tag $PROJECT_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME:latest

echo "✅ Image pushed to ECR!"
echo "Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$PROJECT_NAME:latest"
echo ""
echo "Now go to AWS Console > App Runner to create service with this image"
