#!/bin/bash
set -e

REGION="us-west-2"
CLUSTER="image-similarity-cluster"

aws logs create-log-group --log-group-name /ecs/qdrant --region $REGION 2>/dev/null || true

aws ecs register-task-definition \
  --cli-input-json file://aws-deploy/task-definition-qdrant.json \
  --region $REGION

aws ecs create-service \
  --cluster $CLUSTER \
  --service-name qdrant-service \
  --task-definition qdrant-service:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-068efec545b9458f8,subnet-02c7194e01eed748c],securityGroups=[sg-0fc2ebdd6f6730e65],assignPublicIp=ENABLED}" \
  --region $REGION

echo "Creating internal load balancer for Qdrant..."
QDRANT_TG_ARN=$(aws elbv2 create-target-group \
  --name qdrant-tg \
  --protocol HTTP \
  --port 6333 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-path / \
  --region $REGION \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

echo "Qdrant service deployed"
