#!/bin/bash
# ───────────────────────────────────────────────────────
# TLF Report Generator — GCP Cloud Run 一键部署脚本
# 用法: ./scripts/deploy.sh [project-id]
# ───────────────────────────────────────────────────────
set -euo pipefail

PROJECT_ID="${1:-}"
if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <gcp-project-id>"
  exit 1
fi

REGION="us-central1"
REPO="tlf-repo"
SHORT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

# ── 0. GCloud 配置 ──
gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"

# ── 1. 启用必需 API ──
echo "=== Enabling required APIs ==="
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com

# ── 2. 创建 Artifact Registry 仓库 ──
echo "=== Creating Artifact Registry repo ==="
gcloud artifacts repositories describe "$REPO" --location="$REGION" 2>/dev/null || \
  gcloud artifacts repositories create "$REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="TLF Report Generator images"

# ── 3. 构建并推送 Docker 镜像 ──
echo "=== Building images ==="
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_REGION="$REGION",_ARTIFACT_REPO="$REPO",SHORT_SHA="$SHORT_SHA" \
  --project="$PROJECT_ID"

# ── 4. 输出部署信息 ──
echo ""
echo "=== Deploy Summary ==="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo "Images:  $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/tlf-{api,worker,frontend}:$SHORT_SHA"
echo ""
echo "Next steps:"
echo "  1. Register Upstash Redis (free tier) — https://console.upstash.com"
echo "  2. Run database migrations on Neon:"
echo "     gcloud run deploy tlf-migrate --image=... --command=alembic -- upgrade head"
echo ""
echo "  3. Deploy Stack Auth separately:"
echo "     ./cloudbuild/deploy-stack-auth.sh $PROJECT_ID"
echo ""
echo "  4. Configure custom domain or use the Cloud Run URLs above"
