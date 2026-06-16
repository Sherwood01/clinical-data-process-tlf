#!/bin/bash
# ───────────────────────────────────────────────────────
# Deploy Stack Auth to Cloud Run (with Neon PostgreSQL)
# ───────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${1:-}"
STACK_DB_URL="${2:-}"
if [ -z "$PROJECT_ID" ] || [ -z "$STACK_DB_URL" ]; then
  echo "Usage: $0 <gcp-project-id> <stack-auth-neon-connection-string>"
  echo ""
  echo "Stack Auth needs its own Neon database. Create a separate Neon project"
  echo "and pass its connection string as the second argument."
  exit 1
fi

REGION="us-central1"
IMAGE="stackauth/server:latest"

echo "=== Deploying Stack Auth to Cloud Run ==="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"

# Pull the pre-built image and push to Artifact Registry
docker pull "$IMAGE"
docker tag "$IMAGE" "$REGION-docker.pkg.dev/$PROJECT_ID/tlf-repo/stack-auth:latest"
docker push "$REGION-docker.pkg.dev/$PROJECT_ID/tlf-repo/stack-auth:latest"

echo "=== Deploying to Cloud Run ==="
gcloud run deploy tlf-stack-auth \
  --image="$REGION-docker.pkg.dev/$PROJECT_ID/tlf-repo/stack-auth:latest" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --port=8102 \
  --set-env-vars=" \
    NEXTAUTH_SECRET=$(openssl rand -hex 32), \
    STACK_DATABASE_CONNECTION_STRING=$STACK_DB_URL, \
    STACK_PUBLISHABLE_KEY=placeholder, \
    STACK_PROJECT_ID=internal, \
    NODE_ENV=production \
  "

echo ""
echo "=== Stack Auth deployed successfully ==="
echo "Service URL: https://tlf-stack-auth-xxxxx-uc.a.run.app"
