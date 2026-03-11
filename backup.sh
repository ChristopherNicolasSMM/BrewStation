#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/brewstation"
BACKUP_DIR="$APP_DIR/backups"
STAMP="$(date +%Y%m%d_%H%M%S)"
TARGET="$BACKUP_DIR/brewstation_backup_${STAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

tar \
  --exclude="$APP_DIR/venv" \
  --exclude="$APP_DIR/.git" \
  --exclude="$APP_DIR/backups" \
  -czf "$TARGET" \
  "$APP_DIR/src/.env" \
  "$APP_DIR/src/instance" \
  "$APP_DIR/logs" \
  "$APP_DIR/src/static/uploads" \
  2>/dev/null || true

echo "Backup criado em: $TARGET"
