#!/bin/bash

REGION="us-west-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws ecr create-repository \
    --repository-name image-similarity-backend \
    --region $REGION

aws ecr create-repository \
    --repository-name image-similarity-frontend \
    --region $REGION

echo "ECR Login:"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "Backend repository: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-backend"
echo "Frontend repository: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/image-similarity-frontend"
