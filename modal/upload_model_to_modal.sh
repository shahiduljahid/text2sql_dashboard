#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$ROOT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PY" ]]; then
  echo "Backend venv python not found at $VENV_PY"
  exit 1
fi

cd "$ROOT_DIR"

if ! "$VENV_PY" -c "import modal" >/dev/null 2>&1; then
  "$VENV_PY" -m pip install --upgrade pip
  "$VENV_PY" -m pip install modal
fi

if ! "$VENV_PY" -m modal profile current >/dev/null 2>&1; then
  echo "Modal auth is not configured. Run:"
  echo "  $VENV_PY -m modal setup"
  exit 1
fi

VOLUME_NAME="${MODAL_VOLUME_NAME:-text2sql-model-cache}"
BASE_LOCAL="${BASE_MODEL_LOCAL_PATH:-$ROOT_DIR/hub/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/c03e6d358207e414f1eca0bb1891e29f1db0e242}"
ADAPTER_LOCAL="${ADAPTER_LOCAL_PATH:-$ROOT_DIR/spider1_qlora_latest}"

if [[ ! -d "$BASE_LOCAL" ]]; then
  echo "Base model path not found: $BASE_LOCAL"
  exit 1
fi

if [[ ! -d "$ADAPTER_LOCAL" ]]; then
  echo "Adapter path not found: $ADAPTER_LOCAL"
  exit 1
fi

echo "Creating/ensuring volume: $VOLUME_NAME"
"$VENV_PY" -m modal volume create "$VOLUME_NAME" >/dev/null 2>&1 || true

echo "Uploading base model to /base ..."
"$VENV_PY" -m modal volume put "$VOLUME_NAME" "$BASE_LOCAL" /base

echo "Uploading adapter to /adapter ..."
"$VENV_PY" -m modal volume put "$VOLUME_NAME" "$ADAPTER_LOCAL" /adapter

echo "Upload complete."
echo "Run deploy script next: ./modal/deploy_modal.sh"
