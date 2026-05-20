# BrewStation Dockerfile
# Multi-stage build: development dependencies in build stage, production only in final

# ============================================================
# STAGE 1: Build / Install Dependencies
# ============================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies (for psycopg2, cryptography, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libffi-dev \
        python3-dev \
        musl-dev \
        && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt


# ============================================================
# STAGE 2: Runtime Image
# ============================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_DIR=/opt/brewstation \
    HOST=0.0.0.0 \
    PORT=5000 \
    DEBUG=False \
    FLASK_ENV=PRD \
    HTTPS=False

WORKDIR $APP_DIR

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        curl \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# Create brewstation user (non-root)
RUN groupadd -r brewstation && \
    useradd -r -g brewstation -d $APP_DIR -s /bin/bash brewstation && \
    mkdir -p $APP_DIR/logs $APP_DIR/instance $APP_DIR/backups && \
    chown -R brewstation:brewstation $APP_DIR

# Copy installed Python packages from builder
COPY --from=builder /root/.local /usr/local

# Copy application source
COPY --chown=brewstation:brewstation run.py main.py ./
COPY --chown=brewstation:brewstation src/ src/
COPY --chown=brewstation:brewstation scripts/ scripts/
COPY --chown=brewstation:brewstation scripts/entrypoint.sh /entrypoint.sh

# Create required directories and set permissions
RUN mkdir -p $APP_DIR/src/uploads && \
    chmod +x /entrypoint.sh && \
    chown -R brewstation:brewstation $APP_DIR

# Expose port
EXPOSE 5000

# Switch to non-root user
USER brewstation

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/ >/dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "main:create_app()"]
