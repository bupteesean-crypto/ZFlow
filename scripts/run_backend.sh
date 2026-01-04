#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/backend"

# Placeholder for local API development.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
