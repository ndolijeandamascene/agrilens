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
    WEB_CONCURRENCY=2 \
    DJANGO_SETTINGS_MODULE=config.settings \
    QWEN_LLM_ENABLED=True \
    QWEN_MODEL_PATH=/app/data/models/qwen2.5-3b-instruct-q4_k_m.gguf \
    QWEN_MODEL_N_CTX=2048 \
    QWEN_MODEL_N_THREADS=2 \
    DOWNLOAD_QWEN_MODEL=1 \
    CMAKE_ARGS="-DGGML_BLAS=OFF" \
    CMAKE_BUILD_PARALLEL_LEVEL=2

# Working directory
WORKDIR /app

# Install runtime & build dependencies (libpq5 for PostgreSQL, libgomp1 for OpenMP, build-essential & cmake for C/C++ builds, musl for musl-libc wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    libgomp1 \
    build-essential \
    cmake \
    musl \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Fix libc.musl-x86_64.so.1 shared library loader compatibility for libllama.so
RUN ln -sf /usr/lib/x86_64-linux-musl/libc.so /lib/libc.musl-x86_64.so.1 && \
    ln -sf /usr/lib/x86_64-linux-musl/libc.so /usr/lib/libc.musl-x86_64.so.1 || true

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
RUN mkdir -p /app/staticfiles /app/media /app/data /app/data/models

# Collect static assets into staticfiles
RUN python manage.py collectstatic --noinput

# Expose application port
EXPOSE 8000

# Docker healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--worker-class", "gthread", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]

