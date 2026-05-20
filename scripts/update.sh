#!/bin/bash
# BrewStation Update Script
# Supports both bare-metal (systemd) and Docker deployments.
# Auto-detects the running environment.

set -e

APP_DIR="${APP_DIR:-/opt/brewstation}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

# ---------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ---------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------
detect_environment() {
    # Check if running inside a Docker container
    if [ -f /.dockerenv ] || grep -q docker /proc/1/cgroup 2>/dev/null; then
        echo "docker-container"
        return
    fi

    # Check if docker-compose is available and project is running
    if command -v docker &>/dev/null && command -v docker-compose &>/dev/null; then
        if docker inspect brewstation-app &>/dev/null 2>&1; then
            echo "docker-compose"
            return
        fi
    fi

    # Check if systemd service exists and is running
    if systemctl is-active --quiet brewstation 2>/dev/null; then
        echo "bare-metal"
        return
    fi

    # Default: check what's available
    if command -v docker &>/dev/null; then
        echo "docker-compose"
    else
        echo "bare-metal"
    fi
}

# ---------------------------------------------------------------
# Update: Docker Compose
# ---------------------------------------------------------------
update_docker() {
    log_info "Updating BrewStation via Docker Compose..."

    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "docker-compose.yml not found in $APP_DIR"
        exit 1
    fi

    cd "$APP_DIR"

    # Pull latest image
    log_info "Pulling latest code from git..."
    git fetch origin
    git reset --hard origin/$(git rev-parse --abbrev-ref HEAD) || git pull --ff-only

    log_info "Rebuilding and restarting containers..."
    docker-compose -f "$COMPOSE_FILE" build --pull
    docker-compose -f "$COMPOSE_FILE" up -d --remove-orphans

    # Wait for health check
    log_info "Waiting for app to become healthy..."
    sleep 5
    if docker ps --filter "name=brewstation-app" --filter "health=healthy" --format "{{.Names}}" | grep -q brewstation-app; then
        log_ok "BrewStation updated and running!"
    else
        log_warn "App may still be starting. Check with: docker-compose ps"
    fi

    # Clean up old images
    docker image prune -f
}

# ---------------------------------------------------------------
# Update: Bare-metal (systemd)
# ---------------------------------------------------------------
update_baremetal() {
    log_info "Updating BrewStation (bare-metal)..."

    cd "$APP_DIR"

    # Backup current installation
    if [ -f "scripts/backup.sh" ]; then
        log_info "Creating backup before update..."
        bash scripts/backup.sh
    elif [ -f "backup.sh" ]; then
        log_info "Creating backup before update..."
        bash backup.sh
    fi

    # Pull latest code
    log_info "Pulling latest code from git..."
    git fetch origin
    git reset --hard origin/$(git rev-parse --abbrev-ref HEAD) || git pull --ff-only

    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        log_warn "No virtual environment found. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
    fi

    # Update dependencies
    log_info "Updating Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt --no-cache-dir

    # Restart service
    log_info "Restarting BrewStation service..."
    if systemctl is-active --quiet brewstation; then
        sudo systemctl restart brewstation
        log_ok "Service restarted."
    else
        log_warn "brewstation service not found. Starting manually..."
        if [ -f "scripts/start_brewstation.sh" ]; then
            bash scripts/start_brewstation.sh
        else
            log_error "No start script found. Start manually."
        fi
    fi
}

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
main() {
    echo ""
    echo "======================================"
    echo "  BrewStation Update Script"
    echo "======================================"
    echo ""

    ENV=$(detect_environment)
    log_info "Detected environment: $ENV"

    case "$ENV" in
        docker-container)
            log_info "Running inside container — nothing to update here."
            log_info "Update from the host with: docker-compose build && docker-compose up -d"
            ;;
        docker-compose)
            update_docker
            ;;
        bare-metal)
            update_baremetal
            ;;
        *)
            log_error "Unknown environment."
            exit 1
            ;;
    esac

    echo ""
    log_ok "Update complete!"
    echo ""
}

main "$@"
