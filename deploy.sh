#!/bin/bash
cd frontend
npm run build
aws s3 sync dist/ s3://'$BUCKET_NAME' --delete
aws cloudfront create-invalidation --distribution-id '$CLOUDFRONT_DIST' --paths "/*"
