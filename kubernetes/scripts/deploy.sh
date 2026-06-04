#!/usr/bin/env bash
# =============================================================
# UrbanFlow — Deploy script for k3s
# Usage: ./scripts/deploy.sh [--dry-run]
# Run from the urbanflow/ root directory
# =============================================================
set -euo pipefail

CHART_PATH="./kubernetes/helm/urbanflow"
RELEASE_NAME="urbanflow"
NAMESPACE="urbanflow"

echo "============================================="
echo "  UrbanFlow — Kubernetes Deployment (k3s)"
echo "  Release : $RELEASE_NAME"
echo "  NS      : $NAMESPACE"
echo "============================================="

DRY_RUN=""
for arg in "$@"; do
  [[ "$arg" == "--dry-run" ]] && DRY_RUN="--dry-run"
done

# -- Verify cluster is reachable
echo ""
echo "[INFO] Cluster nodes:"
kubectl get nodes

# -- Import app images into k3s containerd
# k3s uses its own containerd, separate from Docker daemon
# Image names match exactly what 'docker images | grep urbanflow' shows
echo ""
echo "[INFO] Importing local Docker images into k3s containerd..."

APP_IMAGES=(
  "urbanflow-frontend"
  "urbanflow-api-gateway"
  "urbanflow-user-service"
  "urbanflow-incident-report-service"
  "urbanflow-notification-service"
  "urbanflow-traffic-intelligence-service"
  "urbanflow-rag-service"
)

for img in "${APP_IMAGES[@]}"; do
  echo "  → $img:latest"
  docker save "$img:latest" | sudo k3s ctr images import -
done

echo ""
echo "[INFO] Images now available in k3s:"
sudo k3s ctr images list | grep urbanflow

# -- Create namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# -- Helm deploy
echo ""
echo "[INFO] Running helm upgrade --install..."
helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
  --namespace "$NAMESPACE" \
  --atomic \
  --timeout 10m \
  $DRY_RUN

echo ""
echo "[SUCCESS] Deployment complete!"
echo ""
echo "--- Pods ---"
kubectl get pods -n "$NAMESPACE"
echo ""
echo "--- Services ---"
kubectl get svc -n "$NAMESPACE"
echo ""
echo "--- Ingress ---"
kubectl get ingress -n "$NAMESPACE"
echo ""
echo "Jenkins UI: http://$(curl -s ifconfig.me):32080"
