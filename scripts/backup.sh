#!/bin/bash
# BrewStation Backup Script
# Supports both bare-metal and Docker deployments.

set -e

APP_DIR="${APP_DIR:-/opt/brewstation}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="brewstation_backup_$TIMESTAMP.tar.gz"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# ---------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ---------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------
detect_environment() {
    if command -v docker &>/dev/null && docker inspect brewstation-db &>/dev/null 2>&1; then
        echo "docker"
        return
    fi
    echo "bare-metal"
}

# ---------------------------------------------------------------
# Backup: Bare-metal
# ---------------------------------------------------------------
backup_baremetal() {
    log_info "Creating bare-metal backup..."

    # Directories to backup
    BACKUP_PATHS=()
    [ -d "$APP_DIR/.env" ] || [ -f "$APP_DIR/.env" ] && BACKUP_PATHS+=(".env")
    [ -d "$APP_DIR/instance" ] && BACKUP_PATHS+=("instance")
    [ -d "$APP_DIR/logs" ] && BACKUP_PATHS+=("logs")
    [ -d "$APP_DIR/src/uploads" ] && BACKUP_PATHS+=("src/uploads")
    [ -d "$APP_DIR/src/plugins/plugin_device_manager/data/devices" ] && BACKUP_PATHS+=("src/plugins/plugin_device_manager/data/devices")

    if [ ${#BACKUP_PATHS[@]} -eq 0 ]; then
        log_warn "No backup paths found at $APP_DIR"
        exit 0
    fi

    # Create backup
    mkdir -p "$BACKUP_DIR"
    tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
        --exclude="venv" \
        --exclude=".venv" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        --exclude=".git" \
        --exclude="backups" \
        -C "$APP_DIR" \
        "${BACKUP_PATHS[@]}"

    log_ok "Backup created: $BACKUP_DIR/$BACKUP_FILE"
}

# ---------------------------------------------------------------
# Backup: Docker — also dump PostgreSQL
# ---------------------------------------------------------------
backup_docker() {
    log_info "Creating Docker backup..."

    mkdir -p "$BACKUP_DIR"

    # Backup environment file
    if [ -f "$APP_DIR/.env" ]; then
        cp "$APP_DIR/.env" "$BACKUP_DIR/.env.$TIMESTAMP"
        log_ok "Saved .env"
    fi

    # Dump PostgreSQL database
    if docker inspect brewstation-db &>/dev/null 2>&1; then
        log_info "Dumping PostgreSQL database..."
        docker exec brewstation-db pg_dump -U "${NEON_USER:-brewstation}" "${NEON_DATABASE:-brewstation}" \
            > "$BACKUP_DIR/database_$TIMESTAMP.sql" 2>/dev/null || \
        log_warn "Database dump failed. Check database credentials."
        log_ok "Database dump saved"
    fi

    # Backup Docker volumes to tar files
    for volume in brewstation_uploads brewstation_logs brewstation_instance brewstation_configs; do
        if docker volume inspect "$volume" &>/dev/null 2>&1; then
            log_info "Backing up volume: $volume..."
            docker run --rm -v "$volume:/data" -v "$BACKUP_DIR:/backup" alpine \
                tar -czf "/backup/${volume}_$TIMESTAMP.tar.gz" -C /data . || \
            log_warn "Failed to backup volume $volume"
        fi
    done

    # Create a single archive of everything
    log_info "Creating consolidated backup archive..."
    cd "$BACKUP_DIR"
    tar -czf "$BACKUP_FILE" \
        ".env.$TIMESTAMP" \
        "database_$TIMESTAMP.sql" \
        brewstation_*_$TIMESTAMP.tar.gz \
        2>/dev/null || true

    log_ok "Consolidated backup: $BACKUP_DIR/$BACKUP_FILE"

    # Clean up temporary files
    rm -f "$BACKUP_DIR/.env.$TIMESTAMP" \
          "$BACKUP_DIR/database_$TIMESTAMP.sql" \
          "$BACKUP_DIR/brewstation_"*"_$TIMESTAMP.tar.gz"
}

# ---------------------------------------------------------------
# Cleanup old backups
# ---------------------------------------------------------------
cleanup_old_backups() {
    log_info "Removing backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "brewstation_backup_*.tar.gz" -type f -mtime "+$RETENTION_DAYS" -delete
    log_ok "Cleanup complete."
}

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
main() {
    echo ""
    echo "======================================"
    echo "  BrewStation Backup"
    echo "======================================"
    echo ""
    log_info "Timestamp: $TIMESTAMP"
    log_info "Backup dir: $BACKUP_DIR"

    ENV=$(detect_environment)
    log_info "Detected environment: $ENV"

    case "$ENV" in
        docker)
            backup_docker
            ;;
        bare-metal)
            backup_baremetal
            ;;
        *)
            log_error "Unknown environment."
            exit 1
            ;;
    esac

    cleanup_old_backups

    # Show result
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        local size=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
        log_ok "Backup file: $BACKUP_DIR/$BACKUP_FILE ($size)"
    fi

    echo ""
    log_ok "Backup complete!"
    echo ""
}

main "$@"
