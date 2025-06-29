#!/bin/bash

aws elasticache create-cache-cluster \
  --cache-cluster-id image-similarity-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --region us-west-2 \
  --security-group-ids $(aws cloudformation describe-stacks --stack-name image-similarity-stack --query "Stacks[0].Outputs[?OutputKey=='SecurityGroup'].OutputValue" --output text --region us-west-2)

echo "Redis cluster creating..."
echo "Get endpoint with:"
echo "aws elasticache describe-cache-clusters --cache-cluster-id image-similarity-redis --show-cache-node-info --region us-west-2 --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' --output text"
