#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Starting Voice Clone server..."
echo "Project: $(pwd)"
echo "URL: http://127.0.0.1:8010"

export NUMBA_CACHE_DIR="${NUMBA_CACHE_DIR:-/private/tmp/voice_clone_numba_cache}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/private/tmp/voice_clone_mpl_cache}"
mkdir -p "$NUMBA_CACHE_DIR" "$MPLCONFIGDIR"

if command -v conda >/dev/null 2>&1; then
  echo "Using conda environment: cosyvoice"
  conda run --no-capture-output -n cosyvoice uvicorn backend.main:app --host 127.0.0.1 --port 8010
else
  echo "Conda not found, using current Python environment"
  uvicorn backend.main:app --host 127.0.0.1 --port 8010
fi
