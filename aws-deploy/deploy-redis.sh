#!/bin/bash
set -e

REGION="us-west-2"
CACHE_ID="image-similarity-redis"
SUBNET_GROUP="image-similarity-subnet-group"

aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name $SUBNET_GROUP \
  --subnet-ids subnet-068efec545b9458f8 subnet-02c7194e01eed748c \
  --cache-subnet-group-description "Subnet group for image similarity redis" \
  --region $REGION

aws elasticache create-replication-group \
  --replication-group-id $CACHE_ID \
  --replication-group-description "Redis for image similarity engine" \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-clusters 1 \
  --cache-subnet-group-name $SUBNET_GROUP \
  --security-group-ids sg-0fc2ebdd6f6730e65 \
  --region $REGION

echo "Waiting for Redis to be available..."
aws elasticache wait cache-cluster-available \
  --cache-cluster-id $CACHE_ID-001 \
  --region $REGION

REDIS_ENDPOINT=$(aws elasticache describe-replication-groups \
  --replication-group-id $CACHE_ID \
  --region $REGION \
  --query 'ReplicationGroups[0].NodeGroups[0].PrimaryEndpoint.Address' \
  --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"
