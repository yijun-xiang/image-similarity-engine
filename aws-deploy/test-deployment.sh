#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"

echo "Using nginx as test image..."
docker pull --platform linux/amd64 nginx:alpine

echo "Tagging as our backend..."
docker tag nginx:alpine $ECR_BACKEND:test

echo "Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Pushing test image..."
docker push $ECR_BACKEND:test

echo "Creating new task definition with test image..."
cat > test-task-def.json << TASKDEF
{
  "family": "image-similarity-test",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/image-similarity-stack-TaskExecutionRole-BnfykKPkkX0C",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "$ECR_BACKEND:test",
      "cpu": 256,
      "memory": 512,
      "essential": true,
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/image-similarity",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "test"
        }
      }
    }
  ]
}
TASKDEF

aws ecs register-task-definition --cli-input-json file://test-task-def.json --region $REGION

echo "Updating service with test task..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --task-definition image-similarity-test:1 \
  --region $REGION

echo "Test deployment started. This should work if the infrastructure is correct."
