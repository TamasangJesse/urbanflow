#!/usr/bin/env bash
# =============================================================
# UrbanFlow — Rollback script
# Usage: ./scripts/rollback.sh [revision]
# =============================================================
set -euo pipefail

RELEASE_NAME="urbanflow"
NAMESPACE="urbanflow"
REVISION="${1:-}"

echo "============================================="
echo "  UrbanFlow — Rollback"
echo "============================================="

echo ""
echo "[INFO] Helm release history:"
helm history "$RELEASE_NAME" -n "$NAMESPACE"

if [[ -n "$REVISION" ]]; then
  echo "[INFO] Rolling back to revision $REVISION..."
  helm rollback "$RELEASE_NAME" "$REVISION" -n "$NAMESPACE" --wait --timeout 5m
else
  echo "[INFO] Rolling back to previous revision..."
  helm rollback "$RELEASE_NAME" -n "$NAMESPACE" --wait --timeout 5m
fi

echo ""
echo "[SUCCESS] Rollback complete."
kubectl get pods -n "$NAMESPACE"
