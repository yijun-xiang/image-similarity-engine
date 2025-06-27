#!/bin/bash
docker run -d \
  --name image-similarity-backend \
  -p 8001:8000 \
  -e QDRANT_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  image-similarity-backend:latest
