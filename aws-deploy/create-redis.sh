#!/bin/bash
set -e

REGION="us-west-2"
CACHE_ID="image-similarity-redis"
SUBNET_GROUP="image-similarity-subnet-group"

echo "Using existing subnet group: $SUBNET_GROUP"

# Check for existing cache cluster
echo "Checking for existing Redis cache cluster..."
CACHE_STATUS=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id $CACHE_ID \
  --region $REGION \
  --query 'CacheClusters[0].CacheClusterStatus' \
  --output text 2>/dev/null || echo "not-found")

if [ "$CACHE_STATUS" != "not-found" ]; then
  echo "Found existing cache cluster with status: $CACHE_STATUS"
  
  # Get endpoint from cache cluster
  REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id $CACHE_ID \
    --show-cache-node-info \
    --region $REGION \
    --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
    --output text 2>/dev/null || echo "")
    
  if [ -n "$REDIS_ENDPOINT" ] && [ "$REDIS_ENDPOINT" != "None" ]; then
    echo "Redis Endpoint: $REDIS_ENDPOINT"
    echo "export REDIS_HOST=$REDIS_ENDPOINT" > redis-endpoint.sh
    exit 0
  fi
fi

# Check for replication group
echo "Checking Redis replication group..."
REDIS_STATUS=$(aws elasticache describe-replication-groups \
  --replication-group-id $CACHE_ID \
  --region $REGION \
  --query 'ReplicationGroups[0].Status' \
  --output text 2>/dev/null || echo "not-found")

if [ "$REDIS_STATUS" == "available" ]; then
  echo "Redis replication group already exists and is available"
  
  REDIS_ENDPOINT=$(aws elasticache describe-replication-groups \
    --replication-group-id $CACHE_ID \
    --region $REGION \
    --query 'ReplicationGroups[0].NodeGroups[0].PrimaryEndpoint.Address' \
    --output text 2>/dev/null || echo "")
else
  echo "No existing Redis found, please create one manually in AWS Console"
  echo "Or use a different cache identifier"
  REDIS_ENDPOINT="create-manually"
fi

echo "Redis Endpoint: $REDIS_ENDPOINT"
echo "export REDIS_HOST=$REDIS_ENDPOINT" > redis-endpoint.sh
