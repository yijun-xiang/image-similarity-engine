#!/bin/bash

REGION="us-west-2"
CACHE_ID="image-similarity-redis"

echo "Creating ElastiCache Redis cluster..."
aws elasticache create-cache-cluster \
  --cache-cluster-id $CACHE_ID \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --region $REGION \
  --security-group-ids sg-0fc2ebdd6f6730e65

echo "Waiting for Redis to be available..."
aws elasticache wait cache-cluster-available \
  --cache-cluster-id $CACHE_ID \
  --region $REGION

REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id $CACHE_ID \
  --show-cache-node-info \
  --region $REGION \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"
echo "Save this endpoint for your configuration!"
