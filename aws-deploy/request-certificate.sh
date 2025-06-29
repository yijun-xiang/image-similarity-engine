#!/bin/bash

REGION="us-west-2"
DOMAIN="*.yijunxiang.com"

echo "Requesting ACM certificate for $DOMAIN..."

CERTIFICATE_ARN=$(aws acm request-certificate \
    --domain-name "$DOMAIN" \
    --validation-method DNS \
    --region $REGION \
    --query CertificateArn \
    --output text)

echo "Certificate ARN: $CERTIFICATE_ARN"
echo ""
echo "Next steps:"
echo "1. Go to AWS ACM console"
echo "2. Find the certificate and click on it"
echo "3. Copy the CNAME record details"
echo "4. Add the CNAME record in GoDaddy DNS"
echo "5. Wait for validation (usually 5-30 minutes)"
echo ""
echo "To check validation status:"
echo "aws acm describe-certificate --certificate-arn $CERTIFICATE_ARN --region $REGION"
