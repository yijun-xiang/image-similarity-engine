#!/bin/bash
REDIS_ENDPOINT=$(aws elasticache create-cache-cluster \
  --cache-cluster-id image-similarity-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --region us-west-2 \
  --security-group-ids sg-0fc2ebdd6f6730e65 \
  --query 'CacheCluster.CacheClusterId' \
  --output text)

echo "Waiting for Redis..."
sleep 60

aws elasticache describe-cache-clusters \
  --cache-cluster-id image-similarity-redis \
  --show-cache-node-info \
  --region us-west-2 \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text
