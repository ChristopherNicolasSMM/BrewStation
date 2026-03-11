#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/brewstation"
VENV_PY="$APP_DIR/venv/bin/python"

cd "$APP_DIR"
exec "$VENV_PY" "$APP_DIR/run.py" start
