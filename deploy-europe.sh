#!/bin/bash
set -e

# Deploy Polymarket Agent to GCP Cloud Run (Europe)
# Usage: ./deploy-europe.sh

PROJECT_ID="avian-voice-476622-r8"
REGION="europe-west1"
SERVICE_NAME="polymarket-agent"

echo "=========================================="
echo "Deploying Polymarket Agent to Europe"
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
    --set-env-vars "BLOCKRUN_WALLET_KEY=$BLOCKRUN_WALLET_KEY" \
    --set-env-vars "POLYGON_WALLET_PRIVATE_KEY=$POLYGON_WALLET_PRIVATE_KEY" \
    --set-env-vars "FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-polymarket-agent-secret}" \
    --set-env-vars "ADMIN_USER=${ADMIN_USER:-admin}" \
    --set-env-vars "ADMIN_PASS=${ADMIN_PASS:-polymarket2024}"

# Get URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "URL: $SERVICE_URL"
echo "=========================================="
echo ""
echo "Open in browser to control the agent"
