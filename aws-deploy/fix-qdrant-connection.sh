#!/bin/bash
REGION="us-west-2"
ACCOUNT_ID="035711439189"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity"

# Get Redis endpoint
REDIS_HOST=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id image-similarity-redis \
  --show-cache-node-info \
  --region $REGION \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)

# Get Qdrant IP
QDRANT_TASK=$(aws ecs list-tasks --cluster image-similarity-cluster --service-name qdrant-service --region $REGION --query 'taskArns[0]' --output text)
QDRANT_IP=$(aws ecs describe-tasks --cluster image-similarity-cluster --tasks $QDRANT_TASK --region $REGION --query 'tasks[0].attachments[0].details[?name==`privateIPv4Address`].value' --output text)

echo "Qdrant IP: $QDRANT_IP"
echo "Redis Host: $REDIS_HOST"

# Create new task definition
cat > /tmp/backend-task-fixed.json << TASKDEF
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
      "image": "${ECR_URI}:latest",
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
TASKDEF

# Register and update
TASK_DEF_ARN=$(aws ecs register-task-definition \
  --cli-input-json file:///tmp/backend-task-fixed.json \
  --region $REGION \
  --query 'taskDefinition.taskDefinitionArn' \
  --output text)

aws ecs update-service \
  --cluster image-similarity-cluster \
  --service image-similarity-service \
  --task-definition $TASK_DEF_ARN \
  --force-new-deployment \
  --region $REGION
