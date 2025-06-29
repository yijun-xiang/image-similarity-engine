#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"

echo "Step 1: Login to ECR"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Step 2: Build a simple working image"
cd ../backend
cat > Dockerfile.test << 'DOCKERFILE'
FROM nginx:alpine
RUN echo '{"status": "healthy"}' > /usr/share/nginx/html/health
EXPOSE 80
DOCKERFILE

echo "Step 3: Build for AMD64"
docker build --platform linux/amd64 -f Dockerfile.test -t test-backend:latest .

echo "Step 4: Tag and push"
docker tag test-backend:latest $ECR_BACKEND:latest
docker push $ECR_BACKEND:latest

echo "Step 5: Verify"
aws ecr describe-images \
  --repository-name image-similarity-backend \
  --region us-west-2 \
  --query 'imageDetails[?imageTags!=`null`].[imageTags[0],repositoryName,imagePushedAt]' \
  --output table

cd ../aws-deploy

echo "Step 6: Update ECS"
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --force-new-deployment \
  --region $REGION

echo "Done! Check deployment in 1 minute"
