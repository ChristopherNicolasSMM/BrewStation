#!/bin/bash
# BrewStation Start Script (bare-metal)
# Starts the Flask application with gunicorn inside the virtual environment.
# This script is installed at /usr/local/bin/start_brewstation.sh by install.sh.

set -e

APP_DIR="${APP_DIR:-/opt/brewstation}"
VENV_DIR="${VENV_DIR:-$APP_DIR/venv}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-5000}"
WORKERS="${WORKERS:-4}"
LOG_DIR="$APP_DIR/logs"

# Source the .env file if it exists
if [ -f "$APP_DIR/src/.env" ]; then
    set -a
    source "$APP_DIR/src/.env"
    set +a
fi

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Start the application
cd "$APP_DIR"
exec gunicorn \
    --bind "$HOST:$PORT" \
    --workers "$WORKERS" \
    --timeout 120 \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$LOG_DIR/error.log" \
    --pid "$APP_DIR/brewstation.pid" \
    "main:create_app()"
