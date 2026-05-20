#!/bin/bash
# BrewStation Healthcheck (bare-metal)
# Returns 0 if the application is healthy, 1 otherwise.

APP_DIR="${APP_DIR:-/opt/brewstation}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5000}"
HEALTH_URL="${HEALTH_URL:-http://$HOST:$PORT/}"

# Check if the process is running
if [ -f "$APP_DIR/brewstation.pid" ]; then
    PID=$(cat "$APP_DIR/brewstation.pid")
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "Process not running (PID $PID)"
        exit 1
    fi
else
    echo "PID file not found"
    # Try to find the process anyway
    PID=$(pgrep -f "gunicorn.*main:create_app" | head -1)
    if [ -z "$PID" ]; then
        echo "No gunicorn process found"
        exit 1
    fi
fi

# Check if the HTTP endpoint is responding
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
if [ "$STATUS" = "000" ]; then
    echo "HTTP endpoint not responding"
    exit 1
elif [ "$STATUS" -ge 200 ] && [ "$STATUS" -lt 500 ]; then
    echo "Healthy (HTTP $STATUS)"
    exit 0
else
    echo "Unhealthy (HTTP $STATUS)"
    exit 1
fi
