#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/worker"

# Placeholder for local worker development.
python "$ROOT_DIR/worker/worker.py"
