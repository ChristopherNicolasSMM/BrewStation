#!/usr/bin/env bash
set -euo pipefail

APP_USER="brewstation"
APP_DIR="/opt/brewstation"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="brewstation"

if [[ "$EUID" -ne 0 ]]; then
  echo "Execute como root: sudo ./update.sh"
  exit 1
fi

cd "$APP_DIR"
sudo -u "$APP_USER" git pull --ff-only
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r requirements.txt
systemctl restart "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager
