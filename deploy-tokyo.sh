#!/bin/bash
set -e

# Deploy Polymarket Agent to GCP Cloud Run (Tokyo)
# Usage: ./deploy-tokyo.sh
#
# NOTE: Polymarket CLOB API geoblocks US, EU, UK, Singapore, Australia.
# Tokyo (asia-northeast1) is a non-blocked region for order placement.

PROJECT_ID="avian-voice-476622-r8"
REGION="asia-northeast1"
SERVICE_NAME="polymarket-agent"

echo "=========================================="
echo "Deploying Polymarket Agent to Tokyo"
echo "Region: $REGION"
echo "=========================================="

# Check gcloud
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud not found"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Load .env if exists
if [ -f .env ]; then
    echo "Loading .env..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Check required vars
if [ -z "$BLOCKRUN_WALLET_KEY" ]; then
    echo "Error: BLOCKRUN_WALLET_KEY not set"
    exit 1
fi

if [ -z "$POLYGON_WALLET_PRIVATE_KEY" ]; then
    echo "Error: POLYGON_WALLET_PRIVATE_KEY not set"
    exit 1
fi

echo "Deploying to Cloud Run..."

# Build env vars string
ENV_VARS="BLOCKRUN_WALLET_KEY=$BLOCKRUN_WALLET_KEY"
ENV_VARS="$ENV_VARS,POLYGON_WALLET_PRIVATE_KEY=$POLYGON_WALLET_PRIVATE_KEY"
ENV_VARS="$ENV_VARS,FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-polymarket-agent-secret}"
ENV_VARS="$ENV_VARS,ADMIN_USER=${ADMIN_USER:-admin}"
ENV_VARS="$ENV_VARS,ADMIN_PASS=${ADMIN_PASS:-polymarket2024}"

# Add Polymarket API credentials if available (recommended for production)
if [ -n "$POLYMARKET_API_KEY" ]; then
    echo "Including Polymarket API credentials..."
    ENV_VARS="$ENV_VARS,POLYMARKET_API_KEY=$POLYMARKET_API_KEY"
    ENV_VARS="$ENV_VARS,POLYMARKET_API_SECRET=$POLYMARKET_API_SECRET"
    ENV_VARS="$ENV_VARS,POLYMARKET_PASSPHRASE=$POLYMARKET_PASSPHRASE"
else
    echo "Warning: No POLYMARKET_API_KEY set. Agent will try to derive credentials at runtime."
fi

# Add Polymarket proxy wallet if set (funder address for trades)
if [ -n "$POLYMARKET_PROXY_WALLET" ]; then
    echo "Using Polymarket proxy wallet: $POLYMARKET_PROXY_WALLET"
    ENV_VARS="$ENV_VARS,POLYMARKET_PROXY_WALLET=$POLYMARKET_PROXY_WALLET"
fi

# Add Google Cloud Storage settings (optional)
if [ -n "$USE_GCS_STORAGE" ]; then
    echo "GCS Storage: $USE_GCS_STORAGE"
    ENV_VARS="$ENV_VARS,USE_GCS_STORAGE=$USE_GCS_STORAGE"
fi

if [ -n "$GCS_BUCKET_NAME" ]; then
    echo "GCS Bucket: $GCS_BUCKET_NAME"
    ENV_VARS="$ENV_VARS,GCS_BUCKET_NAME=$GCS_BUCKET_NAME"
fi

gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 1 \
    --set-env-vars "$ENV_VARS"

# Get URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "URL: $SERVICE_URL"
echo "=========================================="
echo ""
echo "Open in browser to control the agent"
