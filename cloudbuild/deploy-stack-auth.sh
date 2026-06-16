#!/bin/bash
# ───────────────────────────────────────────────────────
# Deploy Stack Auth to Cloud Run
# ───────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${1:-}"
if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <gcp-project-id>"
  exit 1
fi

REGION="us-central1"
IMAGE="stackauth/server:latest"

echo "=== Deploying Stack Auth to Cloud Run ==="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"

# Pull the pre-built image and push to Artifact Registry
# (Stack Auth doesn't have an official ARM64 image for GCP)
docker pull "$IMAGE"
docker tag "$IMAGE" "$REGION-docker.pkg.dev/$PROJECT_ID/tlf-repo/stack-auth:latest"
docker push "$REGION-docker.pkg.dev/$PROJECT_ID/tlf-repo/stack-auth:latest"

echo "=== Creating Cloud SQL database for Stack Auth ==="
gcloud sql databases create stack-auth \
  --instance=tlf-postgres 2>/dev/null || echo "Database 'stack-auth' already exists"

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
  --add-cloudsql-instances="$PROJECT_ID:$REGION:tlf-postgres" \
  --set-env-vars=" \
    NEXTAUTH_SECRET=$(openssl rand -hex 32), \
    STACK_DATABASE_CONNECTION_STRING=postgresql://postgres:postgres@/stack-auth?host=/cloudsql/$PROJECT_ID:$REGION:tlf-postgres, \
    STACK_PUBLISHABLE_KEY=placeholder, \
    STACK_PROJECT_ID=internal, \
    NODE_ENV=production \
  "

echo ""
echo "=== Stack Auth deployed successfully ==="
echo "Service URL: https://tlf-stack-auth-xxxxx-uc.a.run.app"
