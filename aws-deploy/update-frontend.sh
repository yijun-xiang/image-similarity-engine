#!/bin/bash
cd frontend
npm run build
aws s3 sync dist/ s3://image-search-frontend-1751183489 --delete
aws cloudfront create-invalidation --distribution-id E1QUZW4OA6KUSN --paths "/*"
cd ..
