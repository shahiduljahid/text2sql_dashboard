#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "Backend venv python not found at $VENV_PY"
  exit 1
fi

cd "$ROOT_DIR"

# Install modal CLI/sdk in backend venv if missing.
if ! "$VENV_PY" -c "import modal" >/dev/null 2>&1; then
  "$VENV_PY" -m pip install --upgrade pip
  "$VENV_PY" -m pip install modal
fi

if ! "$VENV_PY" -m modal profile current >/dev/null 2>&1; then
  echo "Modal auth is not configured. Run:"
  echo "  $VENV_PY -m modal setup"
  exit 1
fi

export MODAL_APP_NAME="${MODAL_APP_NAME:-text2sql-sql-endpoint}"
export MODAL_VOLUME_NAME="${MODAL_VOLUME_NAME:-text2sql-model-cache}"
export MODAL_GPU="${MODAL_GPU:-A10G}"
export MODAL_BASE_MODEL_DIR="${MODAL_BASE_MODEL_DIR:-/models/base}"
export MODAL_ADAPTER_DIR="${MODAL_ADAPTER_DIR:-/models/adapter}"

echo "Deploying Modal app..."
"$VENV_PY" -m modal deploy modal/modal_sql_endpoint.py

echo "Deployment command completed."
echo "Get endpoint URLs from Modal deploy output or dashboard."
