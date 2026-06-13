#!/bin/bash
# DiabetesControl AI Expert - Full Deployment Script
# Usage: ./scripts/deploy.sh [region]
# Example: ./scripts/deploy.sh us-east-1

set -e

REGION="${1:-us-east-1}"
STACK_NAME="diabetes-care-agent"

echo ""
echo "🩺 DiabetesControl AI Expert - Deployment"
echo "=========================================="
echo "Region: $REGION"
echo "Stack:  $STACK_NAME"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Install it from:"
    echo "   https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install it from:"
    echo "   https://aws.amazon.com/cli/"
    exit 1
fi

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python 3.11+ not found."
    exit 1
fi

echo "  ✓ All prerequisites met"

# Step 1: Build
echo ""
echo "🔨 Building SAM application..."
sam build --region "$REGION"
echo "  ✓ Build complete"

# Step 2: Deploy
echo ""
echo "🚀 Deploying to AWS..."
sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --no-confirm-changeset \
    --parameter-overrides "BedrockAgentId= BedrockAgentAliasId="

echo "  ✓ SAM deployment complete"

# Step 3: Get outputs
echo ""
echo "📎 Retrieving stack outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

TOOLS_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DiabetesToolsFunctionArn`].OutputValue' \
    --output text)

echo "  API URL:    $API_URL"
echo "  Tools ARN:  $TOOLS_ARN"

# Step 4: Setup Bedrock Agent
echo ""
echo "🤖 Setting up Bedrock Agent..."
python3 scripts/setup_agent.py --region "$REGION" --stack-name "$STACK_NAME"

echo ""
echo "=========================================="
echo "✅ Deployment complete!"
echo ""
echo "API Endpoint: $API_URL"
echo ""
echo "Update frontend/config.js with:"
echo "  API_ENDPOINT: \"$API_URL\""
echo ""
