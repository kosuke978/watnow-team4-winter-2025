#!/usr/bin/env bash
set -euo pipefail

gcloud run deploy signaling-server \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars ENABLE_MDNS=false \
  --session-affinity \
  --min-instances 0 \
  --max-instances 2 \
  --timeout 300
