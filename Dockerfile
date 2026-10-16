# ==============================================================================
# AgriLens Production Dockerfile
# Target Image: ndoli/agrilens:latest
# Host Domain: agrilens.ndoli.dev
# 2026 NISR Big Data Hackathon – Track 1: Agricultural Productivity
# ==============================================================================

FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    WEB_CONCURRENCY=3 \
    DJANGO_SETTINGS_MODULE=config.settings

# Working directory
WORKDIR /app

# Install runtime dependencies (curl for healthcheck, libpq5 for PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements-prod.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# Copy source code
COPY . /app/

# Ensure entrypoint line endings & executable permissions
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Create static, media, and data directories
RUN mkdir -p /app/staticfiles /app/media /app/data

# Collect static assets into staticfiles
RUN python manage.py collectstatic --noinput

# Expose application port
EXPOSE 8000

# Docker healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--worker-class", "gthread", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
