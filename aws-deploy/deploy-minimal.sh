#!/bin/bash
set -e

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BACKEND="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity"

echo "Step 1: Deploying Redis..."
bash aws-deploy/create-redis.sh
source redis-endpoint.sh

echo "Step 2: Deploying Qdrant on ECS..."
# Create Qdrant task definition
cat > /tmp/qdrant-task.json << QDRANT_EOF
{
  "family": "qdrant-service",
  "taskRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "qdrant",
      "image": "qdrant/qdrant:v1.14.0",
      "portMappings": [
        {"containerPort": 6333, "protocol": "tcp"}
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/qdrant",
          "awslogs-region": "${REGION}",
          "awslogs-stream-prefix": "qdrant"
        }
      }
    }
  ]
}
QDRANT_EOF

aws logs create-log-group --log-group-name /ecs/qdrant --region $REGION 2>/dev/null || true

aws ecs register-task-definition \
  --cli-input-json file:///tmp/qdrant-task.json \
  --region $REGION

# Create Qdrant service if not exists
if ! aws ecs describe-services --cluster image-similarity-cluster --services qdrant-service --region $REGION 2>/dev/null | grep -q "qdrant-service"; then
  aws ecs create-service \
    --cluster image-similarity-cluster \
    --service-name qdrant-service \
    --task-definition qdrant-service:1 \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-068efec545b9458f8,subnet-02c7194e01eed748c],securityGroups=[sg-0fc2ebdd6f6730e65],assignPublicIp=ENABLED}" \
    --region $REGION
fi

echo "Waiting for Qdrant to start..."
sleep 30

# Get Qdrant private IP
QDRANT_IP=$(aws ecs list-tasks --cluster image-similarity-cluster --service-name qdrant-service --region $REGION --query 'taskArns[0]' --output text | xargs -I {} aws ecs describe-tasks --cluster image-similarity-cluster --tasks {} --region $REGION --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value' --output text)

echo "Qdrant IP: $QDRANT_IP"

echo "Step 3: Building and deploying backend with full features..."
cd ../backend

docker build -t image-similarity-backend:full .

echo "Pushing to ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

docker tag image-similarity-backend:full $ECR_BACKEND:full
docker push $ECR_BACKEND:full

# Update task definition for backend
cat > /tmp/backend-full-task.json << BACKEND_EOF
{
  "family": "image-similarity-backend",
  "taskRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "executionRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "${ECR_BACKEND}:full",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "QDRANT_HOST", "value": "${QDRANT_IP}"},
        {"name": "QDRANT_PORT", "value": "6333"},
        {"name": "REDIS_HOST", "value": "${REDIS_HOST}"},
        {"name": "REDIS_PORT", "value": "6379"},
        {"name": "MODEL_NAME", "value": "openai/clip-vit-base-patch32"},
        {"name": "DEVICE", "value": "cpu"}
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/image-similarity",
          "awslogs-region": "${REGION}",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
BACKEND_EOF

cd ../aws-deploy

aws ecs register-task-definition \
  --cli-input-json file:///tmp/backend-full-task.json \
  --region $REGION

echo "Updating ECS service..."
aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --task-definition image-similarity-backend \
  --force-new-deployment \
  --region $REGION

echo "Done! Monitor deployment:"
echo "aws ecs describe-services --cluster image-similarity-cluster --services image-similarity-service --region us-west-2"
echo ""
echo "Test the API:"
echo "curl https://image-similarity-alb-691234645.us-west-2.elb.amazonaws.com/api/v1/health"
