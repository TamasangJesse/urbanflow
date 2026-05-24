#!/usr/bin/env bash
# =============================================================
# UrbanFlow — Cleanup (WARNING: destructive)
# Usage: ./scripts/cleanup.sh [--delete-pvc]
# =============================================================
set -euo pipefail

RELEASE_NAME="urbanflow"
NAMESPACE="urbanflow"
DELETE_PVC=false

for arg in "$@"; do
  [[ "$arg" == "--delete-pvc" ]] && DELETE_PVC=true
done

echo "============================================="
echo "  UrbanFlow — Cleanup"
echo "  WARNING: This will delete all resources!"
echo "============================================="
read -rp "  Type 'yes' to confirm: " CONFIRM
[[ "$CONFIRM" != "yes" ]] && echo "Aborted." && exit 0

echo "[INFO] Uninstalling Helm release..."
helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" || true

if [[ "$DELETE_PVC" == true ]]; then
  echo "[WARN] Deleting PersistentVolumeClaims (data will be lost)..."
  kubectl delete pvc --all -n "$NAMESPACE" || true
fi

echo "[INFO] Deleting namespace $NAMESPACE..."
kubectl delete namespace "$NAMESPACE" --ignore-not-found

echo "[SUCCESS] Cleanup complete."
