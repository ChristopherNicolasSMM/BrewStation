#!/bin/bash
# BrewStation Docker Entrypoint
# Handles DB initialization and starts the application

set -e

APP_DIR="${APP_DIR:-/opt/brewstation}"
cd "$APP_DIR"

# Function to wait for PostgreSQL
wait_for_postgres() {
    if [ -n "$DATABASE_URL" ]; then
        # Extract host and port from DATABASE_URL
        local db_host=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:/]*\).*|\1|p')
        local db_port=$(echo "$DATABASE_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
        db_port="${db_port:-5432}"

        if [ -n "$db_host" ]; then
            echo "Waiting for PostgreSQL at $db_host:$db_port..."
            local retries=30
            while [ $retries -gt 0 ]; do
                if curl -s "http://$db_host:$db_port" >/dev/null 2>&1 || \
                   python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('$db_host', $db_port)); s.close()" 2>/dev/null; then
                    echo "PostgreSQL is available."
                    return 0
                fi
                echo "  Waiting... ($retries retries left)"
                retries=$((retries - 1))
                sleep 2
            done
            echo "WARNING: PostgreSQL did not become available in time. Starting anyway."
        fi
    fi
}

# Wait for the database
wait_for_postgres

# Initialize the database
echo "Running database initialization..."
python3 -c "
from main import create_app
app = create_app()
with app.app_context():
    from db.database import init_db
    init_db(app)
    print('Database initialized successfully.')
" || echo "WARNING: Database initialization failed (may already exist or will be created on first request)."

# Run migrations if they exist
if [ -f "scripts/migrate.sh" ]; then
    echo "Running database migrations..."
    bash scripts/migrate.sh || echo "WARNING: Migration script failed."
fi

echo "Starting BrewStation..."
exec "$@"
