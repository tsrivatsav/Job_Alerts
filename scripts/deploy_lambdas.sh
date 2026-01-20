#!/bin/bash

# Configuration
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
SNS_TOPIC_ARN="arn:aws:sns:${REGION}:${ACCOUNT_ID}:job-scraper-notifications"

echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo "SNS Topic ARN: $SNS_TOPIC_ARN"

# Create deployment directory
mkdir -p ../dist

# ============================================
# Deploy Orchestrator Lambda
# ============================================
echo ""
echo "📦 Packaging orchestrator Lambda..."

cd ../lambdas/orchestrator

# Install dependencies
pip install -r requirements.txt -t package/
cp lambda_function.py package/

# Create zip
cd package
zip -r ../../../dist/orchestrator.zip .
cd ..
rm -rf package

# Create/Update Lambda
echo "🚀 Deploying orchestrator Lambda..."

aws lambda create-function \
    --function-name job-scraper-orchestrator \
    --runtime python3.9 \
    --handler lambda_function.lambda_handler \
    --role "arn:aws:iam::${ACCOUNT_ID}:role/job-scraper-orchestrator-role" \
    --zip-file fileb://../../dist/orchestrator.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment "Variables={COMPANIES_TABLE=job_scraper_companies,SCRAPER_FUNCTION=job-scraper-function}" \
    --region $REGION \
    2>/dev/null

if [ $? -ne 0 ]; then
    echo "Function exists, updating..."
    aws lambda update-function-code \
        --function-name job-scraper-orchestrator \
        --zip-file fileb://../../dist/orchestrator.zip \
        --region $REGION
fi

echo "✅ Orchestrator deployed"

# ============================================
# Deploy Scraper Lambda
# ============================================
echo ""
echo "📦 Packaging scraper Lambda..."

cd ../scraper

# Install dependencies
pip install -r requirements.txt -t package/
cp lambda_function.py package/

# Create zip
cd package
zip -r ../../../dist/scraper.zip .
cd ..
rm -rf package

# Create/Update Lambda
echo "🚀 Deploying scraper Lambda..."

aws lambda create-function \
    --function-name job-scraper-function \
    --runtime python3.9 \
    --handler lambda_function.lambda_handler \
    --role "arn:aws:iam::${ACCOUNT_ID}:role/job-scraper-scraper-role" \
    --zip-file fileb://../../dist/scraper.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment "Variables={JOBS_TABLE=job_scraper_jobs,SNS_TOPIC_ARN=${SNS_TOPIC_ARN}}" \
    --region $REGION \
    2>/dev/null

if [ $? -ne 0 ]; then
    echo "Function exists, updating..."
    aws lambda update-function-code \
        --function-name job-scraper-function \
        --zip-file fileb://../../dist/scraper.zip \
        --region $REGION
fi

echo "✅ Scraper deployed"

cd ../../scripts
echo ""
echo "🎉 All Lambdas deployed successfully!"